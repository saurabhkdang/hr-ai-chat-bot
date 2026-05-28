# def validate_sql_old(query: str) -> (bool, str):

# def normalize_rows(result):

# def build_schema_prompt(schema):

# def retry_with_error(user_query, sql_query, error_msg, schema_prompt):

# def execute_with_retry(user_query, sql_query, schema_prompt, max_retries=2):

# def enforce_limit(query: str, limit=10):

# def detect_response_type(rows):

# def format_response(rows, user_query):

# def generate_summary(rows, user_query):

# def build_final_response(rows, user_query):

def format_vector_response(docs, user_query):
    if not docs:
        return {
            "type": "text",
            "message": "No relevant information found."
        }

    # Combine top docs
    combined_text = "\n".join([d["text"] for d in docs[:3]])

    summary = ask_ai(f"""
    Answer the question based on the context below.

    Question:
    {user_query}

    Context:
    {combined_text}

    Give a clear and concise answer.
    """)

    return {
        "type": "text",
        "message": summary
    }

# def handle_query(user_query):

# def handle_sql_query(user_query, SCHEMA_PROMPT):

# def handle_vector_query(user_query):