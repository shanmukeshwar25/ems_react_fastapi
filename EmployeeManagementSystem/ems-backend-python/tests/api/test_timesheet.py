from routers import timesheet_router


def test_current_week_success(client, monkeypatch, set_current_user, employee_user):
    set_current_user(employee_user)
    monkeypatch.setattr(
        timesheet_router.timesheet_service,
        "get_current_week",
        lambda db, emp_id: {"empId": emp_id, "weekStartDate": "2024-01-01"},
    )

    response = client.get("/api/ems/timesheets/current-week")

    assert response.status_code == 200
    assert response.json()["empId"] == "EMP003"


def test_week_success(client, monkeypatch, set_current_user, employee_user):
    set_current_user(employee_user)

    def fake_get_week(db, emp_id, week_start):
        assert week_start.isoformat() == "2024-01-01"
        return {"empId": emp_id, "weekStartDate": week_start.isoformat()}

    monkeypatch.setattr(timesheet_router.timesheet_service, "get_week", fake_get_week)

    response = client.get("/api/ems/timesheets/week?weekStartDate=2024-01-01")

    assert response.status_code == 200
    assert response.json()["weekStartDate"] == "2024-01-01"


def test_week_invalid_date_returns_400(client, set_current_user, employee_user):
    set_current_user(employee_user)

    response = client.get("/api/ems/timesheets/week?weekStartDate=bad-date")

    assert response.status_code == 400


def test_save_timesheet_success(client, monkeypatch, set_current_user, employee_user):
    set_current_user(employee_user)
    monkeypatch.setattr(
        timesheet_router.timesheet_service,
        "save_entry",
        lambda db, emp_id, payload: {**payload, "id": 1, "empId": emp_id},
    )

    response = client.post(
        "/api/ems/timesheets/",
        json={
            "weekStartDate": "2024-01-01",
            "project": "EMS",
            "taskDescription": "Feature work",
            "mondayHours": 8,
        },
    )

    assert response.status_code == 200
    assert response.json()["id"] == 1


def test_submit_timesheet_success(client, monkeypatch, set_current_user, employee_user):
    set_current_user(employee_user)
    monkeypatch.setattr(
        timesheet_router.timesheet_service,
        "submit_week",
        lambda db, emp_id, week_start: {"empId": emp_id, "weekStartDate": str(week_start), "status": "SUBMITTED"},
    )

    response = client.post("/api/ems/timesheets/submit", json={"weekStartDate": "2024-01-01"})

    assert response.status_code == 200
    assert response.json()["status"] == "SUBMITTED"


def test_my_timesheets_success(client, monkeypatch, set_current_user, employee_user):
    set_current_user(employee_user)
    monkeypatch.setattr(
        timesheet_router.timesheet_service,
        "get_my_timesheets",
        lambda db, emp_id, start, end, page, size: ([{"id": 1, "empId": emp_id}], 1),
    )

    response = client.get("/api/ems/timesheets/my?from=2024-01-01&to=2024-01-31")

    assert response.status_code == 200
    assert response.json()["content"][0]["empId"] == "EMP003"


def test_pending_timesheets_success(client, monkeypatch, set_current_user, manager_user):
    set_current_user(manager_user)
    monkeypatch.setattr(
        timesheet_router.timesheet_service,
        "get_pending_timesheets",
        lambda db, page, size: ([{"id": 2, "status": "SUBMITTED"}], 1),
    )

    response = client.get("/api/ems/timesheets/pending")

    assert response.status_code == 200
    assert response.json()["content"][0]["status"] == "SUBMITTED"


def test_team_timesheets_success(client, monkeypatch, set_current_user, manager_user):
    set_current_user(manager_user)
    monkeypatch.setattr(
        timesheet_router.timesheet_service,
        "get_team_timesheets",
        lambda db, emp_id, status, start, end, page, size: ([{"id": 3, "status": status}], 1),
    )

    response = client.get(
        "/api/ems/timesheets/team?empId=EMP003&status=APPROVED&from=2024-01-01&to=2024-01-31"
    )

    assert response.status_code == 200
    assert response.json()["content"][0]["status"] == "APPROVED"


def test_delete_timesheet_success(client, monkeypatch, set_current_user, employee_user):
    set_current_user(employee_user)
    called = {}

    def fake_delete_entry(db, entry_id, actor):
        called["args"] = (entry_id, actor)

    monkeypatch.setattr(timesheet_router.timesheet_service, "delete_entry", fake_delete_entry)

    response = client.delete("/api/ems/timesheets/7")

    assert response.status_code == 200
    assert response.json() == {"message": "Deleted"}
    assert called["args"] == ("EMP003", 7)


def test_review_timesheet_success(client, monkeypatch, set_current_user, manager_user):
    set_current_user(manager_user)
    monkeypatch.setattr(
        timesheet_router.timesheet_service,
        "review_entry",
        lambda db, entry_id, action, actor, notes: {
            "id": entry_id,
            "status": action,
            "reviewedBy": actor,
            "reviewNotes": notes,
        },
    )

    response = client.put(
        "/api/ems/timesheets/7/review",
        json={"action": "APPROVED", "reviewNotes": "Looks good"},
    )

    assert response.status_code == 200
    assert response.json()["reviewedBy"] == "EMP002"


def test_review_timesheet_forbidden_for_employee(
    client, set_current_user, employee_user
):
    set_current_user(employee_user)

    response = client.put(
        "/api/ems/timesheets/7/review",
        json={"action": "APPROVED"},
    )

    assert response.status_code == 403
