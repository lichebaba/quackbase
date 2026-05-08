import re

_TS_VAL_RE = re.compile(r"^\d{4}-\d{2}-\d{2}[ T]\d{2}:\d{2}")
_DATE_VAL_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")


def _detect_cast_type(col_type: str, val):
    """Return 'TIMESTAMP' / 'DATE' / None based on column metadata, with a value-format
    fallback when column type is missing or unrecognized."""
    t = (col_type or "").upper()
    # 列类型已知：兼容 TIMESTAMP / TIMESTAMP_NS / TIMESTAMP WITH TIME ZONE / DATETIME
    if "TIMESTAMP" in t or t.startswith("DATETIME"):
        return "TIMESTAMP"
    if t.startswith("DATE"):
        return "DATE"
    # 列类型未知时，看值的格式做兜底：避免 col_types 拿不到导致 SQL 缺 CAST 报类型错
    if isinstance(val, str):
        v = val.strip()
        if _TS_VAL_RE.match(v):
            return "TIMESTAMP"
        if _DATE_VAL_RE.match(v):
            return "DATE"
    return None


def _build_col_types(columns):
    """Build a column-name → type-upper dict, with strip() variants as fallback keys to
    tolerate stray whitespace / zero-width chars in column names."""
    col_types = {}
    if not columns:
        return col_types
    for c in columns:
        name = c["name"]
        t = c["type"].upper()
        col_types[name] = t
        if isinstance(name, str):
            stripped = name.strip()
            if stripped and stripped != name and stripped not in col_types:
                col_types[stripped] = t
    return col_types


def _lookup_col_type(col_types: dict, col: str) -> str:
    if col in col_types:
        return col_types[col]
    if isinstance(col, str):
        return col_types.get(col.strip(), "")
    return ""


def build_where(filter_list, params, columns=None):
    """Build WHERE clause using parametrized queries.

    columns: optional list of {"name": ..., "type": ...} from DESCRIBE,
    used to add proper CAST for DATE/TIMESTAMP columns to避免类型转换错误。
    """
    col_types = _build_col_types(columns)

    conditions = []
    for f in filter_list:
        col, op, val = f["col"], f["op"], f.get("val", "")
        col_type = _lookup_col_type(col_types, col)
        cast_type = _detect_cast_type(col_type, val)

        if op in ("=", "!=", ">", "<", ">=", "<="):
            if cast_type:
                conditions.append(f'"{col}" {op} CAST(? AS {cast_type})')
            else:
                conditions.append(f'"{col}" {op} ?')
            params.append(val)
        elif op == "LIKE":
            conditions.append(f'"{col}" LIKE ?')
            params.append(f"%{val}%")
        elif op == "IS NULL":
            conditions.append(f'"{col}" IS NULL')
        elif op == "IS NOT NULL":
            conditions.append(f'"{col}" IS NOT NULL')
    return ("WHERE " + " AND ".join(conditions)) if conditions else "", params


def build_search_clause(columns, search_term, params):
    """Build a search clause that searches across all VARCHAR columns."""
    if not search_term:
        return "", params
    conditions = []
    for col in columns:
        conditions.append(f'CAST("{col["name"]}" AS VARCHAR) ILIKE ?')
        params.append(f"%{search_term}%")
    if not conditions:
        return "", params
    return "(" + " OR ".join(conditions) + ")", params


def _escape_sql_value(val):
    """Escape a value for safe inline SQL (prevent SQL injection)."""
    if val is None:
        return "NULL"
    s = str(val).replace("'", "''")
    return f"'{s}'"


def build_where_inline(filter_list, columns=None):
    """Build WHERE clause with values inlined (for COPY/inline SQL statements)."""
    col_types = _build_col_types(columns)

    conditions = []
    for f in filter_list:
        col, op, val = f["col"], f["op"], f.get("val", "")
        col_type = _lookup_col_type(col_types, col)
        cast_type = _detect_cast_type(col_type, val)

        if op in ("=", "!=", ">", "<", ">=", "<="):
            if cast_type:
                conditions.append(
                    f'"{col}" {op} CAST({_escape_sql_value(val)} AS {cast_type})'
                )
            else:
                conditions.append(f'"{col}" {op} {_escape_sql_value(val)}')
        elif op == "LIKE":
            conditions.append(f'"{col}" LIKE {_escape_sql_value(f"%{val}%")}')
        elif op == "IS NULL":
            conditions.append(f'"{col}" IS NULL')
        elif op == "IS NOT NULL":
            conditions.append(f'"{col}" IS NOT NULL')
    return ("WHERE " + " AND ".join(conditions)) if conditions else ""


def build_search_clause_inline(columns, search_term):
    """Build search clause with values inlined (for COPY statements)."""
    if not search_term:
        return ""
    conditions = []
    escaped = _escape_sql_value(f"%{search_term}%")
    for col in columns:
        conditions.append(f'CAST("{col["name"]}" AS VARCHAR) ILIKE {escaped}')
    if not conditions:
        return ""
    return "(" + " OR ".join(conditions) + ")"
