# duckdb-ext

![PyPI Version](https://img.shields.io/pypi/v/duckdb-ext)

This package provides pip installable DuckDB extensions.

## Installation

Change the extras to match which extensions you wish to install e.g.:

```
pip install duckdb-ext[httpfs,delta,s3]
```

## Usage

### Option 1: Automatic

```python
import duckdb
import duckdb_ext

with duckdb_ext.init(duckdb.connect()) as con:
    ...
```

### Option 2: Manual

```python
import duckdb
import duckdb_ext

with duckdb.connect() as con:
    con.execute("SET extension_directory = ?;", (duckdb_ext.get_extension_dir(),))
    # Ideally also:
    con.execute("SET autoinstall_known_extensions = false;")
```