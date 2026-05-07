from routers import attendance_router


def test_check_in_success(client, monkeypatch, set_current_user, employee_user):
    set_current_user(employee_user)
    monkeypatch.setattr(
        attendance_router.attendance_service,
        "check_in",
        lambda db, emp_id, notes: {"empId": emp_id, "status": "PRESENT", "notes": notes},
    )

    response = client.post("/api/ems/attendance/check-in", json={"notes": "Starting work"})

    assert response.status_code == 200
    assert response.json()["status"] == "PRESENT"


def test_check_out_success(client, monkeypatch, set_current_user, employee_user):
    set_current_user(employee_user)
    monkeypatch.setattr(
        attendance_router.attendance_service,
        "check_out",
        lambda db, emp_id: {"empId": emp_id, "status": "CHECKED_OUT"},
    )

    response = client.post("/api/ems/attendance/check-out")

    assert response.status_code == 200
    assert response.json()["status"] == "CHECKED_OUT"


def test_today_requires_authentication(client, set_current_user):
    set_current_user(None)

    response = client.get("/api/ems/attendance/today")

    assert response.status_code == 401


def test_today_success(client, monkeypatch, set_current_user, employee_user):
    set_current_user(employee_user)
    monkeypatch.setattr(
        attendance_router.attendance_service,
        "get_today_status",
        lambda db, emp_id: {"empId": emp_id, "status": "PRESENT"},
    )

    response = client.get("/api/ems/attendance/today")

    assert response.status_code == 200
    assert response.json()["empId"] == "EMP003"


def test_my_attendance_success(client, monkeypatch, set_current_user, employee_user):
    set_current_user(employee_user)
    monkeypatch.setattr(
        attendance_router.attendance_service,
        "get_my_attendance",
        lambda db, emp_id, page, size: ([{"id": 1, "empId": emp_id}], 1),
    )

    response = client.get("/api/ems/attendance/my")

    assert response.status_code == 200
    assert response.json()["numberOfElements"] == 1


def test_my_range_success(client, monkeypatch, set_current_user, employee_user):
    set_current_user(employee_user)

    def fake_range(db, emp_id, start, end):
        assert start.isoformat() == "2024-01-01"
        assert end.isoformat() == "2024-01-31"
        return [{"empId": emp_id, "attendanceDate": "2024-01-01"}]

    monkeypatch.setattr(
        attendance_router.attendance_service,
        "get_my_attendance_range",
        fake_range,
    )

    response = client.get("/api/ems/attendance/my/range?start=2024-01-01&end=2024-01-31")

    assert response.status_code == 200
    assert response.json()[0]["empId"] == "EMP003"


def test_my_range_invalid_date_returns_400(client, set_current_user, employee_user):
    set_current_user(employee_user)

    response = client.get("/api/ems/attendance/my/range?start=bad&end=2024-01-31")

    assert response.status_code == 400


def test_my_summary_success(client, monkeypatch, set_current_user, employee_user):
    set_current_user(employee_user)
    monkeypatch.setattr(
        attendance_router.attendance_service,
        "get_my_summary",
        lambda db, emp_id, month, year: {"empId": emp_id, "month": month, "year": year},
    )

    response = client.get("/api/ems/attendance/my/summary?month=1&year=2024")

    assert response.status_code == 200
    assert response.json()["month"] == 1


def test_override_attendance_success(client, monkeypatch, set_current_user, employee_user):
    set_current_user(employee_user)
    monkeypatch.setattr(
        attendance_router.attendance_service,
        "create_or_override",
        lambda db, payload, actor: {**payload, "recordedBy": actor},
    )

    response = client.post(
        "/api/ems/attendance/override",
        json={
            "empId": "EMP003",
            "attendanceDate": "2024-01-10",
            "status": "PRESENT",
        },
    )

    assert response.status_code == 200
    assert response.json()["recordedBy"] == "EMP003"


def test_update_attendance_success(client, monkeypatch, set_current_user, employee_user):
    set_current_user(employee_user)
    monkeypatch.setattr(
        attendance_router.attendance_service,
        "update_attendance",
        lambda db, item_id, payload, actor: {"id": item_id, "updatedBy": actor, **payload},
    )

    response = client.put(
        "/api/ems/attendance/10",
        json={
            "empId": "EMP003",
            "attendanceDate": "2024-01-10",
            "status": "LATE",
        },
    )

    assert response.status_code == 200
    assert response.json()["id"] == 10


def test_delete_attendance_forbidden_for_employee(
    client, set_current_user, employee_user
):
    set_current_user(employee_user)

    response = client.delete("/api/ems/attendance/10")

    assert response.status_code == 403


def test_team_attendance_success(client, monkeypatch, set_current_user, manager_user):
    set_current_user(manager_user)
    monkeypatch.setattr(
        attendance_router.attendance_service,
        "get_team_attendance",
        lambda db, start, end, emp_id, page, size: ([{"empId": "EMP003"}], 1),
    )

    response = client.get("/api/ems/attendance/team?start=2024-01-01&end=2024-01-31")

    assert response.status_code == 200
    assert response.json()["content"][0]["empId"] == "EMP003"


def test_daily_attendance_success(client, monkeypatch, set_current_user, manager_user):
    set_current_user(manager_user)
    monkeypatch.setattr(
        attendance_router.attendance_service,
        "get_daily_attendance",
        lambda db, date_param, department: [{"date": date_param.isoformat(), "department": department}],
    )

    response = client.get("/api/ems/attendance/daily?date=2024-01-10&department=Engineering")

    assert response.status_code == 200
    assert response.json()[0]["department"] == "Engineering"


def test_summary_for_employee_success(client, monkeypatch, set_current_user, manager_user):
    set_current_user(manager_user)
    monkeypatch.setattr(
        attendance_router.attendance_service,
        "get_my_summary",
        lambda db, emp_id, month, year: {"empId": emp_id, "month": month, "year": year},
    )

    response = client.get("/api/ems/attendance/summary/EMP003?month=1&year=2024")

    assert response.status_code == 200
    assert response.json()["empId"] == "EMP003"
