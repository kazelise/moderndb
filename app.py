from flask import Flask, render_template, request, redirect, url_for, send_file, session, flash
import pandas as pd
import os
import requests
import shlex
from flask_session import Session
import json
import re

app = Flask(__name__)
app.secret_key = os.environ.get('FLASK_SECRET_KEY', 'your_default_secret_key')  # Ensure a secret key is set for sessions
app.config['SESSION_TYPE'] = 'filesystem'  # Store session data on the filesystem
app.config['MAX_CONTENT_LENGTH'] = 10 * 1024 * 1024  # 10 MB limit for file uploads
Session(app)

DATA_PATH = "data/uploaded.csv"  # Path to the CSV file where data is stored
# AI Configuration: Prioritize environment variables, then app defaults.
DEFAULT_AI_URL = os.environ.get("OPENROUTER_API_URL", "https://openrouter.ai/api/v1")
DEFAULT_API_KEY = os.environ.get("OPENROUTER_API_KEY", "")  # Default API Key for the AI service, can be overridden by session
DEFAULT_AI_MODEL = os.environ.get("AI_MODEL", "qwen/qwen3-235b-a22b:free")  # Default AI model

# Helper function to attempt type casting for assignment, inferring from target series or by trying common types.
def _attempt_cast_for_assignment(value_str, target_series_for_dtype_inference):
    # If the target series (column) is empty, we have to guess the type.
    if target_series_for_dtype_inference.empty:
        try:
            # Try converting to numeric first.
            return pd.to_numeric(value_str, errors='raise')
        except ValueError:
            # If numeric conversion fails, assume it's a string.
            return str(value_str)

    target_dtype = target_series_for_dtype_inference.dtype

    # Handle common string representations of null/NA values.
    if str(value_str).lower() in ['nan', 'na', '<na>', 'none', '']:
        return pd.NA  # Use pandas' NA for missing values.

    try:
        # Attempt casting based on the target column's existing dtype.
        if pd.api.types.is_integer_dtype(target_dtype):
            return int(float(value_str))  # Convert to float first to handle "10.0", then to int.
        elif pd.api.types.is_float_dtype(target_dtype):
            return float(value_str)
        elif pd.api.types.is_bool_dtype(target_dtype):
            val_lower = str(value_str).lower()
            if val_lower in ['true', '1', 't', 'yes']:
                return True
            if val_lower in ['false', '0', 'f', 'no']:
                return False
            return str(value_str)  # If not a clear boolean string, keep as string.
        elif pd.api.types.is_datetime64_any_dtype(target_dtype):
            return pd.to_datetime(value_str, errors='raise')  # Try parsing as datetime.
        return str(value_str)  # Default to string if no other type matches.
    except ValueError:
        # If any type conversion fails, return the original string value.
        return str(value_str)

# Loads data from the CSV file. Returns an empty DataFrame if the file doesn't exist or is empty.
def load_data():
    if os.path.exists(DATA_PATH):
        try:
            return pd.read_csv(DATA_PATH)
        except pd.errors.EmptyDataError:
            # Handle empty file case
            return pd.DataFrame()
    else:
        return pd.DataFrame()

# Saves the DataFrame to a CSV file. Creates the 'data' directory if it doesn't exist.
# If the DataFrame is empty, creates an empty CSV file to maintain consistency
def save_data(df):
    os.makedirs("data", exist_ok=True)
    if df.empty:
        # Create an empty file when df is empty
        open(DATA_PATH, 'w').close()
    else:
        df.to_csv(DATA_PATH, index=False)

# Retrieves the terminal output from the session.
def get_terminal_output():
    return session.get("terminal_output", "")

# Appends a message to the terminal output in the session, keeping a maximum number of lines.
def append_terminal_output(msg, max_lines=50):  # Increased max_lines for better history
    output = get_terminal_output()
    output += msg + "<br>"
    lines = output.split("<br>")
    # Keep only the last 'max_lines' lines.
    if len(lines) > max_lines:
        lines = lines[-max_lines:]
    session["terminal_output"] = "<br>".join(lines)

# Retrieves AI configuration (URL, API key, and model).
def get_ai_config():
    # API URL: Env -> Session -> App Default
    ai_url = os.environ.get("OPENROUTER_API_URL")
    if not ai_url:
        ai_url = session.get("api_url")
    if not ai_url:
        ai_url = DEFAULT_AI_URL  # Fallback to app default
    
    # API Key: Env -> Session -> App Default
    api_key = os.environ.get("OPENROUTER_API_KEY")
    if not api_key:
        api_key = session.get("api_key")
    if not api_key:
        api_key = DEFAULT_API_KEY  # Fallback to app default
        
    # AI Model: Env -> Session -> App Default
    ai_model = os.environ.get("AI_MODEL")
    if not ai_model:
        ai_model = session.get("ai_model")
    if not ai_model:
        ai_model = DEFAULT_AI_MODEL  # Fallback to app default

    return ai_url, api_key, ai_model

# Error handler for 413 Request Entity Too Large (file upload exceeds limit).
@app.errorhandler(413)
def request_entity_too_large(e):
    append_terminal_output(f"<span style='color:red;'>Upload failed: File is larger than 10MB.</span>")
    return redirect(url_for("index"))

# Route for the main page. Loads data and renders the index.html template.
@app.route("/", methods=["GET"])
def index():
    df = load_data()
    terminal_output = get_terminal_output()
    _, current_api_key, _ = get_ai_config()  # Get current API key status
    api_key_configured = bool(session.get("api_key") or os.environ.get("OPENROUTER_API_KEY") or DEFAULT_API_KEY)

    return render_template(
        "index.html",
        rows=df.to_dict(orient="records"),  # Data rows for the table
        columns=list(df.columns),          # Column names for the table
        terminal_output=terminal_output,   # Output for the terminal display
        api_key_configured=api_key_configured  # Pass this to the template
    )

# Route for handling file uploads.
@app.route("/upload", methods=["POST"])
def upload():
    file = request.files["file"]
    if file:
        # Check if the file has a .csv extension
        if not file.filename.lower().endswith('.csv'):
            append_terminal_output("<span style='color:red;'>Upload failed: Only CSV files are allowed.</span>")
            return redirect(url_for("index"))
            
        try:
            df = pd.read_csv(file)
            # Check if the uploaded CSV is empty or has no columns.
            if df.empty or len(df.columns) == 0:
                append_terminal_output("<span style='color:red;'>Upload failed: File has no valid data or no header.</span>")
            else:
                save_data(df)
                append_terminal_output(f"<span style='color:green;'>Data uploaded. Rows: {len(df)}, Columns: {len(df.columns)}</span>")
        except Exception as e:
            append_terminal_output(f"<span style='color:red;'>Upload failed: {e}</span>")
    else:
        append_terminal_output("<span style='color:red;'>No file selected.</span>")
    return redirect(url_for("index"))

# Route for exporting data as a CSV file.
@app.route("/export")
def export():
    if os.path.exists(DATA_PATH):
        return send_file(DATA_PATH, as_attachment=True)  # Send the CSV file for download.
    else:
        return "No data to export", 404

# Route for checking the AI service status.
@app.route("/check_ai_status", methods=["POST"])
def check_ai_status():
    ai_url, api_key, ai_model = get_ai_config()
    if api_key:  # Check if api_key is not empty
        append_terminal_output(f"<span style='color:green;'>AI Status: API Key is configured. Using model: {ai_model}. URL: {ai_url}</span>")
    else:
        append_terminal_output("<span style='color:red;'>AI Status: API Key is NOT configured. Please set it via the form or environment variable OPENROUTER_API_KEY.</span>")
    return redirect(url_for("index"))

# Route for processing commands generated by the AI.
@app.route("/ai_command", methods=["POST"])
def ai_command():
    user_input = request.form["user_input"]  # User's natural language query
    ai_url, api_key, model = get_ai_config()  # Get config including model

    if not api_key:  # Explicitly check for API key
        append_terminal_output("<span style='color:red;'>AI Error: API Key is not configured. Please set it first (via UI or OPENROUTER_API_KEY environment variable).</span>")
        return redirect(url_for("index"))

    df = load_data()
    columns = list(df.columns)
    # Provide a preview of the data to the AI for context.
    preview = df.head(5).to_dict(orient="records") if not df.empty else []
    columns_str = ", ".join(columns)
    preview_str = "\n".join([str(row) for row in preview])

    # System prompt to guide the AI in generating commands.
    system_prompt = f"""
You are a database assistant. The user has uploaded the following data table:
Available columns: {columns_str}
First 5 rows of data example:
{preview_str}
You can understand the following operations and must strictly return commands in JSON format:

- list: List all data. JSON: {{"operation": "list"}}

- add: Add a new row. JSON: {{"operation": "add", "data": {{"column_name1": value1, "column_name2": value2}}}}
  Note: Missing columns will receive appropriate default values based on their data types.

- add_batch: Add multiple rows at once. Return JSON as:
  {{"operation": "add_batch", "columns": ["col1", "col2"], "values": [[val1_row1, val2_row1], [val1_row2, val2_row2]]}}

- update: Update rows matching conditions. JSON: 
  {{"operation": "update", "conditions": {{"condition_column1": "condition_value1"}}, "data": {{"update_column1": "new_value1"}}}}
  (conditions cannot be empty)
  
  Supports advanced comparison operators for numeric columns:
  - greater than: "column": ">value" 
  - less than: "column": "<value"
  - greater/equal: "column": ">=value"
  - less/equal: "column": "<=value"
  - not equal: "column": "!=value"
  
  Supports pattern matching for string columns:
  - starts with: "column": "prefix*"
  - ends with: "column": "*suffix"
  - contains: "column": "*contains*"

- delete: Delete rows matching conditions. JSON: 
  {{"operation": "delete", "conditions": {{"condition_column1": "condition_value1", "condition_column2": "condition_value2"}}}}
  (conditions cannot be empty)
  
  Supports the same advanced comparison operators as update.
  For bulk deletions (>10 rows), add "confirm": true to the JSON.

- search: Fuzzy search all fields. JSON: {{"operation": "search", "keyword": "search_term"}}

- search_exact: Exact search a specific column. JSON: 
  {{"operation": "search_exact", "column": "column_name", "value": "exact_value"}}
  
  Also supports pattern matching like update/delete.

- columns: Show column information. JSON: {{"operation": "columns"}}

Important notes:
- The 'conditions' object is required in 'update' and 'delete' operations and cannot be an empty object.
- The 'data' object is required in 'add' and 'update' operations.
- Value types should match column data types as much as possible. For string values, please use strings.
- Strictly return only JSON commands. Do not include any other text, explanations, or Markdown tags.
- For missing/null values, use null or the strings "nan" or "na" (returned as NaN in the database).
- If the user request is outside the above scope or incorrectly formatted, please return {{"operation": "error", "message": "Only specified command formats are supported."}}.
"""

    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_input}
    ]
    payload = {
        "model": model,
        "messages": messages,
        "stream": False  # Not using streaming response for simplicity
    }
    headers = {"Authorization": f"Bearer {api_key}"}

    try:
        # Make the API call to the AI service.
        resp = requests.post(f"{ai_url}/chat/completions", json=payload, headers=headers, timeout=30)
        resp.raise_for_status()  # Raise an exception for HTTP errors.
        data = resp.json()
        
        # Extract the AI's response content.
        if "choices" in data and data["choices"]:
            content = data["choices"][0]["message"]["content"]
        elif "message" in data and "content" in data["message"]:  # Some models might use this structure
            content = data["message"]["content"]
        else:
            content = str(data)  # Fallback if structure is unexpected
        
        try:
            # Clean up potential markdown formatting from the AI response.
            if content.strip().startswith("```json"):
                content = content.strip().removeprefix("```json").removesuffix("```").strip()
            # Replace 'undefined' with 'null' for better JSON parsing compatibility.
            content = re.sub(r':\s*undefined', ': null', content)
            ai_cmd = json.loads(content)  # Parse the JSON command.
            append_terminal_output(f"<span style='color:cyan;'>AI suggested command: {ai_cmd}</span>")
            
            cmd_str = ai_cmd_to_str(ai_cmd)  # Convert the AI's JSON command to a string command.
            if cmd_str:
                append_terminal_output(f"<span style='color:green;'>&gt; {cmd_str}</span>")
                df = load_data()
                result = parse_terminal_command(cmd_str, df)  # Execute the command.
                append_terminal_output(result)
            else:
                append_terminal_output("AI failed to generate a valid command.")
        except Exception as e:
            append_terminal_output(f"AI response could not be parsed as a command: {content} ({e}), please retry or optimize the prompt.")
    except Exception as e:
        append_terminal_output(f"AI request failed: {e}")
    return redirect(url_for("index"))

# Route for processing commands entered directly into the terminal.
@app.route("/terminal_command", methods=["POST"])
def terminal_command():
    cmd = request.form["terminal_input"]  # Command string from the terminal input field.
    append_terminal_output(f"<span style='color:green;'>&gt; {cmd}</span>")
    df = load_data()
    msg = parse_terminal_command(cmd, df)  # Parse and execute the command.
    append_terminal_output(msg)
    return redirect(url_for("index"))

# Route for destroying all data
@app.route("/destroy_data", methods=["POST"])
def destroy_data():
    try:
        # Ensure data directory exists
        os.makedirs("data", exist_ok=True)
        
        # Create an empty file rather than removing it
        # This avoids EmptyDataError when the app tries to read it
        open(DATA_PATH, 'w').close()
        
        # Clear terminal output
        session["terminal_output"] = "<span style='color:green;'>All data has been destroyed. Application reset to initial state.</span>"
        return redirect(url_for("index"))
    except Exception as e:
        append_terminal_output(f"<span style='color:red;'>Data destruction failed: {e}</span>")
    return redirect(url_for("index"))

# Converts a DataFrame to an HTML table string for display.
# Shows first 5 and last 5 rows if the DataFrame has more than 10 rows.
def df_to_html_table(df):
    if df.empty:
        return "<div class='text-gray-400'>No data</div>"
    n = len(df)
    header = "<tr>" + "".join(f"<th>{col}</th>" for col in df.columns) + "</tr>"
    body = ""
    if n > 10:
        # Display first 5 rows
        for _, row in df.head(5).iterrows():
            body += "<tr>" + "".join(f"<td>{row[col]}</td>" for col in df.columns) + "</tr>"
        # Ellipsis to indicate omitted rows
        body += f"<tr><td colspan='{len(df.columns)}' class='text-center text-secondary'>... (Total {n} rows, middle part omitted) ...</td></tr>"
        # Display last 5 rows
        for _, row in df.tail(5).iterrows():
            body += "<tr>" + "".join(f"<td>{row[col]}</td>" for col in df.columns) + "</tr>"
    else:
        # Display all rows if 10 or fewer.
        for _, row in df.iterrows():
            body += "<tr>" + "".join(f"<td>{row[col]}</td>" for col in df.columns) + "</tr>"
    return f"""<div style='overflow-x:auto;'><table class='table table-sm table-striped table-bordered' style='background:white;color:#222;'><thead>{header}</thead><tbody>{body}</tbody></table></div>"""

# Parses and executes terminal commands.
def parse_terminal_command(cmd, df):
    try:
        tokens = shlex.split(cmd)  # Split command string into tokens, respecting quotes.
        if not tokens:
            return "No command input"
        op = tokens[0].lower()  # The operation is the first token.
        
        if op == "clear":
            session["terminal_output"] = ""  # Clear terminal history from session.
            return "<span style='color:green;'>Terminal cleared.</span>"
            
        if op == "help":
            # Display help text for available commands.
            return (
                "<pre>Supported commands:\n"
                "help                                 Show this help\n"
                "clear                                Clear terminal content\n"
                "list                                 List all data\n"
                "columns                              Show column information\n"
                "add col1=val1 col2=val2 ...          Add a new row\n"
                "add_batch col1=val1,val2,... col2=val3,val4,...    Add multiple rows at once\n"
                "update cond1=val1 ... set col_to_update1=new_val1 ...  Update rows based on conditions\n"
                "delete cond1=val1 cond2=val2 ...       Delete rows based on conditions\n"
                "delete_all                           Delete all data (with confirmation)\n"
                "search keyword                       Fuzzy search all fields containing the keyword\n"
                "search_exact col=val                 Exactly search for rows where col equals val\n"
                "\nAdvanced features:\n"
                "- For numeric columns, you can use comparison operators: >, <, >=, <=, != \n"
                "- For string columns, you can use patterns: 'prefix*', '*suffix', '*contains*'\n"
                "- Supported special values: nan, na, none, '' (empty string) for missing values\n"
                "</pre>"
            )

        if op == "columns":
            if df.empty:
                return "<span style='color:orange;'>No data loaded. Please upload a CSV file first.</span>"
            # Display column names and their data types.
            cols_info = [f"{col} ({df[col].dtype})" for col in df.columns]
            return f"<pre>Available columns ({len(df.columns)}):\n{', '.join(cols_info)}</pre>"
        
        if op == "list":
            if df.empty:
                return "<span style='color:orange;'>No data available. Please upload a CSV file first.</span>"
            return df_to_html_table(df)  # Display the current data as an HTML table.
            
        elif op == "delete_all":
            if df.empty:
                return "<span style='color:orange;'>No data to delete</span>"
            # Requires confirmation to delete all data.
            if len(tokens) > 1 and tokens[1].lower() == "confirm":
                # Create an empty file directly, which is more consistent
                # with our handling of empty data elsewhere
                os.makedirs("data", exist_ok=True)
                open(DATA_PATH, 'w').close()
                return f"<span style='color:red;'>All data deleted. Original row count: {len(df)}</span>"
            else:
                return f"<span style='color:orange;'>Warning: You are about to delete all {len(df)} rows. To confirm, type: delete_all confirm</span>"

        elif op == "add":
            # Parse arguments for the 'add' command (e.g., col1=val1 col2=val2).
            args = dict(token.split('=', 1) for token in tokens[1:] if '=' in token)
            if not args:
                return "add requires fields and values, e.g., add name=Tom age=18"
            
            new_row_data = {}
            
            # Initialize new row with default values for existing columns to avoid NaNs.
            if not df.empty:
                for col in df.columns:
                    if pd.api.types.is_numeric_dtype(df[col].dtype):
                        new_row_data[col] = 0  # Numeric defaults to 0.
                    elif pd.api.types.is_bool_dtype(df[col].dtype):
                        new_row_data[col] = False  # Boolean defaults to False.
                    else:
                        new_row_data[col] = ""  # String/object defaults to empty string.
            
            # Override defaults with provided values or add new columns.
            for k, v_str in args.items():
                if k in df.columns:  # If column exists, cast value to column's type.
                    new_row_data[k] = _attempt_cast_for_assignment(v_str, df[k])
                else:  # If column is new, infer type.
                    try:
                        new_row_data[k] = pd.to_numeric(v_str)
                    except ValueError:
                        if v_str.lower() in ['true', 'false']:
                            new_row_data[k] = v_str.lower() == 'true'
                        else:
                            new_row_data[k] = v_str
            
            new_row_df = pd.DataFrame([new_row_data])
            
            # If new columns were added, update the main DataFrame's schema.
            if not df.empty:
                for col in new_row_data:
                    if col not in df.columns:
                        df[col] = None  # Initialize new column with None/NA.
            
            # Concatenate the new row to the DataFrame.
            if df.empty:
                df = new_row_df
            else:
                df = pd.concat([df, new_row_df], ignore_index=True)
                
            save_data(df)
            return f"Row added successfully: {new_row_data}"
        
        elif op == "add_batch":
            # Parse arguments for batch adding rows (e.g., col1=v1,v2 col2=v3,v4).
            args = dict(token.split('=', 1) for token in tokens[1:] if '=' in token)
            if not args:
                return "add_batch requires column lists, e.g., add_batch name=Tom,Alice,Bob age=25,30,28"
            
            column_values = {}
            row_count = -1  # Used to ensure all columns have the same number of values.
            
            # Parse comma-separated values for each column.
            for col, val_list_str in args.items():
                values = [v.strip() for v in val_list_str.split(',')]
                if row_count == -1:
                    row_count = len(values)
                elif len(values) != row_count:  # Validate consistent number of values.
                    return f"Error: All columns must have the same number of values. Column '{col}' has {len(values)} values, but expected {row_count}."
                column_values[col] = values
            
            if row_count <= 0:  # Check if any values were actually provided.
                return "Error: No values provided for batch add, or empty value lists."
            
            new_rows = []
            # Construct each new row.
            for i in range(row_count):
                row_data = {}
                # Initialize with defaults if DataFrame is not empty.
                if not df.empty:
                    for col_existing in df.columns:
                        if pd.api.types.is_numeric_dtype(df[col_existing].dtype):
                            row_data[col_existing] = 0
                        elif pd.api.types.is_bool_dtype(df[col_existing].dtype):
                            row_data[col_existing] = False
                        else:
                            row_data[col_existing] = ""
                
                # Populate row with values from the batch, casting or inferring types.
                for col_batch, values_batch in column_values.items():
                    if i < len(values_batch):
                        val_str_current = values_batch[i]
                        if col_batch in df.columns:
                            row_data[col_batch] = _attempt_cast_for_assignment(val_str_current, df[col_batch])
                        else:  # New column, infer type.
                            try:
                                row_data[col_batch] = pd.to_numeric(val_str_current)
                            except ValueError:
                                if val_str_current.lower() in ['true', 'false']:
                                    row_data[col_batch] = val_str_current.lower() == 'true'
                                else:
                                    row_data[col_batch] = val_str_current
                new_rows.append(row_data)
            
            new_rows_df = pd.DataFrame(new_rows)
            
            # Add any new columns from batch to the main DataFrame schema.
            if not df.empty:
                for col_new in new_rows_df.columns:
                    if col_new not in df.columns:
                        df[col_new] = None 
            
            # Concatenate new rows.
            if df.empty:
                df = new_rows_df
            else:
                df = pd.concat([df, new_rows_df], ignore_index=True)
                
            save_data(df)
            return f"Added {row_count} rows successfully"
        
        elif op == "update":
            if df.empty: return "Data is empty, cannot update."
            try:
                set_idx = tokens.index("set")  # Find 'set' keyword to separate conditions and updates.
            except ValueError:
                return "update command format error: missing 'set' keyword. Usage: update condition1=value1 ... set update_col1=new_val1 ..."

            condition_args_str = tokens[1:set_idx]
            update_args_str = tokens[set_idx+1:]

            if not condition_args_str:
                return "update command format error: missing update conditions."
            if not update_args_str:
                return "update command format error: missing fields and values to update."

            # Parse condition arguments.
            conditions = {}
            for token_cond in condition_args_str:
                if '=' not in token_cond: return f"update command format error: condition '{token_cond}' format is incorrect."
                k, v = token_cond.split('=', 1)
                conditions[k] = v
            
            # Parse update arguments.
            updates = {}
            for token_update in update_args_str:
                if '=' not in token_update: return f"update command format error: update '{token_update}' format is incorrect."
                k, v = token_update.split('=', 1)
                updates[k] = v

            # Build a boolean mask based on conditions.
            mask = pd.Series(True, index=df.index)
            for col_name, val_str in conditions.items():
                if col_name not in df.columns: 
                    return f"Error: Column '{col_name}' in conditions does not exist."
                
                column_series = df[col_name]
                current_condition_mask = pd.Series(False, index=df.index)
                val_str_lower = str(val_str).lower()

                # Handle null/empty string conditions.
                if val_str_lower in ['nan', 'na', '<na>', 'none', '']:
                    current_condition_mask = column_series.isna()
                else:
                    # Apply type-specific comparisons and operators.
                    try:
                        if pd.api.types.is_numeric_dtype(column_series.dtype):
                            # Numeric comparisons (>, <, >=, <=, !=, ==).
                            if val_str.startswith('>='): comp_val = pd.to_numeric(val_str[2:]); current_condition_mask = (column_series >= comp_val)
                            elif val_str.startswith('<='): comp_val = pd.to_numeric(val_str[2:]); current_condition_mask = (column_series <= comp_val)
                            elif val_str.startswith('>'): comp_val = pd.to_numeric(val_str[1:]); current_condition_mask = (column_series > comp_val)
                            elif val_str.startswith('<'): comp_val = pd.to_numeric(val_str[1:]); current_condition_mask = (column_series < comp_val)
                            elif val_str.startswith('!='): comp_val = pd.to_numeric(val_str[2:]); current_condition_mask = (column_series != comp_val)
                            else: comp_val = pd.to_numeric(val_str); current_condition_mask = (column_series == comp_val)
                        elif pd.api.types.is_bool_dtype(column_series.dtype):
                            # Boolean comparisons.
                            if val_str_lower in ['true', '1', 't', 'yes']: comp_val = True
                            elif val_str_lower in ['false', '0', 'f', 'no']: comp_val = False
                            else: comp_val = None 
                            if comp_val is not None: current_condition_mask = (column_series == comp_val)
                            else: current_condition_mask = (column_series.astype(str).str.lower() == val_str_lower)  # Fallback to string match if not clear bool
                        else:  # String/object type column comparisons (contains, startswith, endswith, exact).
                            str_series = column_series.astype(str)
                            if val_str.startswith('*') and val_str.endswith('*'): pattern = val_str.strip('*'); current_condition_mask = str_series.str.contains(pattern, case=True, na=False)
                            elif val_str.startswith('*'): suffix = val_str[1:]; current_condition_mask = str_series.str.endswith(suffix, na=False)
                            elif val_str.endswith('*'): prefix = val_str[:-1]; current_condition_mask = str_series.str.startswith(prefix, na=False)
                            else: current_condition_mask = (str_series == str(val_str))
                    except ValueError:  # Fallback if type conversion (e.g., pd.to_numeric) fails.
                        current_condition_mask = (column_series.astype(str) == str(val_str))
                mask &= current_condition_mask  # Combine masks for multiple conditions.
            
            indices_to_update = df.loc[mask].index
            if indices_to_update.empty:
                return "No rows found matching conditions for update."

            # Perform updates on the matched rows.
            for col_update, val_update_str in updates.items():
                if col_update not in df.columns:
                    df[col_update] = None  # Add new column if it doesn't exist.
                
                for idx in indices_to_update:
                    casted_value = _attempt_cast_for_assignment(val_update_str, df[col_update])
                    df.at[idx, col_update] = casted_value  # Use .at for fast scalar setting.
            
            save_data(df)
            return f"Updated {len(indices_to_update)} row(s). Conditions: {conditions}, Updates: {updates}"

        elif op == "delete":
            if df.empty: return "Data is empty, cannot delete."
            condition_args_str = tokens[1:]
            if not condition_args_str:
                return "delete command requires conditions, e.g., delete name=Tom age=30. For bulk delete confirmation, add confirm=yes"

            conditions = {}
            confirm_delete = False  # Flag for confirming bulk deletes.
            
            # Separate 'confirm=yes' from actual conditions.
            actual_condition_args_str = []
            for token_cond in condition_args_str:
                if token_cond.lower() == "confirm=yes":
                    confirm_delete = True
                else:
                    actual_condition_args_str.append(token_cond)

            if not actual_condition_args_str:  # Ensure there are actual conditions beyond just confirmation.
                 return "delete command requires conditions to specify which rows to delete (beyond just 'confirm=yes')."

            # Parse condition arguments.
            for token_cond in actual_condition_args_str:
                if '=' not in token_cond: 
                    return f"delete command format error: condition '{token_cond}' format is incorrect. Expected 'column=value'."
                k, v = token_cond.split('=', 1)
                conditions[k] = v
            
            if not conditions:  # Should be caught by earlier checks, but as a safeguard.
                return "delete command requires conditions to specify which rows to delete."

            # Build a boolean mask based on conditions (similar to update).
            mask = pd.Series(True, index=df.index)
            for col_name, val_str in conditions.items():
                if col_name not in df.columns: 
                    return f"Error: Column '{col_name}' in conditions does not exist."

                column_series = df[col_name]
                current_condition_mask = pd.Series(False, index=df.index)
                val_str_lower = str(val_str).lower()

                if val_str_lower in ['nan', 'na', '<na>', 'none', '']:
                    current_condition_mask = column_series.isna()
                else:
                    try:
                        if pd.api.types.is_numeric_dtype(column_series.dtype):
                            if val_str.startswith('>='): comp_val = pd.to_numeric(val_str[2:]); current_condition_mask = (column_series >= comp_val)
                            elif val_str.startswith('<='): comp_val = pd.to_numeric(val_str[2:]); current_condition_mask = (column_series <= comp_val)
                            elif val_str.startswith('>'): comp_val = pd.to_numeric(val_str[1:]); current_condition_mask = (column_series > comp_val)
                            elif val_str.startswith('<'): comp_val = pd.to_numeric(val_str[1:]); current_condition_mask = (column_series < comp_val)
                            elif val_str.startswith('!='): comp_val = pd.to_numeric(val_str[2:]); current_condition_mask = (column_series != comp_val)
                            else: comp_val = pd.to_numeric(val_str); current_condition_mask = (column_series == comp_val)
                        elif pd.api.types.is_bool_dtype(column_series.dtype):
                            if val_str_lower in ['true', '1', 't', 'yes']: comp_val = True
                            elif val_str_lower in ['false', '0', 'f', 'no']: comp_val = False
                            else: comp_val = None 
                            if comp_val is not None: current_condition_mask = (column_series == comp_val)
                            else: current_condition_mask = (column_series.astype(str).str.lower() == val_str_lower)
                        else:  # String/object type column
                            str_series = column_series.astype(str)
                            if val_str.startswith('*') and val_str.endswith('*'): pattern = val_str.strip('*'); current_condition_mask = str_series.str.contains(pattern, case=True, na=False)
                            elif val_str.startswith('*'): suffix = val_str[1:]; current_condition_mask = str_series.str.endswith(suffix, na=False)
                            elif val_str.endswith('*'): prefix = val_str[:-1]; current_condition_mask = str_series.str.startswith(prefix, na=False)
                            else: current_condition_mask = (str_series == str(val_str))
                    except ValueError:
                        current_condition_mask = (column_series.astype(str) == str(val_str))
                
                mask &= current_condition_mask
            
            indices_to_delete = df.loc[mask].index
            if indices_to_delete.empty:
                return "No rows found matching conditions for delete."
            
            row_count = len(indices_to_delete)
            # Require confirmation if more than 10 rows are to be deleted.
            if row_count > 10 and not confirm_delete:
                original_cmd_conditions = " ".join([f"{k}={v}" for k,v in conditions.items()])
                return f"<span style='color:orange;'>Warning: This command will delete {row_count} rows. To proceed, add 'confirm=yes' to your command. E.g., delete {original_cmd_conditions} confirm=yes</span>"
            else:
                df.drop(indices_to_delete, inplace=True)
                save_data(df)
                return f"<span style='color:red;'>Deleted {row_count} row(s). Conditions: {conditions}</span>"
        
        elif op == "search":  # Fuzzy search across all columns.
            if df.empty:
                return "<span style='color:orange;'>No data to search. Please upload a CSV file first.</span>"
            if len(tokens) < 2:
                return "search command requires a keyword. Usage: search <keyword>"
            keyword = tokens[1]
            # Apply a function to each row to check if any cell contains the keyword (case-insensitive).
            result_df = df[df.apply(lambda row: row.astype(str).str.contains(keyword, case=False, na=False).any(), axis=1)]

            if result_df.empty:
                return f"No rows found containing '{keyword}'."
            return df_to_html_table(result_df)
            
        elif op == "search_exact":  # Exact search on a specific column, with operator support.
            if df.empty:
                return "No data to search."
            if len(tokens) != 2 or '=' not in tokens[1]:
                return "search_exact command format error. Usage: search_exact column_name=value_to_search"
            
            col_name, val_str = tokens[1].split('=', 1)

            if col_name not in df.columns:
                return f"Error: Column '{col_name}' does not exist."

            column_series = df[col_name]
            mask_se = pd.Series(False, index=df.index)  # Mask for search_exact.
            val_str_lower = str(val_str).lower()

            if val_str_lower in ['nan', 'na', '<na>', 'none', '']:
                mask_se = column_series.isna()
            else:
                # Apply type-specific comparisons and operators (similar to update/delete).
                try:
                    if pd.api.types.is_numeric_dtype(column_series.dtype):
                        if val_str.startswith('>='): comp_val = pd.to_numeric(val_str[2:]); mask_se = (column_series >= comp_val)
                        elif val_str.startswith('<='): comp_val = pd.to_numeric(val_str[2:]); mask_se = (column_series <= comp_val)
                        elif val_str.startswith('>'): comp_val = pd.to_numeric(val_str[1:]); mask_se = (column_series > comp_val)
                        elif val_str.startswith('<'): comp_val = pd.to_numeric(val_str[1:]); mask_se = (column_series < comp_val)
                        elif val_str.startswith('!='): comp_val = pd.to_numeric(val_str[2:]); mask_se = (column_series != comp_val)
                        else: comp_val = pd.to_numeric(val_str); mask_se = (column_series == comp_val)
                    elif pd.api.types.is_bool_dtype(column_series.dtype):
                        if val_str_lower in ['true', '1', 't', 'yes']: comp_val = True
                        elif val_str_lower in ['false', '0', 'f', 'no']: comp_val = False
                        else: comp_val = None
                        if comp_val is not None: mask_se = (column_series == comp_val)
                        else: mask_se = (column_series.astype(str).str.lower() == val_str_lower)  # Fallback for non-standard bool strings
                    else:  # String/object type column
                        str_series = column_series.astype(str)
                        if val_str.startswith('*') and val_str.endswith('*'): pattern = val_str.strip('*'); mask_se = str_series.str.contains(pattern, case=True, na=False)
                        elif val_str.startswith('*'): suffix = val_str[1:]; mask_se = str_series.str.endswith(suffix, na=False)
                        elif val_str.endswith('*'): prefix = val_str[:-1]; mask_se = str_series.str.startswith(prefix, na=False)
                        else: mask_se = (str_series == str(val_str))
                except ValueError: 
                    mask_se = (column_series.astype(str) == str(val_str))  # Fallback on error.
            
            result_df = df[mask_se]
            if result_df.empty:
                return f"No rows found where '{col_name}' matches '{val_str}'."
            return df_to_html_table(result_df)
            
        else:
            # Handle unknown commands.
            return f"<span style='color:orange;'>Unknown command: '{op}'. Type 'help' for available commands.</span>"
    except Exception as e:
        # General error handler for command parsing/execution.
        return f"<span style='color:red;'>Error processing command '{cmd}': {e}. Please check syntax or use 'help'.</span>"

# Converts an AI-generated JSON command object into an executable string command.
def ai_cmd_to_str(ai_cmd):
    if not isinstance(ai_cmd, dict) or "operation" not in ai_cmd:
        return None  # Invalid AI command structure.

    op = ai_cmd.get("operation")

    if op == "error":
        return None 
    elif op == "list":
        return "list"
    elif op == "columns":
        return "columns"
    elif op == "add":
        data = ai_cmd.get("data", {})
        if not data: return None  # 'add' requires data.
        return "add " + " ".join([f"{shlex.quote(str(k))}={shlex.quote(str(v))}" for k, v in data.items()])
    elif op == "add_batch":
        columns = ai_cmd.get("columns")
        values_matrix = ai_cmd.get("values")  # Expected as list of lists.
        if not columns or not values_matrix or not isinstance(columns, list) or not isinstance(values_matrix, list):
            return None 
        if not values_matrix: 
            return "add_batch" 
        if not all(isinstance(row, list) and len(row) == len(columns) for row in values_matrix):
            return None 

        parts = []
        for i, col_name in enumerate(columns):
            col_values = []
            for row in values_matrix:
                val = row[i] if i < len(row) else '' 
                col_values.append(str(val))
            parts.append(f"{shlex.quote(col_name)}={','.join(map(shlex.quote, col_values))}")
        return "add_batch " + " ".join(parts)
    elif op == "update":
        conditions = ai_cmd.get("conditions", {})
        data_to_update = ai_cmd.get("data", {})
        if not conditions or not data_to_update: return None 
        
        cond_str = " ".join([f"{shlex.quote(str(k))}={shlex.quote(str(v))}" for k, v in conditions.items()])
        update_str = " ".join([f"{shlex.quote(str(k))}={shlex.quote(str(v))}" for k, v in data_to_update.items()])
        return f"update {cond_str} set {update_str}"
    elif op == "delete":
        conditions = ai_cmd.get("conditions", {})
        if not conditions: return None 
        
        cond_parts = []
        for k,v in conditions.items():
            cond_parts.append(f"{shlex.quote(str(k))}={shlex.quote(str(v))}")
        cond_str = " ".join(cond_parts)
        
        confirm_str = " confirm=yes" if ai_cmd.get("confirm") is True else ""
        return f"delete {cond_str}{confirm_str}".strip()
    elif op == "search":
        keyword = ai_cmd.get("keyword")
        if keyword is None: return None 
        return f"search {shlex.quote(str(keyword))}"
    elif op == "search_exact":
        column = ai_cmd.get("column")
        value = ai_cmd.get("value")
        if column is None or value is None: return None 
        return f"search_exact {shlex.quote(str(column))}={shlex.quote(str(value))}"
        
    return None 

# New route to set the API key
@app.route("/set_api_key", methods=["POST"])
def set_api_key():
    api_key_from_form = request.form.get("api_key_input")
    if api_key_from_form:
        session["api_key"] = api_key_from_form
        append_terminal_output("<span style='color:green;'>API Key has been set for this session.</span>")
    else:
        append_terminal_output("<span style='color:red;'>No API Key provided in the form.</span>")
    return redirect(url_for("index"))

@app.route('/configure_api_key', methods=['POST'])
def configure_api_key():
    api_key = request.form.get('api_key')
    api_url = request.form.get('api_url')
    ai_model = request.form.get('ai_model')
    
    if api_key:
        session['api_key'] = api_key
        flash('API Key configured successfully.', 'success')
    else:
        flash('No API Key provided.', 'error')
        
    # Store custom API URL if provided
    if api_url:
        session['api_url'] = api_url
        
    # Store custom AI model if provided
    if ai_model:
        session['ai_model'] = ai_model
        
    return redirect(url_for('index'))

# Main entry point for running the Flask application.
if __name__ == "__main__":
    app.run(debug=True)  # Run the Flask development server.
