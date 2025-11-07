# src/snapshot_generator.py
import os
import sys
import json
import datetime
import re
import argparse
from git import Repo, InvalidGitRepositoryError
from colorama import init, Fore, Style

# Initialize colorama to make ANSI escape sequences work on Windows.
# autoreset=True ensures that each print statement returns to the default color.
init(autoreset=True)

class Colors:
    """A simple class to hold color constants for terminal output."""
    BLUE = Fore.BLUE
    CYAN = Fore.CYAN
    GREEN = Fore.GREEN
    YELLOW = Fore.YELLOW
    RED = Fore.RED
    RESET = Style.RESET_ALL

def print_progress_bar(iteration, total, prefix='', suffix='', length=50, fill='█'):
    """
    Draws a progress bar in the terminal.
    This provides real-time feedback for a long-running process without flooding the console.
    """
    if total == 0:
        total = 1 # Avoid ZeroDivisionError
    percent = ("{0:.1f}").format(100 * (iteration / float(total)))
    filled_length = int(length * iteration // total)
    bar = fill * filled_length + '-' * (length - filled_length)
    # The '\r' character moves the cursor to the beginning of the line to overwrite it.
    sys.stdout.write(f'\r{prefix} |{bar}| {percent}% {suffix}')
    sys.stdout.flush()
    if iteration == total:
        sys.stdout.write('\n') # Move to the next line once the bar is complete.

def get_git_commit_info(filepath, repo_path):
    """
    Retrieves the last commit information for a specific file.
    This provides crucial context and traceability for each piece of code.
    """
    try:
        repo = Repo(repo_path)
        relative_filepath = os.path.relpath(filepath, repo_path)
        commits = list(repo.iter_commits(paths=relative_filepath, max_count=1))
        if commits:
            commit = commits[0]
            author = commit.author.name
            date = datetime.datetime.fromtimestamp(commit.authored_date, tz=datetime.timezone.utc).astimezone(datetime.datetime.now().astimezone().tzinfo).strftime('%Y-%m-%d %H:%M:%S')
            hexsha = commit.hexsha[:7]
            return f"{hexsha} ({author}) on {date}"
        return "N/A (No commit info)"
    except InvalidGitRepositoryError:
        return "N/A (Not a Git repository at project root)"
    except Exception:
        # This can happen if the file is new and not yet tracked by Git.
        return "N/A (File not tracked by Git)"

def create_directory_tree(project_name, relative_paths):
    """
    Creates a text-based directory tree from a list of relative file paths.
    This provides a human-readable map of the project structure.
    """
    tree_dict = {}
    for path in relative_paths:
        parts = path.replace(os.sep, '/').split('/')
        current_level = tree_dict
        for part in parts:
            if part not in current_level:
                current_level[part] = {}
            current_level = current_level[part]

    def build_tree_string(d, prefix=''):
        lines = []
        # Sort items to ensure a consistent order: directories first, then files.
        items = sorted(d.keys(), key=lambda x: (not d[x], x.lower()))
        for i, name in enumerate(items):
            connector = '└── ' if i == len(items) - 1 else '├── '
            lines.append(f"{prefix}{connector}{name}")
            if d[name]: # If it's a directory, recurse
                extension = '    ' if i == len(items) - 1 else '│   '
                lines.extend(build_tree_string(d[name], prefix + extension))
        return lines

    tree_lines = [f"{project_name}/"] + build_tree_string(tree_dict)
    return "\n".join(tree_lines)

# --- MODIFICACIÓN 1: Añadir el nuevo parámetro `tree_only` ---
def generate_code_snapshot(config_path="config.json", limit=-1, tree_only=False):
    # 1. Load the user's configuration from the JSON file.
    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            config = json.load(f)
    except FileNotFoundError:
        print(f"{Colors.RED}Error: Configuration file '{config_path}' not found.")
        return
    except json.JSONDecodeError:
        print(f"{Colors.RED}Error: Configuration file '{config_path}' has an invalid JSON format.")
        return

    project_root = config.get("project_root")
    output_dir = config.get("output_directory", "output")
    ignored_patterns = config.get("ignored_patterns", [])
    ignored_extensions = config.get("ignored_file_extensions", [])

    if not project_root:
        print(f"{Colors.RED}Error: 'project_root' is not defined in the configuration file.")
        return

    project_root = os.path.abspath(project_root)
    project_name = os.path.basename(project_root)

    print(f"{Colors.BLUE}=======================================================================")
    print(f"{Colors.CYAN}  INITIALIZING SNAPSHOT FOR PROJECT: {project_name}")
    print(f"{Colors.BLUE}=======================================================================")

    # --- PHASE 1: DISCOVER AND FILTER FILES ---
    # We walk the directory tree once to build a complete list of files to process.
    # This is necessary to get an accurate total count for the progress bar *before*
    # we start writing the output file.
    print(f"{Colors.CYAN}Phase 1: Discovering and filtering files...")
    files_to_process = []
    for root, dirs, files in os.walk(project_root, topdown=True):
        dirs[:] = [d for d in dirs if not any(pattern in os.path.join(os.path.relpath(root, project_root), d).replace(os.sep, '/') for pattern in ignored_patterns)]
        for file in files:
            relative_file_path = os.path.join(os.path.relpath(root, project_root), file)
            if any(pattern in relative_file_path.replace(os.sep, '/') for pattern in ignored_patterns):
                continue
            if any(file.endswith(ext) for ext in ignored_extensions):
                continue
            files_to_process.append(os.path.join(root, file))

    total_files_found = len(files_to_process)
    if total_files_found == 0:
        print(f"{Colors.YELLOW}No files found to process with the current filters.")
        return

    if limit > 0:
        print(f"{Colors.YELLOW}Found {total_files_found} files. Processing the first {limit} due to --limit flag.\n")
        files_to_process = files_to_process[:limit]
    else:
        print(f"{Colors.GREEN}Found {total_files_found} files to process.\n")

    total_files_to_process = len(files_to_process)

    project_name_slug = re.sub(r'[^a-zA-Z0-9_-]', '', project_name).lower()
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    output_filename = os.path.join(output_dir, f"{project_name_slug}_snapshot_{timestamp}.txt")

    relative_paths_for_tree = [os.path.relpath(p, project_root) for p in files_to_process]
    directory_tree_string = create_directory_tree(project_name, relative_paths_for_tree)

    LINE_WIDTH = 150
    HEADER_LINE = "=" * LINE_WIDTH
    SEPARATOR_LINE = "-" * LINE_WIDTH

    # --- MODIFICACIÓN 2: Lógica para el modo "tree-only" ---
    # If the tree_only flag is set, write only the header and the tree, then exit.
    if tree_only:
        print(f"{Colors.CYAN}Phase 2: Generating directory tree only...")
        with open(output_filename, 'w', encoding='utf-8') as outfile:
            outfile.write(f"{HEADER_LINE}\n")
            outfile.write("Fractalcode - Code Snapshot\n")
            outfile.write(f"Generated: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M%S')} (America/Mexico_City)\n")
            outfile.write(f"Project: {project_name}\n")
            outfile.write(f"Root Directory: {project_root}\n")
            outfile.write(f"{HEADER_LINE}\n\n")

            outfile.write(f"{SEPARATOR_LINE}\n")
            tree_header = "--- DIRECTORY & FILE STRUCTURE "
            outfile.write(f"{tree_header}{'-' * (LINE_WIDTH - len(tree_header))}\n")
            outfile.write(directory_tree_string)
            outfile.write(f"\n{SEPARATOR_LINE}\n\n")

        print(f"\n{Colors.BLUE}=======================================================================")
        print(f"{Colors.CYAN}  TREE-ONLY SNAPSHOT FINISHED")
        print(f"{Colors.GREEN}  Total files/directories found: {total_files_to_process}")
        print(f"{Colors.YELLOW}  Output file: {output_filename}")
        print(f"{Colors.BLUE}=======================================================================")
        return # Stop execution here.

    # --- PHASE 2 (FULL SNAPSHOT): PROCESS AND WRITE THE SNAPSHOT ---
    print(f"{Colors.CYAN}Phase 2: Generating full snapshot...")
    with open(output_filename, 'w', encoding='utf-8') as outfile:
        outfile.write(f"{HEADER_LINE}\n")
        outfile.write("Fractalcode - Code Snapshot\n")
        outfile.write(f"Generated: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M%S')} (America/Mexico_City)\n")
        outfile.write(f"Project: {project_name}\n")
        outfile.write(f"Root Directory: {project_root}\n")
        outfile.write(f"{HEADER_LINE}\n\n")

        outfile.write(f"{SEPARATOR_LINE}\n")
        tree_header = "--- DIRECTORY & FILE STRUCTURE "
        outfile.write(f"{tree_header}{'-' * (LINE_WIDTH - len(tree_header))}\n")
        outfile.write(directory_tree_string)
        outfile.write(f"\n{SEPARATOR_LINE}\n\n")

        print_progress_bar(0, total_files_to_process, prefix='Progress:', suffix='Completed', length=50)

        for i, file_path in enumerate(files_to_process):
            relative_path = os.path.relpath(file_path, project_root).replace(os.sep, '/')
            commit_info = get_git_commit_info(file_path, project_root)

            # --- DYNAMICALLY CALCULATE SEPARATOR PADDING ---
            # Calculate the number of dashes needed to fill the line up to LINE_WIDTH.
            # This ensures perfect alignment regardless of the tag's length.
            start_tag = "--- FILE START "
            content_tag = "--- FILE CONTENT "
            end_tag = "--- FILE END "

            outfile.write(f"{SEPARATOR_LINE}\n")
            outfile.write(f"{start_tag}{'-' * (LINE_WIDTH - len(start_tag))}\n")
            outfile.write(f"Full Path: {relative_path}\n")
            outfile.write(f"Last Commit: {commit_info}\n")
            outfile.write(f"{content_tag}{'-' * (LINE_WIDTH - len(content_tag))}\n")
            try:
                with open(file_path, 'r', encoding='utf-8', errors='replace') as infile:
                    outfile.write(infile.read())
            except UnicodeDecodeError as e:
                outfile.write(f"ERROR: Could not read file due to encoding issue: {e}\n")
                outfile.write("This file might be saved with a different encoding than UTF-8 (e.g., UTF-16).\n")
            except Exception as e:
                # If a single file fails to read, we log the error in the snapshot
                # but continue processing the rest of the files.
                outfile.write(f"ERROR: Could not read file: {e}\n")
            outfile.write(f"\n{end_tag}{'-' * (LINE_WIDTH - len(end_tag))}\n")
            outfile.write(f"{SEPARATOR_LINE}\n\n")

            print_progress_bar(i + 1, total_files_to_process, prefix='Progress:', suffix='Completed', length=50)

    print(f"\n{Colors.BLUE}=======================================================================")
    print(f"{Colors.CYAN}  SNAPSHOT FINISHED")
    print(f"{Colors.GREEN}  Total files processed: {total_files_to_process}")
    print(f"{Colors.YELLOW}  Output file: {output_filename}")
    print(f"{Colors.BLUE}=======================================================================")

if __name__ == "__main__":
    # This is the script's entry point.
    # We configure and parse command-line arguments here.
    parser = argparse.ArgumentParser(description='Generate a code snapshot from a project directory.')
    parser.add_argument('--limit', type=int, default=-1,
                        help='Limit the number of files to process for a quick test run.')
    parser.add_argument('--tree-only', action='store_true',
                        help='Generate only the directory tree structure without file content.')
    args = parser.parse_args()

    if not os.path.exists("output"):
        os.makedirs("output")

# Pass the parsed arguments (like the file limit) to the main function.
    generate_code_snapshot(config_path="config.json", limit=args.limit, tree_only=args.tree_only)