def build_where(filter_list, params, columns=None):
    """Build WHERE clause using parametrized queries.

    columns: optional list of {"name": ..., "type": ...} from DESCRIBE,
    used to add proper CAST for DATE/TIMESTAMP columns to避免类型转换错误。
    """
    col_types = {}
    if columns:
        col_types = {c["name"]: c["type"].upper() for c in columns}

    conditions = []
    for f in filter_list:
        col, op, val = f["col"], f["op"], f.get("val", "")
        col_type = col_types.get(col, "")
        is_date = col_type.startswith("DATE")
        is_ts = col_type.startswith("TIMESTAMP")

        if op in ("=", "!=", ">", "<", ">=", "<="):
            if is_ts or is_date:
                # 显式按列类型做 CAST，避免字符串比较导致的转换错误
                cast_type = "TIMESTAMP" if is_ts else "DATE"
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
    col_types = {}
    if columns:
        col_types = {c["name"]: c["type"].upper() for c in columns}

    conditions = []
    for f in filter_list:
        col, op, val = f["col"], f["op"], f.get("val", "")
        col_type = col_types.get(col, "")
        is_date = col_type.startswith("DATE")
        is_ts = col_type.startswith("TIMESTAMP")
        cast_type = "TIMESTAMP" if is_ts else "DATE" if is_date else None

        if op in ("=", "!=", ">", "<", ">=", "<="):
            if cast_type:
                conditions.append(
                    f'"{col}" {op} CAST({_escape_sql_value(val)} AS {cast_type})'
                )
            else:
                conditions.append(f'"{col}" {op} {_escape_sql_value(val)}')
        elif op == "LIKE":
            conditions.append(f'"{col}" LIKE {_escape_sql_value(f"%{val}%")})')
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
