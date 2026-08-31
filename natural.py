import streamlit as st
import oracledb
import pandas as pd
import ollama
import re
ORACLE_CLIENT_LIB_DIR = r"D:\Oracle\instantclient_19_32"
ORACLE_DSN = "localhost:1521/xe"
OLLAMA_MODEL = "gemma3"
try:
    oracledb.init_oracle_client(lib_dir=ORACLE_CLIENT_LIB_DIR)
except oracledb.ProgrammingError:
    # Safe when Streamlit reruns the script after the client
    # has already been initialized.
    pass
st.set_page_config(
    page_title="Oracle DB AI Chatbot",
    page_icon="🤖",
    layout="wide"
)
st.title("🤖 Oracle DB AI Chatbot Agent")
with st.sidebar:
    st.header("🔑 Oracle DB Credentials")

    db_username = st.text_input(
        "Oracle Username",
        type="password"
    )
    db_password = st.text_input(
        "Oracle Password",
        type="password"
    )
if "messages" not in st.session_state:
    st.session_state.messages = []


for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.write(message["content"])
DATABASE_SCHEMA = """
You are generating Oracle SQL for the standard Oracle HR schema.

AVAILABLE TABLES:

EMPLOYEES
---------
EMPLOYEE_ID
FIRST_NAME
LAST_NAME
EMAIL
PHONE_NUMBER
HIRE_DATE
JOB_ID
SALARY
COMMISSION_PCT
MANAGER_ID
DEPARTMENT_ID

DEPARTMENTS
-----------
DEPARTMENT_ID
DEPARTMENT_NAME
MANAGER_ID
LOCATION_ID

JOBS
----
JOB_ID
JOB_TITLE
MIN_SALARY
MAX_SALARY

LOCATIONS
---------
LOCATION_ID
STREET_ADDRESS
POSTAL_CODE
CITY
STATE_PROVINCE
COUNTRY_ID

COUNTRIES
---------
COUNTRY_ID
COUNTRY_NAME
REGION_ID

REGIONS
-------
REGION_ID
REGION_NAME

JOB_HISTORY
-----------
EMPLOYEE_ID
START_DATE
END_DATE
JOB_ID
DEPARTMENT_ID
"""
def generate_common_query(user_question):
    """
    Handle common HR questions deterministically.

    Common Oracle-specific queries are generated in Python instead
    of relying on Ollama to choose Oracle row-limiting syntax.
    """

    question = user_question.strip().lower()
    top_patterns = [
        r"\btop\s+(\d+)\s+employees?\b",
        r"\bfirst\s+(\d+)\s+employees?\b",
        r"\bhighest\s+paid\s+(\d+)\s+employees?\b",
        r"\bhighest[-\s]paid\s+(\d+)\s+employees?\b",
    ]

    for pattern in top_patterns:
        match = re.search(pattern, question)

        if match:
            n = int(match.group(1))
            if 1 <= n <= 1000:
                return f"""
SELECT employee_id,
       first_name,
       last_name,
       salary
FROM (
    SELECT employee_id,
           first_name,
           last_name,
           salary
    FROM employees
    ORDER BY salary DESC
)
WHERE ROWNUM <= {n}
""".strip()
    lowest_patterns = [
        r"\blowest\s+(\d+)\s+employees?\b",
        r"\bleast\s+(\d+)\s+employees?\b",
        r"\blowest\s+paid\s+(\d+)\s+employees?\b",
        r"\blowest[-\s]paid\s+(\d+)\s+employees?\b",
    ]

    for pattern in lowest_patterns:
        match = re.search(pattern, question)

        if match:
            n = int(match.group(1))
            if 1 <= n <= 1000:
                return f"""
SELECT employee_id,
       first_name,
       last_name,
       salary
FROM (
    SELECT employee_id,
           first_name,
           last_name,
           salary
    FROM employees
    ORDER BY salary ASC
)
WHERE ROWNUM <= {n}
""".strip()

    # -----------------------------------------------------
    # HIGHEST-PAID SINGLE EMPLOYEE
    # -----------------------------------------------------

    if (
        "highest paid employee" in question
        or "highest-paid employee" in question
        or "employee with the highest salary" in question
    ):
        return """
SELECT employee_id,
       first_name,
       last_name,
       salary
FROM (
    SELECT employee_id,
           first_name,
           last_name,
           salary
    FROM employees
    ORDER BY salary DESC
)
WHERE ROWNUM = 1
""".strip()

    # -----------------------------------------------------
    # LOWEST-PAID SINGLE EMPLOYEE
    # -----------------------------------------------------

    if (
        "lowest paid employee" in question
        or "lowest-paid employee" in question
        or "employee with the lowest salary" in question
    ):
        return """
SELECT employee_id,
       first_name,
       last_name,
       salary
FROM (
    SELECT employee_id,
           first_name,
           last_name,
           salary
    FROM employees
    ORDER BY salary ASC
)
WHERE ROWNUM = 1
""".strip()

    # -----------------------------------------------------
    # HIGHEST AVERAGE SALARY BY DEPARTMENT
    # -----------------------------------------------------

    if (
        "department" in question
        and "average salary" in question
        and (
            "highest" in question
            or "maximum" in question
            or "max" in question
        )
    ):
        return """
SELECT department_id,
       department_name,
       average_salary
FROM (
    SELECT d.department_id,
           d.department_name,
           AVG(e.salary) AS average_salary
    FROM employees e
    JOIN departments d
      ON e.department_id = d.department_id
    GROUP BY d.department_id, d.department_name
    ORDER BY AVG(e.salary) DESC
)
WHERE ROWNUM = 1
""".strip()

    # -----------------------------------------------------
    # LOWEST AVERAGE SALARY BY DEPARTMENT
    # -----------------------------------------------------

    if (
        "department" in question
        and "average salary" in question
        and (
            "lowest" in question
            or "least" in question
            or "minimum" in question
            or "min" in question
        )
    ):
        return """
SELECT department_id,
       department_name,
       average_salary
FROM (
    SELECT d.department_id,
           d.department_name,
           AVG(e.salary) AS average_salary
    FROM employees e
    JOIN departments d
      ON e.department_id = d.department_id
    GROUP BY d.department_id, d.department_name
    ORDER BY AVG(e.salary) ASC
)
WHERE ROWNUM = 1
""".strip()

    # -----------------------------------------------------
    # AVERAGE SALARY FOR EACH DEPARTMENT
    # -----------------------------------------------------

    if (
        "average salary" in question
        and "department" in question
        and (
            "each" in question
            or "every" in question
            or "all" in question
            or "department-wise" in question
            or "department wise" in question
        )
    ):
        return """
SELECT d.department_id,
       d.department_name,
       AVG(e.salary) AS average_salary
FROM employees e
JOIN departments d
  ON e.department_id = d.department_id
GROUP BY d.department_id, d.department_name
ORDER BY AVG(e.salary) DESC
""".strip()

    # -----------------------------------------------------
    # EMPLOYEE COUNT BY DEPARTMENT
    # -----------------------------------------------------

    if (
        "department" in question
        and "employee" in question
        and (
            "how many" in question
            or "count" in question
            or "number of" in question
        )
    ):
        return """
SELECT d.department_id,
       d.department_name,
       COUNT(e.employee_id) AS employee_count
FROM departments d
LEFT JOIN employees e
  ON d.department_id = e.department_id
GROUP BY d.department_id, d.department_name
ORDER BY COUNT(e.employee_id) DESC
""".strip()

    # -----------------------------------------------------
    # TOTAL NUMBER OF EMPLOYEES
    # -----------------------------------------------------

    if (
        "how many employees" in question
        or "number of employees" in question
        or "count of employees" in question
        or "total employees" in question
    ):
        return """
SELECT COUNT(*) AS employee_count
FROM employees
""".strip()

    # -----------------------------------------------------
    # OVERALL AVERAGE SALARY
    # -----------------------------------------------------

    if (
        "average salary" in question
        and "department" not in question
    ):
        return """
SELECT AVG(salary) AS average_salary
FROM employees
""".strip()

    # -----------------------------------------------------
    # EMPLOYEE LOCATION
    # -----------------------------------------------------

    location_patterns = [
        r"^([a-z][a-z .'-]+)\s+where\s+from$",
        r"^where\s+is\s+([a-z][a-z .'-]+)\s+from$",
        r"^where\s+does\s+([a-z][a-z .'-]+)\s+(?:live|work)$",
        r"^which\s+city\s+does\s+([a-z][a-z .'-]+)\s+work\s+in$",
        r"^which\s+country\s+is\s+([a-z][a-z .'-]+)\s+in$",
        r"^([a-z][a-z .'-]+)'s\s+location$",
    ]

    for pattern in location_patterns:
        match = re.search(pattern, question)

        if match:
            name = match.group(1).strip().upper()

            return f"""
SELECT e.first_name,
       e.last_name,
       l.city,
       l.state_province,
       c.country_name
FROM employees e
JOIN departments d
  ON e.department_id = d.department_id
JOIN locations l
  ON d.location_id = l.location_id
JOIN countries c
  ON l.country_id = c.country_id
WHERE UPPER(e.first_name) = '{name}'
""".strip()

    # -----------------------------------------------------
    # EMPLOYEE DEPARTMENT
    # -----------------------------------------------------

    department_patterns = [
        r"^([a-z][a-z .'-]+)\s+department$",
        r"^which\s+department\s+does\s+([a-z][a-z .'-]+)\s+work\s+in$",
        r"^what\s+department\s+does\s+([a-z][a-z .'-]+)\s+work\s+in$",
    ]

    for pattern in department_patterns:
        match = re.search(pattern, question)

        if match:
            name = match.group(1).strip().upper()

            return f"""
SELECT e.employee_id,
       e.first_name,
       e.last_name,
       d.department_name
FROM employees e
JOIN departments d
  ON e.department_id = d.department_id
WHERE UPPER(e.first_name) = '{name}'
""".strip()

    # -----------------------------------------------------
    # EMPLOYEE JOB
    # -----------------------------------------------------

    job_patterns = [
        r"^([a-z][a-z .'-]+)\s+job$",
        r"^what\s+is\s+([a-z][a-z .'-]+)'?s?\s+job$",
        r"^what\s+is\s+([a-z][a-z .'-]+)'?s?\s+job\s+title$",
        r"^which\s+job\s+does\s+([a-z][a-z .'-]+)\s+have$",
    ]

    for pattern in job_patterns:
        match = re.search(pattern, question)

        if match:
            name = match.group(1).strip().upper()

            return f"""
SELECT e.employee_id,
       e.first_name,
       e.last_name,
       j.job_title
FROM employees e
JOIN jobs j
  ON e.job_id = j.job_id
WHERE UPPER(e.first_name) = '{name}'
""".strip()

    # -----------------------------------------------------
    # EMPLOYEE SALARY
    # -----------------------------------------------------

    salary_patterns = [
        r"^([a-z][a-z .'-]+)\s+salary$",
        r"^what\s+is\s+([a-z][a-z .'-]+)'?s?\s+salary$",
        r"^how\s+much\s+does\s+([a-z][a-z .'-]+)\s+earn$",
    ]

    for pattern in salary_patterns:
        match = re.search(pattern, question)

        if match:
            name = match.group(1).strip().upper()

            return f"""
SELECT employee_id,
       first_name,
       last_name,
       salary
FROM employees
WHERE UPPER(first_name) = '{name}'
""".strip()

    # -----------------------------------------------------
    # EMPLOYEE EMAIL
    # -----------------------------------------------------

    email_patterns = [
        r"^([a-z][a-z .'-]+)\s+email$",
        r"^what\s+is\s+([a-z][a-z .'-]+)'?s?\s+email$",
        r"^what\s+is\s+the\s+email\s+of\s+([a-z][a-z .'-]+)$",
    ]

    for pattern in email_patterns:
        match = re.search(pattern, question)

        if match:
            name = match.group(1).strip().upper()

            return f"""
SELECT employee_id,
       first_name,
       last_name,
       email
FROM employees
WHERE UPPER(first_name) = '{name}'
""".strip()

    # -----------------------------------------------------
    # EMPLOYEE HIRE DATE
    # -----------------------------------------------------

    hire_patterns = [
        r"^([a-z][a-z .'-]+)\s+hire date$",
        r"^when\s+was\s+([a-z][a-z .'-]+)\s+hired$",
        r"^when\s+did\s+([a-z][a-z .'-]+)\s+join$",
    ]

    for pattern in hire_patterns:
        match = re.search(pattern, question)

        if match:
            name = match.group(1).strip().upper()

            return f"""
SELECT employee_id,
       first_name,
       last_name,
       hire_date
FROM employees
WHERE UPPER(first_name) = '{name}'
""".strip()

    # -----------------------------------------------------
    # SHOW ALL EMPLOYEES
    # -----------------------------------------------------

    if question in {
        "show all employees",
        "show all employee",
        "list all employees",
        "list employees",
        "display all employees",
        "all employees",
    }:
        return """
SELECT *
FROM employees
""".strip()

    # Otherwise let Ollama handle more complex questions.
    return None


# =========================================================
# GENERATE SQL USING OLLAMA
# =========================================================

def generate_sql(user_question, model):
    common_query = generate_common_query(user_question)

    if common_query:
        return common_query

    prompt = f"""
You are an expert Oracle SQL developer.

Convert the user's natural-language question into ONE valid
Oracle SELECT query.

{DATABASE_SCHEMA}

IMPORTANT RULES:

1. Return ONLY the SQL query.
2. Do NOT return explanations.
3. Do NOT use Markdown code fences.
4. Do NOT return ```sql.
5. The query must be a SELECT query.
6. Do NOT generate INSERT.
7. Do NOT generate UPDATE.
8. Do NOT generate DELETE.
9. Do NOT generate DROP.
10. Do NOT generate ALTER.
11. Do NOT generate CREATE.
12. Do NOT generate TRUNCATE.
13. Do NOT generate MERGE.
14. Do NOT generate GRANT.
15. Do NOT generate REVOKE.
16. Do NOT generate COMMIT.
17. Do NOT generate ROLLBACK.
18. Do NOT generate EXECUTE.
19. Do NOT generate BEGIN.
20. Do NOT generate DECLARE.
21. Do NOT generate multiple SQL statements.
22. Use Oracle SQL syntax.
23. Use JOIN when information is in another table.
24. Use UPPER() for case-insensitive name matching.
25. The final query must NOT contain a semicolon.
26. Do NOT use LIMIT.
27. Do NOT use MySQL TOP syntax.
28. Do NOT use FETCH FIRST.
29. For "top N" or "highest N" records, use Oracle ROWNUM.
30. When selecting the highest N values, ORDER BY the relevant
    column DESC inside a subquery, then apply WHERE ROWNUM <= N.
31. When selecting the lowest N values, ORDER BY the relevant
    column ASC inside a subquery, then apply WHERE ROWNUM <= N.
32. NEVER use LIMIT.
33. NEVER use FETCH FIRST.
34. NEVER use TOP.
35. For department average-salary ranking, use GROUP BY department,
    ORDER BY AVG(e.salary) DESC or ASC inside a subquery, then use
    WHERE ROWNUM = 1.
36. "Which department has the highest average salary?" means:
    group employees by department, calculate AVG(e.salary), sort
    descending, and return the first row using Oracle ROWNUM.

IMPORTANT TOP-N PATTERN:

SELECT columns
FROM (
    SELECT columns
    FROM table
    ORDER BY column DESC
)
WHERE ROWNUM <= N

Examples:

Question:
Show all employees

SQL:
SELECT * FROM employees

Question:
Show employees whose salary is greater than 5000

SQL:
SELECT employee_id, first_name, last_name, salary
FROM employees
WHERE salary > 5000
ORDER BY salary DESC

Question:
What is Steven's salary?

SQL:
SELECT employee_id, first_name, last_name, salary
FROM employees
WHERE UPPER(first_name) = 'STEVEN'

Question:
Which department does Steven work in?

SQL:
SELECT e.employee_id,
       e.first_name,
       e.last_name,
       d.department_name
FROM employees e
JOIN departments d
  ON e.department_id = d.department_id
WHERE UPPER(e.first_name) = 'STEVEN'

Question:
Where is Steven from?

SQL:
SELECT e.first_name,
       e.last_name,
       l.city,
       l.state_province,
       c.country_name
FROM employees e
JOIN departments d
  ON e.department_id = d.department_id
JOIN locations l
  ON d.location_id = l.location_id
JOIN countries c
  ON l.country_id = c.country_id
WHERE UPPER(e.first_name) = 'STEVEN'

Question:
Which department has the highest average salary?

SQL:
SELECT department_id,
       department_name,
       average_salary
FROM (
    SELECT d.department_id,
           d.department_name,
           AVG(e.salary) AS average_salary
    FROM employees e
    JOIN departments d
      ON e.department_id = d.department_id
    GROUP BY d.department_id, d.department_name
    ORDER BY AVG(e.salary) DESC
)
WHERE ROWNUM = 1

Question:
Show top 10 employees

SQL:
SELECT employee_id,
       first_name,
       last_name,
       salary
FROM (
    SELECT employee_id,
           first_name,
           last_name,
           salary
    FROM employees
    ORDER BY salary DESC
)
WHERE ROWNUM <= 10

User question:
{user_question}
"""

    response = ollama.chat(
        model=model,
        messages=[
            {
                "role": "user",
                "content": prompt
            }
        ]
    )

    sql = response["message"]["content"].strip()

    return sql


# =========================================================
# CLEAN GENERATED SQL
# =========================================================

def clean_sql(sql):
    sql = sql.strip()

    # Remove Markdown code fences.
    sql = re.sub(
        r"```sql\s*",
        "",
        sql,
        flags=re.IGNORECASE
    )

    sql = re.sub(
        r"```",
        "",
        sql
    )

    # Remove accidental leading/trailing whitespace.
    sql = sql.strip()

    # Remove a trailing semicolon because execution uses
    # a single SQL statement without a terminator.
    sql = sql.rstrip(";").strip()

    return sql


# =========================================================
# SQL SECURITY VALIDATION
# =========================================================

def validate_sql(sql):
    sql = sql.strip()
    sql_lower = sql.lower()

    # Must start with SELECT.
    if not re.match(r"^\s*select\b", sql_lower):
        return False, "Only SELECT queries are allowed."

    dangerous_keywords = [
        "insert",
        "update",
        "delete",
        "drop",
        "alter",
        "create",
        "truncate",
        "merge",
        "grant",
        "revoke",
        "commit",
        "rollback",
        "execute",
        "begin",
        "declare"
    ]

    for keyword in dangerous_keywords:
        pattern = r"\b" + re.escape(keyword) + r"\b"

        if re.search(pattern, sql_lower):
            return False, f"Unsafe SQL detected: {keyword.upper()}"

    # Prevent multiple statements.
    if ";" in sql:
        return False, "Multiple SQL statements are not allowed."

    # Prevent SQL comments.
    if "--" in sql or "/*" in sql or "*/" in sql:
        return False, "SQL comments are not allowed."

    # Prevent non-Oracle row limiting syntax that commonly
    # causes ORA-00933 on older Oracle versions.
    if re.search(r"\blimit\s+\d+", sql_lower):
        return False, "LIMIT is not supported. Use Oracle ROWNUM."

    if re.search(r"\bfetch\s+first\b", sql_lower):
        return False, "FETCH FIRST is disabled. Use Oracle ROWNUM."

    return True, ""


# =========================================================
# GENERATE SIMPLE ANSWER FROM DATAFRAME
# =========================================================

def create_answer(df):
    if df.empty:
        return "No records were found for your question."

    row_count = len(df)
    column_count = len(df.columns)

    if row_count == 1:
        if column_count == 1:
            value = df.iloc[0, 0]
            return f"The answer is: **{value}**"

        return (
            f"I found **1 matching record** "
            f"with {column_count} fields."
        )

    return f"I found **{row_count} matching records**."


# =========================================================
# DATABASE EXECUTION
# =========================================================

def execute_query(sql, username, password):
    connection = None

    try:
        connection = oracledb.connect(
            user=username,
            password=password,
            dsn=ORACLE_DSN
        )

        df = pd.read_sql(
            sql,
            connection
        )

        return df

    finally:
        if connection is not None:
            connection.close()


# =========================================================
# CHAT INPUT
# =========================================================

user_query = st.chat_input(
    "Ask your question here based on the database..."
)


# =========================================================
# PROCESS QUESTION
# =========================================================

if user_query:

    # -----------------------------------------------------
    # Display user question
    # -----------------------------------------------------

    st.session_state.messages.append(
        {
            "role": "user",
            "content": user_query
        }
    )

    with st.chat_message("user"):
        st.write(user_query)

    # -----------------------------------------------------
    # Check Oracle credentials
    # -----------------------------------------------------

    if not db_username or not db_password:

        with st.chat_message("assistant"):
            st.error(
                "⚠️ Please enter your Oracle username and password."
            )

    else:

        try:

            # =================================================
            # STEP 1: GENERATE SQL
            # =================================================

            with st.spinner(
                "⏱️ Generating your database answer..."
            ):
                generated_sql = generate_sql(
                    user_query,
                    OLLAMA_MODEL
                )

            # =================================================
            # STEP 2: CLEAN SQL
            # =================================================

            sql_query = clean_sql(
                generated_sql
            )

            # =================================================
            # STEP 3: VALIDATE SQL
            # =================================================

            valid, error_message = validate_sql(
                sql_query
            )

            if not valid:

                with st.chat_message("assistant"):
                    st.error(
                        f"❌ {error_message}"
                    )

            else:

                # =================================================
                # SHOW GENERATED SQL IN STREAMLIT
                # =================================================
                # The SQL is generated internally and displayed here
                # after validation and before execution.

                with st.chat_message("assistant"):
                    st.subheader("🧠 Generated SQL Query")
                    st.code(
                        sql_query,
                        language="sql"
                    )

                # =================================================
                # STEP 4: CONNECT + EXECUTE SQL
                # =================================================

                with st.spinner(
                    "🔗 Connecting to Oracle Database..."
                ):
                    with st.spinner(
                        "⚡ Executing database query..."
                    ):
                        df = execute_query(
                            sql_query,
                            db_username,
                            db_password
                        )

                # =================================================
                # STEP 5: DISPLAY RESULT
                # =================================================

                with st.chat_message("assistant"):

                    st.success(
                        "✅ Oracle Database connected successfully!"
                    )

                    st.subheader(
                        "Answer for the Question asked above"
                    )

                    if df.empty:

                        st.info(
                            "No records found."
                        )

                    else:

                        st.dataframe(
                            df,
                            use_container_width=True,
                            hide_index=True
                        )

                    # =================================================
                    # STEP 6: SIMPLE ANSWER
                    # =================================================

                    st.subheader(
                        "💬 Answer"
                    )

                    answer = create_answer(
                        df
                    )

                    st.write(
                        answer
                    )

                # =================================================
                # SAVE ASSISTANT MESSAGE
                # =================================================

                st.session_state.messages.append(
                    {
                        "role": "assistant",
                        "content": (
                            f"Query executed successfully. "
                            f"{len(df)} record(s) found."
                        )
                    }
                )

        # =====================================================
        # ERROR HANDLING
        # =====================================================

        except ollama.ResponseError as e:

            with st.chat_message("assistant"):

                st.error(
                    f"❌ Ollama Error: {e}"
                )

                st.info(
                    f"Make sure the Ollama model "
                    f"'{OLLAMA_MODEL}' is installed and running."
                )

        except oracledb.Error as e:

            with st.chat_message("assistant"):

                st.error(
                    f"❌ Oracle Database Error: {e}"
                )

        except Exception as e:

            with st.chat_message("assistant"):

                st.error(
                    f"❌ Application Error: {e}"
                )