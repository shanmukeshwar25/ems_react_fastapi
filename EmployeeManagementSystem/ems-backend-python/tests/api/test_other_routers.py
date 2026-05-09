from routers import other_routers


def test_audit_logs_success(client, monkeypatch, set_current_user, admin_user):
    set_current_user(admin_user)
    monkeypatch.setattr(other_routers.audit_service, "get_all_logs", lambda db, page, size: ([{"id": 1}], 1))
    monkeypatch.setattr(other_routers.audit_service, "to_dto", lambda item: item)

    response = client.get("/api/ems/audit/logs")

    assert response.status_code == 200
    assert response.json()["content"][0]["id"] == 1


def test_audit_log_search_success(client, monkeypatch, set_current_user, admin_user):
    set_current_user(admin_user)
    monkeypatch.setattr(
        other_routers.audit_service,
        "search_logs",
        lambda db, user_param, action, target, page, size: ([{"id": 2, "action": action}], 1),
    )
    monkeypatch.setattr(other_routers.audit_service, "to_dto", lambda item: item)

    response = client.get("/api/ems/audit/logs/search?user=EMP001&action=LOGIN&target=AUTH")

    assert response.status_code == 200
    assert response.json()["content"][0]["action"] == "LOGIN"


def test_audit_logs_by_user_success(client, monkeypatch, set_current_user, admin_user):
    set_current_user(admin_user)
    monkeypatch.setattr(
        other_routers.audit_service,
        "get_logs_by_user",
        lambda db, emp_id, page, size: ([{"id": 3, "user": emp_id}], 1),
    )
    monkeypatch.setattr(other_routers.audit_service, "to_dto", lambda item: item)

    response = client.get("/api/ems/audit/logs/user/EMP003")

    assert response.status_code == 200
    assert response.json()["content"][0]["user"] == "EMP003"


def test_db_config_success_for_manager(client, set_current_user, manager_user):
    set_current_user(manager_user)

    response = client.get("/api/ems/db-config")

    assert response.status_code == 200
    assert "host" in response.json()
    assert "database" in response.json()


def test_db_config_forbidden_for_employee(client, set_current_user, employee_user):
    set_current_user(employee_user)

    response = client.get("/api/ems/db-config")

    assert response.status_code == 403


def test_import_employees_success(client, monkeypatch, set_current_user, admin_user):
    set_current_user(admin_user)
    monkeypatch.setattr(
        other_routers.excel_import_service,
        "import_employees",
        lambda db, content, actor: {"imported": 2, "uploadedBy": actor, "size": len(content)},
    )

    response = client.post(
        "/api/ems/employees/import",
        files={"file": ("employees.xlsx", b"fake-excel-content", "application/vnd.ms-excel")},
    )

    assert response.status_code == 200
    assert response.json()["imported"] == 2
    assert response.json()["uploadedBy"] == "EMP001"
