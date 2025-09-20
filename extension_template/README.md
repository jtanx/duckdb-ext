# DuckDB extensions via PIP

## Installaton

```
pip install duckdb-ext[{ext_name}]
```

## Usage

## Option 1: Automatic

```python
import duckdb
import duckdb_ext

with duckdb_ext.init(duckdb.connect()) as con:
    ...
```

## Option 2: Manual

```python
import duckdb
import duckdb_ext

with duckdb.connect() as con:
    con.execute("SET extension_directory = ?;", (get_extension_dir(),))
    # Ideally also:
    con.execute("SET autoinstall_known_extensions = false;")
```
