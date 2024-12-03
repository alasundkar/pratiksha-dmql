from flask import Flask, render_template, request
import sqlite3
import pandas as pd
import os

app = Flask(__name__)

# SQLite database file
DATABASE = 'netflixdata.db'  # Ensure this matches your database file name

# Function to execute SQL file
def execute_sql_file(file_path):
    try:
        # Connect to SQLite database
        conn = sqlite3.connect(DATABASE)
        cursor = conn.cursor()
        
        # Read and execute the SQL file
        with open(file_path, 'r') as sql_file:
            sql_script = sql_file.read()
        cursor.executescript(sql_script)  # Use executescript for multiple SQL statements
        conn.commit()
        print(f"SQL script {file_path} executed successfully!")
    except Exception as e:
        print(f"An error occurred while executing the SQL file {file_path}: {e}")
    finally:
        cursor.close()
        conn.close()

# Initialize the database
def init_db():
    # Execute the create.sql and alter.sql files to set up the tables
    execute_sql_file("sql_queries/create.sql")
    execute_sql_file("sql_queries/alter.sql")

# Directory containing the CSV files
csv_directory = "data_files"  # Replace with the path to your CSV directory

def load_csv_to_sqlite(csv_directory, sqlite_db):
    # Connect to the SQLite database
    conn = sqlite3.connect(sqlite_db)
    cursor = conn.cursor()

    try:
        # Loop through all CSV files in the directory
        for filename in os.listdir(csv_directory):
            if filename.endswith(".csv"):  # Check if the file is a CSV
                file_path = os.path.join(csv_directory, filename)
                
                # Infer table name from the file name (remove .csv extension)
                table_name = os.path.splitext(filename)[0]

                # Load the CSV file into a Pandas DataFrame
                df = pd.read_csv(file_path)

                # Write the DataFrame to the SQLite database table
                # Use if_exists='replace' to overwrite existing data
                df.to_sql(table_name, conn, if_exists='replace', index=False)

                print(f"Loaded {filename} into table {table_name}.")
    except Exception as e:
        print(f"An error occurred while loading CSV files: {e}")
    finally:
        cursor.close()
        conn.close()

# Initialize the database and load data
init_db()
load_csv_to_sqlite(csv_directory, DATABASE)

# Function to execute SQL queries
def execute_query(query):
    conn = sqlite3.connect(DATABASE)
    try:
        cursor = conn.cursor()
        cursor.execute(query)
        conn.commit()
        if query.strip().upper().startswith('SELECT'):
            rows = cursor.fetchall()
            columns = [description[0] for description in cursor.description]
            df = pd.DataFrame(rows, columns=columns)
            return df.to_html(index=False), None  # Convert DataFrame to HTML table
        else:
            return None, f"Query executed successfully. {cursor.rowcount} rows affected."
    except Exception as e:
        return None, f"An error occurred: {e}"
    finally:
        cursor.close()
        conn.close()

@app.route('/', methods=['GET', 'POST'])
def index():
    query = ''
    result = None
    message = ''
    if request.method == 'POST':
        query = request.form['query']
        if query.strip():
            result, message = execute_query(query)
        else:
            message = "Please enter a SQL query."
    return render_template('index.html', query=query, result=result, message=message)

if __name__ == '__main__':
    app.run(debug=True)
