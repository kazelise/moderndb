# Flask Modern DB: AI-Powered CSV Data Editor

Flask Modern DB is a web-based application that allows users to upload, view, edit, and manage CSV data through an intuitive interface. It features a terminal-like command input for data manipulation and integrates with AI models (via OpenRouter API) to translate natural language queries into executable data operations. The application has a clean, light-themed UI with excellent readability and modern aesthetics.

## Features

*   **CSV Data Management**: Upload, view, and export data in CSV format.
*   **Modern UI/UX**: Light theme, responsive design, custom-styled components, and loading indicators.
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

*   Python 3.11+
*   pip (Python package installer)
*   [python-dotenv](https://pypi.org/project/python-dotenv/) (for local .env support)

## Installation

1.  **Clone the repository (or download the source code):**
    ```bash
    git clone https://github.com/kazelise/moderndb.git
    cd moderndb
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
    The `requirements.txt` file contains:
    ```
    flask==2.3.3
    Flask-Session==0.5.0
    pandas==2.1.0
    requests==2.31.0
    jinja2==3.1.2
    python-dotenv==1.0.1
    ```

4.  **API Configuration (Required for AI features):**
    The application uses environment variables for all sensitive configuration. You can set your API key in several ways:
    
    *   **Using a .env file (recommended for local development):**
        * Copy the provided `.env.example` file to a new `.env` file: `cp .env.example .env`
        * Edit the `.env` file and fill in your actual API key and other settings
        * The `.env` file is ignored by git, ensuring your keys won't be committed to the repository
        * The app will automatically load `.env` using `python-dotenv`
    
    *   **Using shell environment variables (for production or Docker):**
        * Export variables in your shell before running the app:
          ```fish
          set -x OPENROUTER_API_KEY your_api_key_here
          set -x FLASK_SECRET_KEY your_flask_secret
          python app.py
          ```
    
    *   **Using Docker Compose:**
        * See the Docker section below for details.

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
        *   Type your data request in natural language (e.g., "add a new user with name John and age 30", "show all users older than 25") into the AI input bar at the bottom and press Enter or click the send button.
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
*   You must have a valid OpenRouter API key configured via environment variable or .env file for AI features to work.
*   The UI does not support setting API keys for security reasons.
*   The `system_prompt` in `app.py` defines the capabilities and JSON output format expected from the AI model. This prompt is crucial for the AI to understand the available commands and data structure.
*   The `ai_cmd_to_str` function in `app.py` converts the AI-generated JSON command into a string format that can be processed by the `parse_terminal_command` function.

## Docker Deployment

This application includes a `Dockerfile` and `docker-compose.yml` for easy containerization and deployment.

**Prerequisites:**

*   Docker installed and running on your system.

**1. Using Docker Compose (Recommended):**

   *   **Navigate to the project directory:**
       ```bash
       cd moderndb
       ```
   *   **Build and run the services:**
       ```bash
       docker-compose up
       ```
       To run in detached mode (in the background):
       ```bash
       docker-compose up -d
       ```
   *   The application will be accessible at `http://localhost:5000`.
   *   To stop the services:
       ```bash
       docker-compose down
       ```
   *   **Environment Variables:**
       * By default, Docker Compose will read from a `.env` file in the project root (see `.env.example`).
       * You can also set environment variables directly in `docker-compose.yml` under the `environment` section.
       * Example:
         ```yaml
         environment:
           - FLASK_SECRET_KEY=your_strong_random_secret_key
           - FLASK_ENV=production
           - OPENROUTER_API_KEY=your_openrouter_key_here
           - OPENROUTER_API_URL=https://openrouter.ai/api/v1
           - AI_MODEL=qwen/qwen3-235b-a22b:free
         ```

**2. Using Dockerfile directly:**

   *   **Navigate to the project directory:**
       ```bash
       cd moderndb
       ```
   *   **Build the Docker image:**
       ```bash
       docker build -t flask_modern_db_app .
       ```
   *   **Run the Docker container:**
       ```bash
       docker run -d -p 5000:5000 \
         -v "(pwd)/data:/app/data" \
         -v "(pwd)/flask_session:/app/flask_session" \
         -e FLASK_SECRET_KEY=your_strong_random_secret_key \
         -e FLASK_ENV=production \
         -e OPENROUTER_API_KEY=your_openrouter_key_here \
         -e OPENROUTER_API_URL=https://openrouter.ai/api/v1 \
         -e AI_MODEL=qwen/qwen3-235b-a22b:free \
         --name modern_db_container \
         flask_modern_db_app
       ```
   *   The application will be accessible at `http://localhost:5000`.
   *   To stop the container:
       ```bash
       docker stop modern_db_container
       ```
   *   To remove the container:
       ```bash
       docker rm modern_db_container
       ```

**Important Considerations for Docker:**

*   **`.dockerignore` file:** A `.dockerignore` file is included to prevent unnecessary files (like `.git`, `venv/`, `__pycache__/`) from being copied into the Docker image, keeping it small and build times fast.
*   **Data Persistence:** The provided `docker-compose.yml` and `docker run` commands use volume mounts (`./data:/app/data` and `./flask_session:/app/flask_session`) to ensure that your uploaded CSV data and user session data persist even if the container is stopped or removed.
*   **API Key for AI Features:** When running in Docker, the application will prioritize `OPENROUTER_API_KEY` environment variable if set. If not, it will check the `.env` file if present. The `OPENROUTER_API_URL` and `AI_MODEL` environment variables can also be used to customize the AI service endpoint and model respectively.

## File Structure

```
moderndb/
├── app.py            # Main Flask application, backend logic, command parsing
├── Dockerfile        # Docker configuration for containerizing the application
├── docker-compose.yml# Docker Compose configuration for easy deployment
├── requirements.txt  # Python dependencies with locked versions
├── .env.example      # Template for environment variables (copy to .env for local use)
├── .gitignore        # Specifies files to exclude from version control
├── data/             # Directory for storing uploaded CSV data
│   ├── uploaded.csv  # Default name for the uploaded data file
│   └── .gitkeep      # Empty file to maintain directory structure in git
├── flask_session/    # Directory for Flask session files
├── static/
│   └── modern.css    # Custom CSS for styling the application
├── templates/
│   └── index.html    # Main HTML template for the user interface
└── README.md         # This file
```

## Security Notice

- **API keys and all sensitive configuration must be set via environment variables or .env file.**
- **The frontend does not support API key configuration for security reasons.**
- **Never commit your real .env file or API keys to version control.**

## Recent Updates (May 2025)

* Added python-dotenv support for .env file loading
* All AI/API key configuration is now environment variable only
* Removed all frontend API key input and settings
* Improved English-only user-facing messages
* Security best practices for all deployment scenarios
