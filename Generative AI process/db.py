from sqlalchemy import create_engine, text
from dotenv import load_dotenv
import os
from urllib.parse import quote_plus

load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), '.env'))

db_user = quote_plus(os.getenv('DB_USER') or '')
db_password = quote_plus(os.getenv('DB_PASSWORD') or '')
db_host = os.getenv('DB_HOST')
db_port = os.getenv('DB_PORT')
db_name = os.getenv('DB_NAME')

connection_uri = f"postgresql://{db_user}:{db_password}@{db_host}:{db_port}/{db_name}"

engine = create_engine(
    connection_uri,
    pool_size=10,
    max_overflow=20,
    pool_recycle=1800,
    pool_pre_ping=True,
    connect_args={"connect_timeout": 10}
)

def get_dynamic_schema():
    """
    Queries the database metadata to build a schema string for the AI.
    """
    query = """
    SELECT table_name, column_name
    FROM information_schema.columns
    WHERE table_schema = 'public'
    ORDER BY table_name, ordinal_position;
    """
    try:
        with engine.connect() as conn:
            result = conn.execute(text(query))
            schema_dict = {}
            for row in result:
                table = row[0]
                column = row[1]
                if table not in schema_dict:
                    schema_dict[table] = []
                schema_dict[table].append(f'- "{column}"')

            schema_string = "Database Schema:\n\n"
            for table, columns in schema_dict.items():
                schema_string += f"Table: {table}\n"
                schema_string += "\n".join(columns) + "\n\n"
            return schema_string
    except Exception as e:
        return f"Error fetching schema: {str(e)}"

if __name__ == "__main__":
    print(get_dynamic_schema())
