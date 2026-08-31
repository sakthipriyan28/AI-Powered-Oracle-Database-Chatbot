# 🤖 AI-Powered Oracle Database Chatbot

An AI-powered natural-language chatbot that allows users to query an Oracle HR database using simple English questions.

The application uses Ollama with Gemma 3 to convert natural-language questions into Oracle SQL queries and Streamlit to provide an interactive chat interface.

## 🚀 Features

- Convert natural-language questions into Oracle SQL
- Query Oracle HR database using a chatbot interface
- Powered by locally hosted Ollama Gemma 3
- Streamlit-based interactive UI
- Supports employee, salary, department, job, and location queries
- Predefined query patterns for common HR questions
- SQL validation for safe read-only database operations
- Oracle-specific ROWNUM support for top/lowest records
- Interactive database result display

## 🛠️ Tech Stack

- Python
- Streamlit
- Ollama
- Gemma 3
- Oracle Database
- Oracle SQL
- Pandas
- python-oracledb
- Regular Expressions

## 🔄 System Workflow

```text
User Question
      ↓
Streamlit Chat Interface
      ↓
Question Processing
      ↓
Common Query Pattern Matching
      ↓
Ollama / Gemma 3
      ↓
Oracle SQL Generation
      ↓
SQL Cleaning & Validation
      ↓
Oracle Database
      ↓
Query Execution
      ↓
Results Displayed in Streamlit