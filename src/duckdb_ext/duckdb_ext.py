import os

import duckdb

EXTENSION_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "extensions")


def get_extension_dir() -> str:
    """Get the directory where the DuckDB extension files are located.

    Returns:
        str: The path to the directory containing the DuckDB extension files.
    """
    return EXTENSION_DIR


def init(con: duckdb.DuckDBPyConnection) -> duckdb.DuckDBPyConnection:
    """initialise a DuckDB connection to use the duckdb-ext extensions.

    This function sets the extension directory for the connection to the directory
    where the duckdb-ext extension files are located. It also disables automatic
    installation of known extensions.

    Args:
        con (duckdb.DuckDBPyConnection): The DuckDB connection to initialise.
    """

    con.execute("SET extension_directory = ?;", (get_extension_dir(),))
    con.execute("SET autoinstall_known_extensions = false;")
    return con
