from routers import leave_router


def test_submit_leave_success(client, monkeypatch, set_current_user, employee_user):
    set_current_user(employee_user)
    monkeypatch.setattr(
        leave_router.leave_service,
        "submit_leave",
        lambda db, emp_id, payload: {"empId": emp_id, "status": "PENDING", **payload},
    )

    response = client.post(
        "/api/ems/leaves/",
        json={
            "leaveType": "ANNUAL",
            "startDate": "2024-02-01",
            "endDate": "2024-02-02",
            "reason": "Vacation",
        },
    )

    assert response.status_code == 200
    assert response.json()["status"] == "PENDING"


def test_submit_leave_validation_error(client, set_current_user, employee_user):
    set_current_user(employee_user)

    response = client.post(
        "/api/ems/leaves/",
        json={
            "leaveType": "INVALID",
            "startDate": "2024-02-01",
            "endDate": "2024-02-02",
        },
    )

    assert response.status_code == 422


def test_cancel_leave_success(client, monkeypatch, set_current_user, employee_user):
    set_current_user(employee_user)
    monkeypatch.setattr(
        leave_router.leave_service,
        "cancel_leave",
        lambda db, emp_id, leave_id: {"message": f"Leave {leave_id} cancelled", "empId": emp_id},
    )

    response = client.delete("/api/ems/leaves/5")

    assert response.status_code == 200
    assert response.json()["empId"] == "EMP003"


def test_my_leaves_success(client, monkeypatch, set_current_user, employee_user):
    set_current_user(employee_user)
    monkeypatch.setattr(
        leave_router.leave_service,
        "get_my_leaves",
        lambda db, emp_id, page, size: ([{"id": 5, "empId": emp_id}], 1),
    )

    response = client.get("/api/ems/leaves/my")

    assert response.status_code == 200
    assert response.json()["content"][0]["id"] == 5


def test_my_balance_success(client, monkeypatch, set_current_user, employee_user):
    set_current_user(employee_user)
    monkeypatch.setattr(
        leave_router.leave_service,
        "get_balance",
        lambda db, emp_id: {"empId": emp_id, "annualRemaining": 10},
    )

    response = client.get("/api/ems/leaves/balance")

    assert response.status_code == 200
    assert response.json()["annualRemaining"] == 10


def test_pending_leaves_success(client, monkeypatch, set_current_user, manager_user):
    set_current_user(manager_user)
    monkeypatch.setattr(
        leave_router.leave_service,
        "get_pending_leaves",
        lambda db, emp_id, page, size: ([{"id": 7}], 1),
    )

    response = client.get("/api/ems/leaves/pending")

    assert response.status_code == 200
    assert response.json()["content"][0]["id"] == 7


def test_all_leaves_success(client, monkeypatch, set_current_user, manager_user):
    set_current_user(manager_user)
    monkeypatch.setattr(
        leave_router.leave_service,
        "get_all_leaves",
        lambda db, emp_id, status, page, size: ([{"id": 9, "status": status}], 1),
    )

    response = client.get("/api/ems/leaves/all?empId=EMP003&status=APPROVED")

    assert response.status_code == 200
    assert response.json()["content"][0]["status"] == "APPROVED"


def test_review_leave_success(client, monkeypatch, set_current_user, manager_user):
    set_current_user(manager_user)
    monkeypatch.setattr(
        leave_router.leave_service,
        "review_leave",
        lambda db, leave_id, action, actor, notes: {
            "id": leave_id,
            "status": action,
            "reviewedBy": actor,
            "reviewNotes": notes,
        },
    )

    response = client.put(
        "/api/ems/leaves/5/review",
        json={"action": "APPROVED", "reviewNotes": "Approved"},
    )

    assert response.status_code == 200
    assert response.json()["reviewedBy"] == "EMP002"


def test_employee_balance_lookup_success(
    client, monkeypatch, set_current_user, manager_user
):
    set_current_user(manager_user)
    monkeypatch.setattr(
        leave_router.leave_service,
        "get_balance",
        lambda db, emp_id: {"empId": emp_id, "annualRemaining": 8},
    )

    response = client.get("/api/ems/leaves/balance/EMP003")

    assert response.status_code == 200
    assert response.json()["empId"] == "EMP003"


def test_grant_leave_success(client, monkeypatch, set_current_user, admin_user):
    set_current_user(admin_user)
    monkeypatch.setattr(
        leave_router.leave_service,
        "grant_leave",
        lambda db, actor, emp_id, payload: {"grantedBy": actor, "empId": emp_id, **payload},
    )

    response = client.post(
        "/api/ems/leaves/grant/EMP003",
        json={
            "leaveType": "SICK",
            "startDate": "2024-02-10",
            "endDate": "2024-02-10",
            "reason": "Medical",
        },
    )

    assert response.status_code == 200
    assert response.json()["grantedBy"] == "EMP001"


def test_grant_leave_forbidden_for_manager(client, set_current_user, manager_user):
    set_current_user(manager_user)

    response = client.post(
        "/api/ems/leaves/grant/EMP003",
        json={
            "leaveType": "SICK",
            "startDate": "2024-02-10",
            "endDate": "2024-02-10",
        },
    )

    assert response.status_code == 403
