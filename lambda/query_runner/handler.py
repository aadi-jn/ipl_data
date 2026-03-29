import json
import os
import re
import time

import boto3

WORKGROUP = os.environ["ATHENA_WORKGROUP"]
DATABASE = os.environ["ATHENA_DATABASE"]

athena = boto3.client("athena")

# Keywords that are never allowed at the start of a statement
_BLOCKED = re.compile(
    r"^\s*(INSERT|UPDATE|DELETE|DROP|CREATE|ALTER|TRUNCATE|EXEC(UTE)?|CALL|MERGE|REPLACE|LOAD)\b",
    re.IGNORECASE,
)
_IS_SELECT = re.compile(r"^\s*SELECT\b", re.IGNORECASE)
_HAS_LIMIT = re.compile(r"\bLIMIT\s+\d+", re.IGNORECASE)
_SEMICOLONS = re.compile(r";")


def _validate(sql: str) -> str | None:
    """Return an error string if sql is invalid, else None."""
    if _BLOCKED.search(sql):
        return "Only SELECT statements are allowed."
    if not _IS_SELECT.match(sql):
        return "Query must start with SELECT."
    if len(_SEMICOLONS.findall(sql)) > 1:
        return "Multiple statements are not allowed."
    return None


def _add_limit(sql: str) -> str:
    # Strip trailing semicolon before appending LIMIT
    sql = sql.rstrip().rstrip(";")
    if not _HAS_LIMIT.search(sql):
        sql = f"{sql} LIMIT 50"
    return sql


def _poll(query_id: str) -> dict:
    """Poll Athena until terminal state. Returns the execution dict."""
    delay = 1
    max_delay = 8
    deadline = time.time() + 55  # Lambda timeout is 60s

    while time.time() < deadline:
        resp = athena.get_query_execution(QueryExecutionId=query_id)
        execution = resp["QueryExecution"]
        state = execution["Status"]["State"]
        if state in ("SUCCEEDED", "FAILED", "CANCELLED"):
            return execution
        time.sleep(delay)
        delay = min(delay * 2, max_delay)

    # Timed out — try to cancel
    try:
        athena.stop_query_execution(QueryExecutionId=query_id)
    except Exception:
        pass
    return {"Status": {"State": "TIMED_OUT", "StateChangeReason": "Query exceeded the 55-second time limit."}}


def _fetch_results(query_id: str) -> tuple[list[str], list[list[str]]]:
    """Return (columns, rows) from a completed Athena query."""
    columns: list[str] = []
    rows: list[list[str]] = []

    paginator = athena.get_paginator("get_query_results")
    first_page = True
    for page in paginator.paginate(QueryExecutionId=query_id):
        result_rows = page["ResultSet"]["Rows"]
        if first_page:
            columns = [col.get("VarCharValue", "") for col in result_rows[0]["Data"]]
            result_rows = result_rows[1:]
            first_page = False
        for row in result_rows:
            rows.append([cell.get("VarCharValue", "") for cell in row["Data"]])

    return columns, rows


def _respond(status_code: int, body: dict) -> dict:
    return {
        "statusCode": status_code,
        "headers": {
            "Content-Type": "application/json",
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Headers": "Content-Type",
            "Access-Control-Allow-Methods": "POST,OPTIONS",
        },
        "body": json.dumps(body),
    }


def handler(event, context):
    # Handle preflight
    if event.get("httpMethod") == "OPTIONS":
        return _respond(200, {})

    # Parse body
    try:
        body = json.loads(event.get("body") or "{}")
    except json.JSONDecodeError:
        return _respond(400, {"error": "Invalid JSON in request body."})

    sql = body.get("query", "").strip()
    if not sql:
        return _respond(400, {"error": "Missing required field: query."})

    # Validate
    err = _validate(sql)
    if err:
        return _respond(400, {"error": err})

    # Add LIMIT if missing
    sql = _add_limit(sql)

    # Start query
    try:
        start_resp = athena.start_query_execution(
            QueryString=sql,
            QueryExecutionContext={"Database": DATABASE},
            WorkGroup=WORKGROUP,
        )
    except Exception as e:
        return _respond(500, {"error": f"Failed to start query: {str(e)}"})

    query_id = start_resp["QueryExecutionId"]

    # Poll
    execution = _poll(query_id)
    state = execution["Status"]["State"]

    if state == "TIMED_OUT":
        return _respond(504, {"error": execution["Status"]["StateChangeReason"]})

    if state in ("FAILED", "CANCELLED"):
        reason = execution["Status"].get("StateChangeReason", "Query failed.")
        return _respond(400, {"error": reason})

    # Fetch results
    columns, rows = _fetch_results(query_id)

    if not rows:
        return _respond(200, {"columns": columns, "data": [], "row_count": 0, "query": sql, "message": "Query returned no results."})

    return _respond(200, {
        "columns": columns,
        "data": rows,
        "row_count": len(rows),
        "query": sql,
    })
