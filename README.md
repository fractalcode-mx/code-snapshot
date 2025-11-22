<div align="center">
  <table>
    <tr>
      <td align="center" valign="middle">
        <a href="https://fractalcode.com.mx" target="_blank">
          <picture>
            <source media="(prefers-color-scheme: dark)" srcset="./assets/fractalcode-dark-background.png" width="450">
            <source media="(prefers-color-scheme: light)" srcset="./assets/fractalcode-dark-background.png" width="450">
            <img alt="Fractalcode Logo" src="./assets/fractalcode-dark-background.png" width="450">
          </picture>
        </a>
      </td>
      <td align="center" valign="middle">
        <img src="./assets/logo.png" alt="Code Snapshot Logo" width="150">
      </td>
    </tr>
  </table>
</div>



# Code Snapshot by Fractalcode

**Code Snapshot** is a Python CLI tool that captures a complete, self-contained snapshot of a software project. It consolidates the file structure, the content of each file, and key metadata from the Git history into a single text file (`.txt`).

Its primary purpose is to generate an exhaustive and easily processable context, ideal for documentation, code analysis, archiving, or for use as a knowledge base for Large Language Models (LLMs).

## Features

*   **Unified Snapshot**: Generates a single `.txt` file with the entire project's content.
*   **Git Metadata**: Includes the last commit information (hash, author, date) for each file, providing traceability.
*   **Highly Configurable**: Uses a `config.json` file to easily define which directories, files, or extensions to exclude.
*   **Clean & Structured Format**: The output is formatted with clear separators to be readable by both humans and machines.
*   **Interactive Progress Bar**: Displays real-time progress without cluttering the console.
*   **Quick Test Mode**: Includes a `--limit` flag to process only a limited number of files, ideal for testing and debugging.

## Prerequisites

*   Python 3.x
*   Git

## Installation and Setup

Follow these steps to set up the environment and prepare the tool for use.

1.  **Clone the repository:**
    ```bash
    git clone git@github.com:Fractalcode/code-snapshot.git
    cd code-snapshot
    ```

2.  **Create and activate a virtual environment:**
    This isolates the project's dependencies.
    ```bash
    # Create the environment
    python -m venv .venv

    # Activate on Windows (PowerShell/VSCode Terminal)
    .venv\Scripts\activate

    # Activate on Linux/macOS
    # source .venv/bin/activate
    ```

3.  **Install dependencies:**
    The `requirements.txt` file contains all the necessary libraries.
    ```bash
    pip install -r requirements.txt
    ```

4.  **Configure the project to analyze:**
    a. Copy the configuration template:
    ```bash
    # On Windows
    copy config.template.json config.json

    # On Linux/macOS
    # cp config.template.json config.json
    ```
    b. Open `config.json` and edit the values to point to your project. The most important field is `project_root`.

    ```json
    {
        "project_root": "/path/to/your/project",
        "output_directory": "output",
        "ignored_patterns": [
            "node_modules",
            "vendor",
            ".venv",
            "venv",
            ".git",
            ".vscode",
            ".DS_Store",
            "composer.lock",
            "output"
        ],
        "ignored_file_extensions": [
            // Images
            ".jpg", ".jpeg", ".png", ".gif", ".bmp", ".svg", ".ico",

            // Fonts
            ".woff", ".woff2", ".ttf", ".otf", ".eot",

            // Compressed Archives
            ".zip", ".tar", ".gz", ".rar", ".7z",

            // Documents
            ".pdf", ".doc", ".docx", ".xls", ".xlsx", ".ppt", ".pptx",

            // Design & Graphics Source Files
            ".psd", ".ai", ".sketch",

            // Database Files
            ".db", ".sqlite",

            // Development & Metadata
            ".md", ".map"
        ]
    }
    ```

## Usage

Once configured, you can generate snapshots with the following commands.

#### Generate a full snapshot

Run the script without arguments to process all files in the configured project.

```bash
python src/snapshot_generator.py
```

Run tree only
```bash
python src/snapshot_generator.py --tree-only
```