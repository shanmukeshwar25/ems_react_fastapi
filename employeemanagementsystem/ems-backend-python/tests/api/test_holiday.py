from routers import holiday_router


def test_list_holidays_success(client, monkeypatch, set_current_user, employee_user):
    set_current_user(employee_user)
    monkeypatch.setattr(
        holiday_router.holiday_service,
        "get_holidays_by_year",
        lambda db, year: [{"name": "New Year", "year": year}],
    )

    response = client.get("/api/ems/holidays/?year=2024")

    assert response.status_code == 200
    assert response.json()[0]["year"] == 2024


def test_add_holiday_success(client, monkeypatch, set_current_user, admin_user):
    set_current_user(admin_user)
    monkeypatch.setattr(
        holiday_router.holiday_service,
        "add_holiday",
        lambda db, payload, actor: {**payload, "createdBy": actor},
    )

    response = client.post(
        "/api/ems/holidays/",
        json={
            "holidayDate": "2024-12-25",
            "name": "Christmas",
            "description": "Holiday",
            "isMandatory": True,
        },
    )

    assert response.status_code == 200
    assert response.json()["createdBy"] == "EMP001"


def test_add_holiday_forbidden_for_employee(client, set_current_user, employee_user):
    set_current_user(employee_user)

    response = client.post(
        "/api/ems/holidays/",
        json={"holidayDate": "2024-12-25", "name": "Christmas"},
    )

    assert response.status_code == 403


def test_update_holiday_success(client, monkeypatch, set_current_user, admin_user):
    set_current_user(admin_user)
    monkeypatch.setattr(
        holiday_router.holiday_service,
        "update_holiday",
        lambda db, holiday_id, payload, actor: {"id": holiday_id, "updatedBy": actor, **payload},
    )

    response = client.put(
        "/api/ems/holidays/4",
        json={"holidayDate": "2024-12-25", "name": "Christmas Updated"},
    )

    assert response.status_code == 200
    assert response.json()["id"] == 4


def test_delete_holiday_success(client, monkeypatch, set_current_user, admin_user):
    set_current_user(admin_user)
    monkeypatch.setattr(holiday_router.holiday_service, "delete_holiday", lambda db, holiday_id: None)

    response = client.delete("/api/ems/holidays/4")

    assert response.status_code == 200
    assert response.json() == {"message": "Deleted"}


def test_delete_holiday_year_success(client, monkeypatch, set_current_user, admin_user):
    set_current_user(admin_user)
    monkeypatch.setattr(holiday_router.holiday_service, "delete_all_by_year", lambda db, year: 3)

    response = client.delete("/api/ems/holidays/year/2024")

    assert response.status_code == 200
    assert response.json() == {"deleted": 3}


def test_non_working_dates_success(client, monkeypatch, set_current_user, employee_user):
    set_current_user(employee_user)
    monkeypatch.setattr(
        holiday_router.holiday_service,
        "get_non_working_dates",
        lambda db, start, end: [start.isoformat(), end.isoformat()],
    )

    response = client.get("/api/ems/holidays/non-working?start=2024-01-01&end=2024-01-07")

    assert response.status_code == 200
    assert response.json() == ["2024-01-01", "2024-01-07"]


def test_non_working_dates_invalid_date_returns_400(
    client, set_current_user, employee_user
):
    set_current_user(employee_user)

    response = client.get("/api/ems/holidays/non-working?start=bad&end=2024-01-07")

    assert response.status_code == 400
