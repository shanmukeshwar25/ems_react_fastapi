import pandas as pd

from chatbot import router as chatbot_router


class FakeConnection:
    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        return False


class FakeEngine:
    def connect(self):
        return FakeConnection()


def test_connect_success(client, monkeypatch):
    monkeypatch.setattr(chatbot_router, "_engine", lambda cfg=None: FakeEngine())
    monkeypatch.setattr(
        chatbot_router,
        "get_schema_preview",
        lambda engine: {
            "employees": [
                {"name": "emp_id", "type": "varchar", "nullable": False, "sensitive": False}
            ]
        },
    )

    response = client.post(
        "/api/chatbot/connect",
        json={"db": {"database": "EMSNew", "user": "postgres", "password": "1234"}},
    )

    assert response.status_code == 200
    assert response.json()["connected"] is True
    assert "employees" in response.json()["schema"]


def test_query_crud_intent_success(client, monkeypatch):
    monkeypatch.setattr(
        chatbot_router,
        "detect_crud_intent",
        lambda question: {"action": "add", "entity": "employee"},
    )

    response = client.post("/api/chatbot/query", json={"question": "add a new employee"})

    assert response.status_code == 200
    assert response.json()["action"] == "add"
    assert response.json()["entity"] == "employee"


def test_query_sql_dataframe_success(client, monkeypatch):
    monkeypatch.setattr(chatbot_router, "detect_crud_intent", lambda question: None)
    monkeypatch.setattr(chatbot_router, "_engine", lambda cfg=None: FakeEngine())
    monkeypatch.setattr(chatbot_router, "get_schema_preview", lambda engine: {"employees": []})
    monkeypatch.setattr(chatbot_router, "detect_chart_intent", lambda question: None)
    monkeypatch.setattr(chatbot_router, "get_sql_query_from_nl", lambda question, schema, db_type: "select 1")
    monkeypatch.setattr(
        chatbot_router,
        "run_query",
        lambda engine, sql, params=None: pd.DataFrame([{"count": 1}]),
    )

    response = client.post("/api/chatbot/query", json={"question": "how many employees?"})

    assert response.status_code == 200
    assert response.json()["sql"] == "select 1"
    assert response.json()["row_count"] == 1


def test_query_sql_generation_failure_returns_500(client, monkeypatch):
    monkeypatch.setattr(chatbot_router, "detect_crud_intent", lambda question: None)
    monkeypatch.setattr(chatbot_router, "_engine", lambda cfg=None: FakeEngine())
    monkeypatch.setattr(chatbot_router, "get_schema_preview", lambda engine: {"employees": []})
    monkeypatch.setattr(chatbot_router, "detect_chart_intent", lambda question: None)
    monkeypatch.setattr(chatbot_router, "get_sql_query_from_nl", lambda question, schema, db_type: None)

    response = client.post("/api/chatbot/query", json={"question": "how many employees?"})

    assert response.status_code == 500


def test_schema_success(client, monkeypatch):
    monkeypatch.setattr(chatbot_router, "_engine", lambda cfg=None: FakeEngine())
    monkeypatch.setattr(
        chatbot_router,
        "get_schema_preview",
        lambda engine: {"employees": [{"name": "emp_id", "type": "varchar", "nullable": False}]},
    )

    response = client.post(
        "/api/chatbot/schema",
        json={"db": {"database": "EMSNew", "user": "postgres", "password": "1234"}},
    )

    assert response.status_code == 200
    assert "employees" in response.json()


def test_add_record_success(client, monkeypatch):
    monkeypatch.setattr(chatbot_router, "_engine", lambda cfg=None: FakeEngine())
    monkeypatch.setattr(chatbot_router, "run_query", lambda engine, sql, params=None: "Inserted 1 row")

    response = client.post(
        "/api/chatbot/add",
        json={"table": "employee", "data": {"name": "Jane"}, "db": {"database": "EMSNew", "user": "postgres", "password": "1234"}},
    )

    assert response.status_code == 200
    assert response.json()["success"] is True


def test_add_record_without_valid_fields_returns_400(client, monkeypatch):
    monkeypatch.setattr(chatbot_router, "_engine", lambda cfg=None: FakeEngine())

    response = client.post(
        "/api/chatbot/add",
        json={"table": "employee", "data": {"secret_token": "bad"}, "db": {"database": "EMSNew", "user": "postgres", "password": "1234"}},
    )

    assert response.status_code == 400


def test_update_record_success(client, monkeypatch):
    monkeypatch.setattr(chatbot_router, "_engine", lambda cfg=None: FakeEngine())
    monkeypatch.setattr(chatbot_router, "run_query", lambda engine, sql, params=None: "Updated 1 row")

    response = client.put(
        "/api/chatbot/update",
        json={
            "table": "employee",
            "pk_col": "emp_id",
            "pk_value": "EMP100",
            "data": {"name": "Jane Doe"},
            "db": {"database": "EMSNew", "user": "postgres", "password": "1234"},
        },
    )

    assert response.status_code == 200
    assert response.json()["success"] is True


def test_update_record_without_updatable_fields_returns_400(client, monkeypatch):
    monkeypatch.setattr(chatbot_router, "_engine", lambda cfg=None: FakeEngine())

    response = client.put(
        "/api/chatbot/update",
        json={
            "table": "employee",
            "pk_col": "emp_id",
            "pk_value": "EMP100",
            "data": {"emp_id": "EMP100"},
            "db": {"database": "EMSNew", "user": "postgres", "password": "1234"},
        },
    )

    assert response.status_code == 400


def test_delete_record_success(client, monkeypatch):
    monkeypatch.setattr(chatbot_router, "_engine", lambda cfg=None: FakeEngine())
    monkeypatch.setattr(chatbot_router, "run_query", lambda engine, sql, params=None: "Deleted 1 row")

    response = client.request(
        "DELETE",
        "/api/chatbot/delete",
        json={
            "table": "employee",
            "pk_col": "emp_id",
            "pk_value": "EMP100",
            "db": {"database": "EMSNew", "user": "postgres", "password": "1234"},
        },
    )

    assert response.status_code == 200
    assert response.json()["success"] is True


def test_get_record_success(client, monkeypatch):
    monkeypatch.setattr(chatbot_router, "_engine", lambda cfg=None: FakeEngine())
    monkeypatch.setattr(
        chatbot_router,
        "get_record_by_id",
        lambda engine, table, pk_col, pk_value: ({"emp_id": pk_value, "name": "Jane"}, None),
    )

    response = client.post(
        "/api/chatbot/record",
        json={
            "table": "employee",
            "pk_col": "emp_id",
            "pk_value": "EMP100",
            "db": {"database": "EMSNew", "user": "postgres", "password": "1234"},
        },
    )

    assert response.status_code == 200
    assert response.json()["record"]["emp_id"] == "EMP100"


def test_get_record_not_found_returns_404(client, monkeypatch):
    monkeypatch.setattr(chatbot_router, "_engine", lambda cfg=None: FakeEngine())
    monkeypatch.setattr(chatbot_router, "get_record_by_id", lambda engine, table, pk_col, pk_value: (None, None))

    response = client.post(
        "/api/chatbot/record",
        json={
            "table": "employee",
            "pk_col": "emp_id",
            "pk_value": "EMP404",
            "db": {"database": "EMSNew", "user": "postgres", "password": "1234"},
        },
    )

    assert response.status_code == 404


def test_next_id_success(client, monkeypatch):
    monkeypatch.setattr(chatbot_router, "_engine", lambda cfg=None: FakeEngine())
    monkeypatch.setattr(chatbot_router, "get_next_id", lambda engine, table, id_col: "EMP101")

    response = client.post(
        "/api/chatbot/next-id",
        json={
            "table": "employee",
            "id_col": "emp_id",
            "db": {"database": "EMSNew", "user": "postgres", "password": "1234"},
        },
    )

    assert response.status_code == 200
    assert response.json()["next_id"] == "EMP101"


def test_get_primary_key_success(client, monkeypatch):
    monkeypatch.setattr(chatbot_router, "_engine", lambda cfg=None: FakeEngine())
    monkeypatch.setattr(chatbot_router, "get_primary_key_column", lambda engine, table: "emp_id")

    response = client.post(
        "/api/chatbot/pk",
        json={"table": "employee", "db": {"database": "EMSNew", "user": "postgres", "password": "1234"}},
    )

    assert response.status_code == 200
    assert response.json()["pk_col"] == "emp_id"


def test_get_primary_key_not_found_returns_404(client, monkeypatch):
    monkeypatch.setattr(chatbot_router, "_engine", lambda cfg=None: FakeEngine())
    monkeypatch.setattr(chatbot_router, "get_primary_key_column", lambda engine, table: None)

    response = client.post(
        "/api/chatbot/pk",
        json={"table": "employee", "db": {"database": "EMSNew", "user": "postgres", "password": "1234"}},
    )

    assert response.status_code == 404
