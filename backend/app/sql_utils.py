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


_NON_TEXT_TYPE_KEYWORDS = ("INT", "FLOAT", "DOUBLE", "DECIMAL", "NUMERIC", "REAL",
                           "TIMESTAMP", "DATE", "TIME", "BOOLEAN", "BOOL", "INTERVAL", "BIT", "HUGEINT")


def _is_text_column(col_type: str) -> bool:
    """判断列是否文本类型 —— 用于全局搜索时只扫描文本列，跳过数值/时间列上的 CAST+ILIKE 全表扫描。"""
    t = (col_type or "").upper()
    if not t:
        # 类型未知时保守地保留，按文本处理
        return True
    return not any(k in t for k in _NON_TEXT_TYPE_KEYWORDS)


def _is_pure_varchar(col_type: str) -> bool:
    """是否已经是 VARCHAR/TEXT，可省去 CAST(... AS VARCHAR)。"""
    t = (col_type or "").upper()
    return t.startswith("VARCHAR") or t.startswith("TEXT") or t in ("STRING",)


def build_search_clause(columns, search_term, params):
    """Build a search clause across textual columns.

    优化：
    - 跳过数值 / 时间 / 布尔 列：这些列上 CAST(... AS VARCHAR) ILIKE '%x%' 几乎不会
      产生有意义的命中，却会强制对全表每行做一次 CAST + 字符串匹配，是大表搜索的主要瓶颈。
    - 对已经是 VARCHAR 的列省去 CAST，直接 ILIKE。
    """
    if not search_term:
        return "", params
    conditions = []
    pattern = f"%{search_term}%"
    for col in columns:
        col_type = col.get("type", "") if isinstance(col, dict) else ""
        if not _is_text_column(col_type):
            continue
        if _is_pure_varchar(col_type):
            conditions.append(f'"{col["name"]}" ILIKE ?')
        else:
            conditions.append(f'CAST("{col["name"]}" AS VARCHAR) ILIKE ?')
        params.append(pattern)
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
    """Build search clause with values inlined (for COPY statements). 同 build_search_clause 的优化。"""
    if not search_term:
        return ""
    conditions = []
    escaped = _escape_sql_value(f"%{search_term}%")
    for col in columns:
        col_type = col.get("type", "") if isinstance(col, dict) else ""
        if not _is_text_column(col_type):
            continue
        if _is_pure_varchar(col_type):
            conditions.append(f'"{col["name"]}" ILIKE {escaped}')
        else:
            conditions.append(f'CAST("{col["name"]}" AS VARCHAR) ILIKE {escaped}')
    if not conditions:
        return ""
    return "(" + " OR ".join(conditions) + ")"
