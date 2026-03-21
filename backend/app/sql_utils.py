def build_where(filter_list, params):
    conditions = []
    for f in filter_list:
        col, op, val = f["col"], f["op"], f.get("val", "")
        if op in ("=", "!=", ">", "<", ">=", "<="):
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


def build_where_inline(filter_list):
    """Build WHERE clause with values inlined (for COPY statements that don't support params)."""
    conditions = []
    for f in filter_list:
        col, op, val = f["col"], f["op"], f.get("val", "")
        if op in ("=", "!=", ">", "<", ">=", "<="):
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
