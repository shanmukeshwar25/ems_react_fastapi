"""Chatbot router — merged from ems-chatbot/routers/chatbot.py with adjusted imports."""

from __future__ import annotations
import os, traceback
from typing import Any, Optional
from urllib.parse import urlparse
import pandas as pd
from dotenv import load_dotenv
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from sqlalchemy import create_engine

from core.config import settings
from chatbot.db_utils import (AUTO_FIELDS, SENSITIVE_KEYWORDS, get_next_id,
                               get_primary_key_column, get_record_by_id,
                               get_schema_preview, run_query)
import re
from chatbot.llm_utils import detect_chart_intent, detect_crud_intent, get_sql_query_from_nl, PG_ENUM_COLUMNS

load_dotenv()
router = APIRouter()

# Collect all ENUM column names across all tables so we can safety-fix any ILIKE the LLM generates
_ALL_ENUM_COLS: set[str] = {col for col in PG_ENUM_COLUMNS}


def _fix_enum_ilike(sql: str) -> str:
    """Replace `col ILIKE 'x'` with `CAST(col AS TEXT) ILIKE 'x'` for known ENUM columns."""
    for col in _ALL_ENUM_COLS:
        # matches: col ILIKE 'val'  or  alias.col ILIKE 'val'  (case-insensitive)
        pattern = rf'(?<![\w.])([\w]+\.)?({re.escape(col)})\s+ILIKE\s+'
        replacement = rf'\1CAST(\2 AS TEXT) ILIKE '
        sql = re.sub(pattern, replacement, sql, flags=re.IGNORECASE)
    return sql


class DBConfig(BaseModel):
    db_type: str = "postgres"; host: str = "localhost"; port: int = 5432
    database: str; user: str; password: str

def _default_db() -> DBConfig:
    # 1. Try parsing settings.database_url or environment DATABASE_URL first
    db_url = settings.database_url or os.getenv("DATABASE_URL")
    if db_url:
        try:
            clean_url = db_url
            if clean_url.startswith("postgresql+psycopg2://"):
                clean_url = clean_url.replace("postgresql+psycopg2://", "postgresql://", 1)
            elif clean_url.startswith("postgres://"):
                clean_url = clean_url.replace("postgres://", "postgresql://", 1)
            
            parsed = urlparse(clean_url)
            db_type = "postgres" if parsed.scheme == "postgresql" else parsed.scheme
            
            return DBConfig(
                db_type=db_type,
                host=parsed.hostname or "localhost",
                port=parsed.port or 5432,
                database=parsed.path.lstrip("/"),
                user=parsed.username or "postgres",
                password=parsed.password or ""
            )
        except Exception as e:
            traceback.print_exc()

    # 2. Otherwise fallback to individual env vars
    return DBConfig(db_type=os.getenv("DB_TYPE","postgres"), host=os.getenv("DB_HOST","localhost"),
                    port=int(os.getenv("DB_PORT","5432")), database=os.getenv("DB_NAME","EMSNew"),
                    user=os.getenv("DB_USER","postgres"), password=os.getenv("DB_PASSWORD","1234"))

class ConnectRequest(BaseModel): db: Optional[DBConfig] = None
class QueryRequest(BaseModel): question: str; db: Optional[DBConfig] = None
class AddRequest(BaseModel): table: str; data: dict[str, Any]; db: Optional[DBConfig] = None
class UpdateRequest(BaseModel): table: str; pk_col: str; pk_value: Any; data: dict[str, Any]; db: Optional[DBConfig] = None
class DeleteRequest(BaseModel): table: str; pk_col: str; pk_value: Any; db: Optional[DBConfig] = None
class RecordRequest(BaseModel): table: str; pk_col: str; pk_value: Any; db: Optional[DBConfig] = None
class NextIdRequest(BaseModel): table: str; id_col: str; db: Optional[DBConfig] = None
class PKRequest(BaseModel): table: str; db: Optional[DBConfig] = None

def _engine(cfg=None):
    db = cfg or _default_db()
    url = f"postgresql+psycopg2://{db.user}:{db.password}@{db.host}:{db.port}/{db.database}" if db.db_type == "postgres" else f"mysql+pymysql://{db.user}:{db.password}@{db.host}:{db.port}/{db.database}" if db.db_type == "mysql" else f"sqlite:///{db.database}"
    return create_engine(url)

def _resolve_db(cfg): return cfg or _default_db()
def _safe_schema(schema): return {t: [{"name":c["name"],"type":c["type"],"nullable":c["nullable"],"sensitive":c.get("sensitive",False)} for c in cols] for t,cols in schema.items()}

# ── EMS navigation hints used in friendly error messages ─────────────────────
_EMS_HINTS: list[tuple[list[str], str]] = [
    (["leave", "leaves", "annual", "sick", "casual", "maternity", "paternity"],
     "📋 Go to **Leave Management** in the sidebar to view, apply, or manage leave requests."),
    (["attendance", "present", "absent", "late", "work from home", "wfh"],
     "📅 Go to **Attendance** in the sidebar to view and filter attendance records."),
    (["employee", "staff", "department", "designation", "joining", "salary"],
     "👤 Go to **Employees** in the sidebar to browse and filter employee data."),
    (["timesheet", "hours", "work hours", "task", "project"],
     "⏱ Go to **Timesheets** in the sidebar to view timesheet entries."),
    (["holiday", "calendar", "public holiday", "weekend"],
     "🗓 Go to **Holiday Calendar** in the sidebar to view holidays and non-working days."),
    (["audit", "log", "activity", "history"],
     "🔍 Go to **Audit Logs** (Admin panel) to review activity history."),
    (["role", "permission", "admin", "manager"],
     "⚙️ Go to **Roles & Permissions** in the Admin section to manage user roles."),
]


def _friendly_error(question: str, raw_result: str) -> str:
    """Convert a raw ❌ SQL Error or ⚠️ Security Block into a helpful user-facing message."""
    q = question.lower()

    if raw_result.startswith("⚠️"):
        # Security block (DROP / TRUNCATE)
        hints = [
            "🔒 Destructive database operations (DROP, TRUNCATE, DELETE all rows) are disabled for safety.",
            "If you need to delete specific records, please use the relevant form in the EMS dashboard:",
            "  • To cancel a leave → Leave Management → select request → Cancel",
            "  • To remove an employee → Employees → select employee → Deactivate / Delete",
            "  • To delete a timesheet → Timesheets → select entry → Delete",
        ]
        return "\n".join(hints)

    # SQL execution error — build contextual navigation hints
    nav = [h for kws, h in _EMS_HINTS if any(kw in q for kw in kws)]
    if not nav:
        nav = ["🏠 Navigate to the relevant section in the EMS sidebar to find the information you need."]

    lines = [
        "I wasn't able to run that query directly. Here's how you can get this information:",
        "",
    ] + nav + [
        "",
        "💡 *Tip: Try rephrasing your question — e.g. \"Show me all employees\" or \"List pending leaves\".*",
    ]
    return "\n".join(lines)


@router.post("/connect")
def connect(req: ConnectRequest):
    try:
        db = _resolve_db(req.db); engine = _engine(db)
        with engine.connect(): pass
        return {"connected":True,"db_type":db.db_type,"database":db.database,"schema":_safe_schema(get_schema_preview(engine))}
    except Exception as exc: raise HTTPException(400, f"Connection failed: {exc}")

@router.post("/query")
def nl_query(req: QueryRequest):
    try:
        crud = detect_crud_intent(req.question)
        if crud:
            labels = {"add":{"employee":"Add Employee","leave":"Apply Leave","attendance":"Mark Attendance","timesheet":"Add Timesheet","user":"Add User","role":"Add Role","holiday":"Add Holiday"},"update":{"employee":"Edit Employee","leave":"Edit Leave","attendance":"Edit Attendance","timesheet":"Edit Timesheet"},"delete":{"employee":"Delete Employee","leave":"Cancel Leave","attendance":"Delete Attendance","timesheet":"Delete Timesheet"}}
            label = labels.get(crud["action"],{}).get(crud["entity"],f"{crud['action']} {crud['entity']}")
            return {"sql":None,"columns":[],"rows":[],"row_count":0,"chart_type":None,"message":f"Opening the {label} form for you.","action":crud["action"],"entity":crud["entity"],"label":label}
        db = _resolve_db(req.db); engine = _engine(db); schema = get_schema_preview(engine)
        chart_meta = detect_chart_intent(req.question)
        sql_q = chart_meta["sql_prompt"] if chart_meta else req.question
        sql = get_sql_query_from_nl(sql_q, schema, db.db_type)
        if not sql:
            raise HTTPException(500, "Could not generate a valid SQL query. Check the Groq API key and backend logs.")
        # Safety-net: rewrite any ILIKE on ENUM columns to CAST(...AS TEXT) ILIKE
        if db.db_type == "postgres":
            sql = _fix_enum_ilike(sql)
        result = run_query(engine, sql)
        if isinstance(result, pd.DataFrame):
            # Replace NaN / inf / -inf (from NULL DB columns) with None so JSON serialisation never fails
            safe_df = result.where(pd.notna(result), other=None)
            rows = [{k: (None if isinstance(v, float) and (v != v or v == float("inf") or v == float("-inf")) else v)
                     for k, v in row.items()} for row in safe_df.to_dict(orient="records")]
            return {"sql":sql,"columns":list(result.columns),"rows":rows,"row_count":len(result),"chart_type":chart_meta["chart_type"] if chart_meta else None,"message":None,"action":None,"entity":None,"label":None}
        # run_query returns a plain string for errors / security blocks
        if isinstance(result, str) and (result.startswith("❌") or result.startswith("⚠️")):
            friendly = _friendly_error(req.question, result)
            return {"sql":sql,"columns":[],"rows":[],"row_count":0,"chart_type":None,"message":friendly,"action":None,"entity":None,"label":None,"error":True}
        return {"sql":sql,"columns":[],"rows":[],"row_count":0,"chart_type":None,"message":result,"action":None,"entity":None,"label":None}
    except HTTPException: raise
    except Exception as exc:
        traceback.print_exc()
        friendly = _friendly_error(req.question, f"❌ {exc}")
        return {"sql":None,"columns":[],"rows":[],"row_count":0,"chart_type":None,"message":friendly,"action":None,"entity":None,"label":None,"error":True}

@router.post("/schema")
def get_schema(req: ConnectRequest):
    try: return _safe_schema(get_schema_preview(_engine(req.db)))
    except Exception as exc: raise HTTPException(500, str(exc))

@router.post("/add")
def add_record(req: AddRequest):
    try:
        engine = _engine(req.db)
        safe_data = {k:v for k,v in req.data.items() if not any(kw in k.lower() for kw in SENSITIVE_KEYWORDS) or k.lower() in ["password"]}
        if not safe_data: raise HTTPException(400, "No valid fields.")
        cols = ", ".join(safe_data.keys()); params = ", ".join([f":{k}" for k in safe_data.keys()])
        result = run_query(engine, f"INSERT INTO {req.table} ({cols}) VALUES ({params})", params=safe_data)
        if "❌" in result: raise HTTPException(400, result)
        return {"success":True,"message":result,"table":req.table}
    except HTTPException: raise
    except Exception as exc: raise HTTPException(500, str(exc))

@router.put("/update")
def update_record(req: UpdateRequest):
    try:
        engine = _engine(req.db)
        readonly = set(AUTO_FIELDS) | {req.pk_col.lower()}
        data = {k:v for k,v in req.data.items() if k.lower() not in readonly}
        if not data: raise HTTPException(400, "No updatable fields.")
        set_c = ", ".join([f"{k} = :{k}" for k in data.keys()]); data["__pk__"] = req.pk_value
        result = run_query(engine, f"UPDATE {req.table} SET {set_c} WHERE {req.pk_col} = :__pk__", params=data)
        if "❌" in result: raise HTTPException(400, result)
        return {"success":True,"message":result,"table":req.table,"pk":req.pk_value}
    except HTTPException: raise
    except Exception as exc: raise HTTPException(500, str(exc))

@router.delete("/delete")
def delete_record(req: DeleteRequest):
    try:
        engine = _engine(req.db)
        result = run_query(engine, f"DELETE FROM {req.table} WHERE {req.pk_col} = :pk", params={"pk":req.pk_value})
        if "❌" in result: raise HTTPException(400, result)
        return {"success":True,"message":result,"table":req.table,"pk":req.pk_value}
    except HTTPException: raise
    except Exception as exc: raise HTTPException(500, str(exc))

@router.post("/record")
def get_record(req: RecordRequest):
    try:
        record, err = get_record_by_id(_engine(req.db), req.table, req.pk_col, req.pk_value)
        if err: raise HTTPException(500, err)
        if not record: raise HTTPException(404, f"No record found where {req.pk_col} = '{req.pk_value}'")
        safe = {k:v for k,v in record.items() if not any(kw in k.lower() for kw in SENSITIVE_KEYWORDS)}
        return {"record":safe,"table":req.table,"pk_col":req.pk_col}
    except HTTPException: raise
    except Exception as exc: raise HTTPException(500, str(exc))

@router.post("/next-id")
def next_id(req: NextIdRequest):
    try: return {"next_id":get_next_id(_engine(req.db), req.table, req.id_col),"table":req.table,"id_col":req.id_col}
    except Exception as exc: raise HTTPException(500, str(exc))

@router.post("/pk")
def get_pk(req: PKRequest):
    try:
        pk = get_primary_key_column(_engine(req.db), req.table)
        if not pk: raise HTTPException(404, f"No PK found for table '{req.table}'")
        return {"table":req.table,"pk_col":pk}
    except HTTPException: raise
    except Exception as exc: raise HTTPException(500, str(exc))
