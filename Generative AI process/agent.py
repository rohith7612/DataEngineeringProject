import pandas as pd
from db import engine, get_dynamic_schema
from openai import OpenAI
from dotenv import load_dotenv
import os
import collections
import re
from threading import Lock
from sqlalchemy import text

load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), '.env'))

client = OpenAI(
    api_key=os.getenv("OPENAI_API_KEY")
)

class QueryResult:
    """
    A lazy-loaded, pandas-compatible database query result object.
    Bypasses pandas DataFrame creation unless .to_string() is called.
    """
    def __init__(self, records):
        self._records = records
        self._df = None

    def to_dict(self, orient="records"):
        return self._records

    def to_string(self, *args, **kwargs):
        if self._df is None:
            self._df = pd.DataFrame(self._records)
        return self._df.to_string(*args, **kwargs)

    def __repr__(self):
        return self.to_string()

class ThreadSafeLRUCache:
    def __init__(self, maxsize=128):
        self.maxsize = maxsize
        self.cache = collections.OrderedDict()
        self.lock = Lock()
        
    def get(self, key):
        with self.lock:
            if key not in self.cache:
                return None
            self.cache.move_to_end(key)
            return self.cache[key]
            
    def set(self, key, value):
        with self.lock:
            if key in self.cache:
                self.cache.move_to_end(key)
            self.cache[key] = value
            if len(self.cache) > self.maxsize:
                self.cache.popitem(last=False)

sql_cache = ThreadSafeLRUCache(maxsize=100)
explanation_cache = ThreadSafeLRUCache(maxsize=100)

def execute_query(query):
    # Safety Check: Only allow read-only query execution
    cleaned = query.strip()
    words = re.findall(r'\b\w+\b', cleaned.lower())
    if words and words[0] not in ('select', 'with', 'explain', 'show', 'values'):
        raise ValueError(f"Security Exception: Only read-only queries (SELECT, WITH) are allowed. Blocked query starting with: '{words[0]}'")

    with engine.connect() as conn:
        result = conn.execute(text(query))
        if result.returns_rows:
            records = [dict(row._mapping) for row in result]
        else:
            records = []
        return QueryResult(records)

def get_region_summary():
    query = """
    SELECT *
    FROM gold_region_sales
    """
    
    data = execute_query(query)
    
    prompt = f"""
    Analyze this regional sales data:
    
    {data.to_string()}
    
    Give an executive summary.
    """
    
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {
                "role": "user",
                "content": prompt
            }
        ]
    )
    
    return response.choices[0].message.content

def generate_sql(question):
    # Fetch latest schema from DB
    current_schema = get_dynamic_schema()
    
    norm_question = " ".join(question.lower().strip().split())
    cached_sql = sql_cache.get(norm_question)
    if cached_sql:
        return cached_sql

    prompt = f"""
    You are a PostgreSQL expert.

    Database Schema:
    {current_schema}

    Instructions:
    1. Generate ONLY raw PostgreSQL SQL.
    2. Use the table that most closely matches the user's request.
    3. CRITICAL: You MUST wrap all column names in double quotes (e.g., "Region", "Total_Sales", "Total_Profit", "Ship_Mode") because they are case-sensitive.
    4. Do not wrap the SQL in a markdown code block.
    5. If a specific metric (like Profit) is requested, use the appropriate column (like "Total_Profit").

    Question:
    {question}
    """

    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {
                "role": "user",
                "content": prompt
            }
        ]
    )

    result_sql = response.choices[0].message.content
    

    result_sql = result_sql.strip()
    if result_sql.startswith("```"):
        result_sql = re.sub(r'^```(?:sql)?\n?', '', result_sql)
        result_sql = re.sub(r'\n?```$', '', result_sql)
    result_sql = result_sql.strip()
    
    sql_cache.set(norm_question, result_sql)
    return result_sql

def explain_results(question, data):
    norm_question = " ".join(question.lower().strip().split())
    cache_key = (norm_question, data)
    cached_explanation = explanation_cache.get(cache_key)
    if cached_explanation:
        return cached_explanation

    prompt = f"""
    CEO Question:
    {question}

    Query Results:
    {data}

    Provide a concise executive summary.
    """

    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {
                "role": "user",
                "content": prompt
            }
        ]
    )

    explanation = response.choices[0].message.content
    explanation_cache.set(cache_key, explanation)
    return explanation

def answer_question(question):
    """
    Orchestrates the process: Generates SQL, executes it with self-healing retries, 
    and summarizes results.
    """
    sql_query = generate_sql(question)
    
    attempts = 0
    max_retries = 2
    last_error = None
    
    while attempts <= max_retries:
        try:
            # Attempt to execute the query
            result = execute_query(sql_query)
            
            # If successful, explain the results
            summary = explain_results(question, result.to_string())
            
            return {
                "sql": sql_query,
                "summary": summary,
                "data": result.to_dict(orient="records"),
                "status": "success" if attempts == 0 else "self_corrected",
                "attempts": attempts + 1
            }
            
        except Exception as e:
            attempts += 1
            last_error = str(e)
            
            if attempts > max_retries:
                break
                
            # Self-Healing: Send the error back to the AI to get a fix
            correction_prompt = f"""
            The following SQL query failed:
            {sql_query}

            The database returned this error:
            {last_error}

            Please analyze the error and provide a CORRECTED PostgreSQL query.
            Ensure you follow the latest database schema:
            {get_dynamic_schema()}
            """
            
            # We don't want to cache the "error correction" prompt in the main SQL cache 
            # with the original question's key, so we call the LLM again.
            sql_query = generate_sql(correction_prompt)

    # If we reached here, retries failed
    raise Exception(f"Query failed after {max_retries} attempts. Final Error: {last_error}")
