# AI-Powered Oracle Database Chatbot

An AI-powered natural language chatbot that allows users to interact with an Oracle Database using simple English questions.

The application uses Ollama to convert natural language questions into Oracle SQL queries, executes the queries against an Oracle Database, and displays the results through an interactive Streamlit interface.

## Features

- Natural language to Oracle SQL conversion
- Ollama-powered SQL generation
- Oracle Database integration
- SQL query validation
- Interactive Streamlit chatbot interface
- Dynamic database query execution
- Tabular result display
- Supports common employee, department, salary, job, and location queries

## Tech Stack

- Python
- Streamlit
- Ollama
- Oracle Database
- Oracle SQL
- Pandas

## How It Works

User Question
        ?
Streamlit Chat Interface
        ?
Ollama
        ?
Oracle SQL Generation
        ?
SQL Validation
        ?
Oracle Database
        ?
Query Execution
        ?
Results Displayed in Streamlit

## Example

User:

    Which department does Steven work in?

The application converts the natural language question into an Oracle SQL query, executes it against the database, and displays the result.

## Installation

### 1. Clone the Repository

    git clone https://github.com/YOUR_USERNAME/AI-Powered-Oracle-Database-Chatbot.git

### 2. Navigate to the Project

    cd AI-Powered-Oracle-Database-Chatbot

### 3. Create a Virtual Environment

    python -m venv .venv

### 4. Activate the Virtual Environment

Windows:

    .venv\Scripts\activate

### 5. Install Dependencies

    pip install -r requirements.txt

## Ollama Setup

Install Ollama and make sure the required model is available.

The application currently uses:

    gemma3

## Oracle Database Setup

The application is designed to work with an Oracle Database using the Oracle HR schema.

Make sure the Oracle Database and Oracle Instant Client are installed and configured on your system.

## Run the Application

    streamlit run natural.py

The Streamlit application will open in your browser.

## Security

Database credentials are entered through the Streamlit interface and are not stored in the source code.

Do not commit passwords, API keys, or other sensitive information to GitHub.

## Future Enhancements

- Conversation history
- Support for additional database schemas
- Advanced SQL validation
- Improved natural language understanding
- Voice-based database queries
- Multi-database support

## Author

Sakthi Priyan
