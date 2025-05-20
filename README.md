# Flask Modern DB: AI-Powered CSV Data Editor

Flask Modern DB *   **API Configuration (Optional but recommended for AI features):**
    The application uses a secure, multi-layered approach to manage API credentials. For persistent and reliable AI integration, you can set your API key in several ways:
    
    *   **Using environment variables (recommended for security):**
        * Copy the provided `.env.example` file to a new `.env` file: `cp .env.example .env`
        * Edit the `.env` file and fill in your actual API key and other settings
        * The `.env` file is ignored by git (via .gitignore), ensuring your keys won't be committed to the repository
        * Environment variables are the most secure method and take precedence over other configuration methods
    
    *   **Using the in-app UI:**
        * Click on the "AI Settings" button in the application's header
        * Enter your API key, custom URL (optional), and preferred AI model (optional)
        * Your settings will be saved to your session, not to disk, for better security
        * Session data is automatically cleared when the browser session ends
    
    *   **Configuration precedence:**
        * Environment variables (highest priority)
        * User session values (set via UI)
        * Application defaults (lowest priority)ed application that allows users to upload, view, edit, and manage CSV data through an intuitive interface. It features a terminal-like command input for data manipulation and integrates with AI models (via OpenRouter API) to translate natural language queries into executable data operations. The application has a clean, light-themed UI with excellent readability and modern aesthetics.

## Features

*   **CSV Data Management**: Upload, view, and export data in CSV format with robust empty file handling.
*   **Modern UI/UX**: Light theme, responsive design, custom-styled components, loading indicators, and confirmation dialogs for destructive actions.
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

## Installation

1.  **Clone the repository (or download the source code):**
    ```bash
    git clone https://github.com/kazelise/moderndb.git
    cd moderndb-master
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
    ```

4.  **API Configuration (Optional but recommended for AI features):**
    The application uses default API endpoint and a placeholder key for OpenRouter. For persistent and reliable AI integration, you can set your API key in several ways:
    
    *   **Using environment variables (recommended for security):**
        * Copy the provided `.env.example` file to a new `.env` file: `cp .env.example .env`
        * Edit the `.env` file and fill in your actual API key and other settings
        * The `.env` file is ignored by git, ensuring your keys won't be committed to the repository
    
    *   **Using the in-app UI:**
        * Click on the "AI Settings" button in the application's header
        * Enter your API key, custom URL (optional), and preferred AI model (optional)
        * Your settings will be saved to your session

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
    *   **UI Data Destruction**: The application also provides a dedicated "Destroy All Data" button in the interface for quick data reset with confirmation dialog.
    *   `search <keyword>`: Perform a fuzzy search across all fields for rows containing the keyword (case-insensitive).
        *   Example: `search admin`
    *   `search_exact col=val`: Perform an exact search for rows where the specified column matches the given value.
        *   Example: `search_exact email=test@example.com`
        *   Supports the same pattern matching as `update`/`delete` for string columns.

## AI Integration Details

*   The AI assistant uses the OpenRouter API to process natural language queries.
*   You need to have a valid OpenRouter API key configured for AI features to work reliably, which can be set through:
    * Environment variables (most secure, see `.env.example`)
    * The AI Settings panel in the UI (persists in session storage)
*   The enhanced UI now allows for:
    * Setting custom API URLs (useful for self-hosted LLM endpoints or enterprise scenarios)
    * Selecting different AI models from the OpenRouter ecosystem
    * Secure session-based storage of credentials (not saved to disk)
*   The `system_prompt` in `app.py` defines the capabilities and JSON output format expected from the AI model. This prompt is crucial for the AI to understand the available commands and data structure.
*   The `ai_cmd_to_str` function in `app.py` converts the AI-generated JSON command into a string format that can be processed by the `parse_terminal_command` function.
*   The application now implements a secure credential flow that prioritizes environment variables over session storage, with fallback to defaults.

## Docker Deployment

This application includes a `Dockerfile` and `docker-compose.yml` for easy containerization and deployment.

**Prerequisites:**

*   Docker installed and running on your system.

**1. Using Docker Compose (Recommended):**

   This is the simplest way to get the application running with Docker.

   *   **Navigate to the project directory:**
       ```bash
       cd flask_modern_db
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
   *   **Environment Variables:** You can configure the `FLASK_SECRET_KEY` and `FLASK_ENV` in the `docker-compose.yml` file. For AI features, you can also set `OPENROUTER_API_KEY`, `OPENROUTER_API_URL`, and `AI_MODEL` as environment variables.
       Example `docker-compose.yml` snippet:
       ```yaml
       services:
         web:
           # ... other configurations ...
           environment:
             - FLASK_SECRET_KEY=your_strong_random_secret_key
             - FLASK_ENV=production
             - OPENROUTER_API_KEY=your_openrouter_key_here 
             - OPENROUTER_API_URL=https://your_custom_url # Optional
             - AI_MODEL=your_chosen_model # Optional, e.g., mistralai/mistral-7b-instruct
       ```
       By default, `FLASK_ENV` is set to `production` in the `Dockerfile`.

**2. Using Dockerfile directly:**

   *   **Navigate to the project directory:**
       ```bash
       cd flask_modern_db
       ```
   *   **Build the Docker image:**
       ```bash
       docker build -t flask_modern_db_app .
       ```
       (You can replace `flask_modern_db_app` with your preferred image name).
   *   **Run the Docker container:**
       ```bash
       docker run -d -p 5000:5000 \
         -v "$(pwd)/data:/app/data" \
         -v "$(pwd)/flask_session:/app/flask_session" \
         -e FLASK_SECRET_KEY=your_strong_random_secret_key \
         -e FLASK_ENV=production \
         -e OPENROUTER_API_KEY=your_openrouter_key_here \
         -e OPENROUTER_API_URL=https://your_custom_url \
         -e AI_MODEL=your_chosen_model \
         --name modern_db_container \
         flask_modern_db_app
       ```
       *   `-d`: Runs the container in detached mode.
       *   `-p 5000:5000`: Maps port 5000 on the host to port 5000 in the container.
       *   `-v "$(pwd)/data:/app/data"`: Mounts the local `./data` directory to `/app/data` in the container for data persistence.
       *   `-v "$(pwd)/flask_session:/app/flask_session"`: Mounts the local `./flask_session` directory to `/app/flask_session` in the container for session persistence.
       *   `--name modern_db_container`: Assigns a name to the running container.
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
*   **API Key for AI Features:** When running in Docker, the application will prioritize `OPENROUTER_API_KEY` environment variable if set. If not, it will check the user's session (configured via UI). If neither is available, AI features will require UI configuration. The `OPENROUTER_API_URL` and `AI_MODEL` environment variables can also be used to customize the AI service endpoint and model respectively.

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

## Recent Updates (May 2025)

* Changed application theme from dark to light mode for better readability and accessibility
* Added functionality to destroy all data with confirmation dialog for safety
* Enhanced AI configuration UI to allow customizing API URL and model selection
* Updated Docker configuration to use Python 3.11 for better performance
* Added strict file type checking for CSV uploads only to prevent errors
* All user-facing messages standardized to English for consistency
* Pinned dependency versions for better stability and reproducibility
* Improved empty file handling to prevent EmptyDataError exceptions
* Added `.env.example` template for secure environment variable configuration
* Enhanced security for API key management using environment variables
* Added `.gitignore` patterns to exclude sensitive data from version control
* Added `data/.gitkeep` to maintain directory structure without storing data in git repository
* Improved error handling and user feedback throughout the application
