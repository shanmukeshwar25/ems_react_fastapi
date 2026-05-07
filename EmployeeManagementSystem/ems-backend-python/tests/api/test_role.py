from routers import role_router


def test_assign_role_success(client, monkeypatch, set_current_user, admin_user):
    set_current_user(admin_user)
    called = {}

    def fake_assign_role(db, emp_id, role, actor):
        called["args"] = (emp_id, role, actor)

    monkeypatch.setattr(role_router.role_service, "assign_role", fake_assign_role)

    response = client.post("/api/ems/assign/EMP100", json={"role": "MANAGER"})

    assert response.status_code == 200
    assert response.json() == {"message": "Role MANAGER assigned to EMP100"}
    assert called["args"] == ("EMP100", "MANAGER", "EMP001")


def test_assign_role_forbidden_for_employee(client, set_current_user, employee_user):
    set_current_user(employee_user)

    response = client.post("/api/ems/assign/EMP100", json={"role": "MANAGER"})

    assert response.status_code == 403


def test_remove_role_success(client, monkeypatch, set_current_user, admin_user):
    set_current_user(admin_user)
    monkeypatch.setattr(role_router.role_service, "remove_role", lambda db, emp_id, role, actor: None)

    response = client.post("/api/ems/remove/EMP100", json={"role": "MANAGER"})

    assert response.status_code == 200
    assert response.json() == {"message": "Role MANAGER removed from EMP100"}


def test_get_roles_success(client, monkeypatch, set_current_user, admin_user):
    set_current_user(admin_user)
    monkeypatch.setattr(role_router.role_service, "get_roles", lambda db, emp_id: ["EMPLOYEE", "MANAGER"])

    response = client.get("/api/ems/roles/EMP100")

    assert response.status_code == 200
    assert response.json() == ["EMPLOYEE", "MANAGER"]
