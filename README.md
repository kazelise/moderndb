# Flask Modern DB: AI-Powered CSV Data Editor

Flask Modern DB is a web-based application that allows users to upload, view, edit, and manage CSV data through an intuitive interface. It features a terminal-like command input for data manipulation and integrates with AI models (via OpenRouter API) to translate natural language queries into executable data operations. The application boasts a modern, dark-themed UI inspired by "Codex" or "OpenAI" aesthetics.

## Features

*   **CSV Data Management**: Upload, view, and export data in CSV format.
*   **Modern UI/UX**: Dark theme, responsive design, custom-styled components, and loading indicators.
*   **Terminal Interface**: Execute commands to interact with the data (list, add, update, delete, search, etc.).
*   **Flexible Data Operations**:
    *   Add single or multiple rows (`add`, `add_batch`).
    *   Update and delete rows based on flexible, multi-column conditions.
    *   Support for advanced comparison operators (`>`, `<`, `>=`, `<=`, `!=`) for numeric fields.
    *   Support for pattern matching (`prefix*`, `*suffix`, `*contains*`) for string fields.
    *   Handle missing values (`nan`, `na`, `none`, `''`).
    *   View column names and their data types (`columns`).
    *   Delete all data with confirmation (`delete_all`).
*   **AI-Powered Commands**:
    *   Translate natural language queries into data manipulation commands.
    *   Supports integration with AI models via OpenRouter API.
    *   Fetches available models and allows model switching.
*   **Real-time Feedback**: Terminal output displays command execution results and AI suggestions.
*   **Session Management**: Persists terminal output and AI model selection across requests.

## Tech Stack

*   **Backend**: Python, Flask, Pandas
*   **Frontend**: HTML, CSS, JavaScript
*   **AI Integration**: OpenRouter API
*   **Session Management**: Flask-Session (Filesystem-based)

## Prerequisites

*   Python 3.11.11
*   pip (Python package installer)

## Installation

1.  **Clone the repository (or download the source code):**
    ```bash
    git clone https://github.com/kazelise/moderndb.git
    cd flask_modern_db
    ```

2.  **Create a virtual environment (recommended):**
    ```bash
    python -m venv venv
    source venv/bin/activate  # On Windows use `venv\Scripts\activate`
    ```

3.  **Install the required dependencies:**
    ```bash
    pip install -r requirements.txt
    ```
    The `requirements.txt` file should contain:
    ```
    Flask
    Flask-Session
    pandas
    requests
    ```

4.  **API Configuration (Optional but recommended for AI features):**
    The application uses default API endpoint and a placeholder key for OpenRouter. For persistent and reliable AI integration, you might want to update these in `app.py`:
    *   `DEFAULT_AI_URL`: Change if you use a different OpenRouter compatible endpoint.
    *   `DEFAULT_API_KEY`: **Replace `"sk-or-v1-..."` with your actual OpenRouter API key.**

## Usage

1.  **Run the Flask application:**
    ```bash
    python app.py
    ```
    The application will typically be available at `http://127.0.0.1:5000/`.

2.  **Interacting with the Application:**

    *   **Upload Data**:
        *   Click the "Choose File" button under the "File Operations" card.
        *   Select a CSV file from your local system.
        *   The data will be loaded, and a preview will be displayed. Terminal output will confirm the upload.
    *   **Export Data**:
        *   Click the "Export Data" button to download the current dataset as a CSV file.
    *   **AI Commands**:
        *   **Fetch Models**: Click "Fetch Models" under the "AI Assistant" card. Currently, it's hardcoded to a specific Qwen model.
        *   **Select Model**: Choose a model from the dropdown list.
        *   **Set Model**: Click "Set Model" to activate the selected AI model.
        *   **Enter Query**: Type your data request in natural language (e.g., "add a new user with name John and age 30", "show all users older than 25") into the AI input bar at the bottom and press Enter or click the send button.
        *   The AI will attempt to translate your query into a JSON command, which is then converted to a terminal command and executed. Both the AI's suggested JSON and the executed command will appear in the terminal.
    *   **Terminal Commands**:
        *   Type commands directly into the "Terminal Input" field under the "Terminal" card and press Enter or click "Execute".
        *   Results and messages will be displayed in the "Terminal Output" area.

3.  **Available Terminal Commands:**

    *   `help`: Show the list of supported commands and their syntax.
    *   `clear`: Clear the terminal output.
    *   `list`: Display all data in a paginated table format.
    *   `columns`: Show column names and their inferred data types.
    *   `add col1=val1 col2=val2 ...`: Add a new row with the specified column values.
        *   Example: `add name=Alice age=28 city=London`
    *   `add_batch col1=val1,val2 col2=val3,val4 ...`: Add multiple rows at once. Values for each column are comma-separated.
        *   Example: `add_batch name=Bob,Charlie age=35,42 city=Paris,Berlin`
    *   `update <conditions> set <updates>`: Update rows matching specified conditions.
        *   Conditions: `col1=val1 col2=val2 ...`
        *   Updates: `col_to_update1=new_val1 ...`
        *   Example: `update age=28 city=London set age=29`
        *   **Advanced Conditions**:
            *   Numeric: `age=>30`, `price=<100`, `count>=10`, `stock_level<=5`, `id!=101`
            *   String Patterns: `name=John*` (starts with), `email=*@example.com` (ends with), `description=*important*` (contains)
            *   Missing Values: `notes=nan`, `middle_name=''`
    *   `delete <conditions>`: Delete rows matching specified conditions.
        *   Example: `delete city=Paris`
        *   Supports the same advanced conditions as `update`.
        *   For bulk deletions (more than 10 rows), confirmation `confirm=yes` might be required by the AI or can be added manually (e.g., `delete age=>60 confirm=yes`).
    *   `delete_all`: Delete all data from the table. Requires confirmation.
        *   To confirm: `delete_all confirm`
    *   `search <keyword>`: Perform a fuzzy search across all fields for rows containing the keyword (case-insensitive).
        *   Example: `search admin`
    *   `search_exact col=val`: Perform an exact search for rows where the specified column matches the given value.
        *   Example: `search_exact email=test@example.com`
        *   Supports the same pattern matching as `update`/`delete` for string columns.

## AI Integration Details

*   The AI assistant uses the OpenRouter API to process natural language queries.
*   You need to have a valid OpenRouter API key configured in `app.py` (variable `DEFAULT_API_KEY`) for the AI features to work reliably.
*   The `system_prompt` in `app.py` defines the capabilities and JSON output format expected from the AI model. This prompt is crucial for the AI to understand the available commands and data structure.
*   The `ai_cmd_to_str` function in `app.py` converts the AI-generated JSON command into a string format that can be processed by the `parse_terminal_command` function.

## File Structure

```
flask_modern_db/
├── app.py            # Main Flask application, backend logic, command parsing
├── requirements.txt  # Python dependencies
├── data/             # Directory for storing uploaded CSV data
│   └── uploaded.csv  # Default name for the uploaded data file
├── flask_session/    # Directory for Flask session files
├── static/
│   └── modern.css    # Custom CSS for styling the application
└── templates/
    └── index.html    # Main HTML template for the user interface
└── README.md         # This file
```
