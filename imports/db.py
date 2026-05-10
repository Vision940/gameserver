import atexit
import os

from contextlib import contextmanager

from psycopg.rows import dict_row
from psycopg_pool import ConnectionPool

_pool = None


def get_database_url():
    db_url = os.environ.get("DATABASE_URL")
    if not db_url:
        raise EnvironmentError("DATABASE_URL is not set in env")
    return db_url


def init_pool():
    global _pool
    if _pool is not None:
        return _pool

    _pool = ConnectionPool(
        conninfo=get_database_url(),
        min_size=1,
        max_size=10,
        kwargs={"row_factory": dict_row},
    )

    atexit.register(close_pool)
    return _pool


def close_pool():
    global _pool
    if _pool is not None:
        _pool.close()
        _pool = None


def get_pool():
    if _pool is None:
        return init_pool()
    return _pool


@contextmanager
def db_connection():
    """
    Function to yield a db connection
    """

    pool = get_pool()
    with pool.connection() as conn:
        try:
            yield conn
            conn.commit()
        except Exception:
            conn.rollback()
            raise


@contextmanager
def db_cursor():
    """
    Function to yield a single db cursor for when operations need multiple steps
    Implementations should use `with db.db_cursor() as cursor:` and call fetch
        commands with cursor=cursor passed in
    """

    with db_connection() as conn:
        with conn.cursor() as cur:
            yield cur


def _execute_on_cursor(query, params, fetch, cur):
    """
    Execute query on provided cursor
    Only directly called by execute function
    """

    cur.execute(query, params or {})

    match fetch:
        case "all":
            return list(cur.fetchall()) if cur.description is not None else []
        case "one":
            return cur.fetchone() if cur.description is not None else None
        case "smart":
            if cur.description is None: return None
            rows = list(cur.fetchall())
            if not rows: return None
            if len(rows) == 1: return rows[0]
            return rows
        case None:
            return None
        case _:
            raise ValueError(f"Invalid fetch mode to db execute: {fetch}")

def execute(query, params=None, fetch="smart", cursor=None):
    """
    Function to execute db queries
    Will get cursor automatically if not passed in

    fetch="all" will return a list with rows
    fetch="one" will return a single row dict
    fetch=None will return None
    fetch="smart" will dynamically choose the fetch type and return appropriately
    """

    if cursor:
        return _execute_on_cursor(query, params, fetch, cursor)

    with db_cursor() as cur:
        return _execute_on_cursor(query, params, fetch, cur)


def fetch_col(query, params=None, col="id", cursor=None):
    """
    Function to execute a statement and get a value from returned row
    Uses optional col input as key name if the returned row has multiple columns
    """

    row = execute(query, params, fetch="one", cursor=cursor)
    if not row: return None
    if len(row) == 1:
        return next(iter(row.values()))
    if col not in row:
        raise KeyError(f"Column {col!r} not found in returned row")
    return row[col]


def fetch_row(query, params=None, cursor=None):
    """
    Function to execute statement and return a single row
    """

    return execute(query, params, fetch="one", cursor=cursor)


def fetch_rows(query, params=None, cursor=None):
    """
    Function to execute a statement and return all resulting rows
    """

    return execute(query, params, fetch="all", cursor=cursor)

