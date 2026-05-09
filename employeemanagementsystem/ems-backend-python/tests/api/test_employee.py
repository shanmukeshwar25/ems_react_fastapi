from routers import employee_router


def test_create_employee_success(client, monkeypatch, set_current_user, admin_user):
    set_current_user(admin_user)

    monkeypatch.setattr(
        employee_router.employee_service,
        "create_employee",
        lambda db, payload, actor: {"empId": "EMP100", **payload, "createdBy": actor},
    )

    response = client.post(
        "/api/ems/employee",
        json={
            "name": "Jane Doe",
            "companyEmail": "jane@company.com",
            "department": "Engineering",
            "roles": ["EMPLOYEE"],
        },
    )

    assert response.status_code == 200
    assert response.json()["empId"] == "EMP100"
    assert response.json()["createdBy"] == "EMP001"


def test_create_employee_forbidden_for_non_admin(
    client, set_current_user, employee_user
):
    set_current_user(employee_user)

    response = client.post(
        "/api/ems/employee",
        json={
            "name": "Jane Doe",
            "companyEmail": "jane@company.com",
            "roles": ["EMPLOYEE"],
        },
    )

    assert response.status_code == 403


def test_my_profile_success(client, monkeypatch, set_current_user, employee_user):
    set_current_user(employee_user)
    monkeypatch.setattr(
        employee_router.employee_service,
        "get_employee_by_id",
        lambda db, emp_id: {"empId": emp_id, "name": "Employee User"},
    )

    response = client.get("/api/ems/profile")

    assert response.status_code == 200
    assert response.json() == {"empId": "EMP003", "name": "Employee User"}


def test_get_employee_by_id_success_for_manager(
    client, monkeypatch, set_current_user, manager_user
):
    set_current_user(manager_user)
    monkeypatch.setattr(
        employee_router.employee_service,
        "get_employee_by_id",
        lambda db, emp_id: {"empId": emp_id, "name": "Jane Doe"},
    )

    response = client.get("/api/ems/employee/EMP100")

    assert response.status_code == 200
    assert response.json()["empId"] == "EMP100"


def test_search_employees_success(client, monkeypatch, set_current_user, manager_user):
    set_current_user(manager_user)

    def fake_get_employees(db, name, department, date_param, skill, page, size):
        assert name == "Jane"
        assert department == "Engineering"
        assert date_param.isoformat() == "2024-01-01"
        assert skill == "Python"
        assert page == 0
        assert size == 10
        return ([{"empId": "EMP100", "name": "Jane Doe"}], 1)

    monkeypatch.setattr(employee_router.employee_service, "get_employees", fake_get_employees)

    response = client.get(
        "/api/ems/employees?name=Jane&department=Engineering&date=2024-01-01&skill=Python"
    )

    assert response.status_code == 200
    assert response.json()["content"][0]["empId"] == "EMP100"
    assert response.json()["totalElements"] == 1


def test_search_employees_invalid_date_returns_400(
    client, set_current_user, manager_user
):
    set_current_user(manager_user)

    response = client.get("/api/ems/employees?date=bad-date")

    assert response.status_code == 400


def test_inactive_employees_success(client, monkeypatch, set_current_user, manager_user):
    set_current_user(manager_user)
    monkeypatch.setattr(
        employee_router.employee_service,
        "get_inactive_employees",
        lambda db, page, size: ([{"empId": "EMP404"}], 1),
    )

    response = client.get("/api/ems/employees/inactive")

    assert response.status_code == 200
    assert response.json()["content"][0]["empId"] == "EMP404"


def test_get_inactive_employee_by_id_success(
    client, monkeypatch, set_current_user, manager_user
):
    set_current_user(manager_user)
    monkeypatch.setattr(
        employee_router.employee_service,
        "get_inactive_employee_by_id",
        lambda db, emp_id: {"empId": emp_id, "active": False},
    )

    response = client.get("/api/ems/employee/inactive/EMP404")

    assert response.status_code == 200
    assert response.json()["active"] is False


def test_deactivate_employee_success(client, monkeypatch, set_current_user, admin_user):
    set_current_user(admin_user)
    called = {}

    def fake_delete_employee(db, emp_id, actor):
        called["args"] = (emp_id, actor)

    monkeypatch.setattr(employee_router.employee_service, "delete_employee", fake_delete_employee)

    response = client.delete("/api/ems/employee/EMP100")

    assert response.status_code == 200
    assert response.json() == {"message": "Employee EMP100 deactivated"}
    assert called["args"] == ("EMP100", "EMP001")


def test_update_employee_success(client, monkeypatch, set_current_user, employee_user):
    set_current_user(employee_user)
    monkeypatch.setattr(
        employee_router.employee_service,
        "update_fields",
        lambda db, emp_id, payload, actor: {"empId": emp_id, **payload, "updatedBy": actor},
    )

    response = client.patch("/api/ems/update/EMP003", json={"phoneNumber": "1234567890"})

    assert response.status_code == 200
    assert response.json()["updatedBy"] == "EMP003"
    assert response.json()["phoneNumber"] == "1234567890"


def test_update_profile_image_success(client, monkeypatch, set_current_user, employee_user):
    set_current_user(employee_user)
    monkeypatch.setattr(
        employee_router.employee_service,
        "update_profile_image",
        lambda db, emp_id, image: {"empId": emp_id, "profileImage": image},
    )

    response = client.put(
        "/api/ems/profile/image",
        json={"profileImage": "https://cdn.example.com/avatar.png"},
    )

    assert response.status_code == 200
    assert response.json()["profileImage"].endswith("avatar.png")
