from services.sql_config import METRIC_CONFIG

def build_sql(metric, user_ids=None, date_range=None, filters=None):
    config = METRIC_CONFIG.get(metric)

    if not config:
        raise ValueError(f"Unsupported metric: {metric}")

    table = config["table"]
    alias = config["alias"]
    date_column = config.get("date_column")

    # 🔥 SELECT clause
    if config.get("aggregation") == "SUM":
        cols = f"SUM({alias}.{config['aggregation_column']}) as total_value"

    elif "columns" in config:
        cols = ", ".join([f"{alias}.{c}" for c in config["columns"]])

    elif "column" in config:
        cols = f"{alias}.{config['column']}"

    else:
        raise ValueError(f"No column defined for metric: {metric}")

    sql = f"""
    SELECT u.name, {cols}
    FROM api_users_hrdb u
    """

    # 🔥 JOIN
    if table != "api_users_hrdb":
        sql += f"""
        JOIN {table} {alias} ON u.id = {alias}.user_id
        """

    sql += " WHERE 1=1 "

    # 🔥 User filter
    if user_ids:
        ids = ",".join(map(str, user_ids))
        sql += f" AND u.id IN ({ids}) "

    # 🔥 Date filter (fixed)
    if date_range:
        start, end = date_range

        if config.get("type") == "range":
            sql += f"""
            AND (
                {alias}.start_date <= '{end}'
                AND {alias}.end_date >= '{start}'
            )
            """
        elif date_column and start and end:
            sql += f" AND {alias}.{date_column} BETWEEN '{start}' AND '{end}' "
        elif date_column and not start and end:
            sql += f" AND {alias}.{date_column} <= '{end}' "
        elif date_column and start and not end:
            sql += f" AND {alias}.{date_column} >= '{start}' "

    # 🔥 Filters
    if filters:
        for key, value in filters.items():

            if key == "status" and value == "active":
                sql += " AND u.status = 1 "

            elif key == "name_like":
                sql += f" AND u.name LIKE '%{value}%' "

    return sql.strip()

def build_sql11(metric, user_ids=None, date_range=None, filters=None):
    config = METRIC_CONFIG.get(metric)

    if not config:
        raise ValueError(f"Unsupported metric: {metric}")

    table = config["table"]
    alias = config["alias"]
    # column = config["column"]
    date_column = config["date_column"]

    # 🔥 Handle multiple columns OR single column

    if "columns" in config:
        cols = ", ".join([f"{alias}.{c}" for c in config["columns"]])
    elif config.get("aggregation") == "SUM":
        cols = f"SUM({alias}.{config['aggregation_column']}) as total_value"
    else:
        cols = f"{alias}.{config['column']}"

    # Base query
    sql = f"""
    SELECT u.name, {cols}
    FROM api_users_hrdb u
    """

    # Join if needed
    if table != "api_users_hrdb":
        sql += f"""
        JOIN {table} {alias} ON u.id = {alias}.user_id
        """

    # WHERE clause
    sql += " WHERE 1=1 "

    # User filter
    if user_ids:
        ids = ",".join(map(str, user_ids))
        sql += f" AND u.id IN ({ids}) "

    # Date filter
    if date_range and date_column:
        start, end = date_range
        if start and end:
            sql += f" AND {alias}.{date_column} BETWEEN '{start}' AND '{end}' "

    if date_range and config.get("type") == "range":
        start, end = date_range

        sql += f"""
        AND (
            {alias}.start_date <= '{end}'
            AND {alias}.end_date >= '{start}'
        )
        """

    # Extra filters
    if filters:
        for f in filters:
            sql += f" AND {f} "

    return sql.strip()