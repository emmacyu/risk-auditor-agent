from psycopg_pool import AsyncConnectionPool
from app.config import settings

# Read the DB connection from central config. Pydantic handles fail-fast validation.
DB_URI = settings.DATABASE_URL

# Create a global connection pool here, allowing concurrency and tying it into LangGraph state caching.
# Note: autocommit=True is strictly required by LangGraph PostgresSaver for parallel streaming writes.
connection_kwargs = {"autocommit": True, "prepare_threshold": 0}

pool = AsyncConnectionPool(
    conninfo=DB_URI,
    max_size=20,
    timeout=1.0,  # [Security]: If Docker fails to connect within 1s, throw an error to avoid infinite retry deadlocks.
    kwargs=connection_kwargs,
    open=False
)

def get_db_pool():
    """Singleton export to retrieve the underlying DB connection pool."""
    return pool
