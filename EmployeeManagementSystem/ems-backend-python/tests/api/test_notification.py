from routers import notification_router


def test_my_notifications_success(client, monkeypatch, set_current_user, employee_user):
    set_current_user(employee_user)
    monkeypatch.setattr(
        notification_router.notification_service,
        "get_my_notifications",
        lambda db, emp_id, page, size: ([{"id": 1, "empId": emp_id}], 1),
    )

    response = client.get("/api/ems/notifications/my")

    assert response.status_code == 200
    assert response.json()["content"][0]["id"] == 1


def test_unread_count_success(client, monkeypatch, set_current_user, employee_user):
    set_current_user(employee_user)
    monkeypatch.setattr(
        notification_router.notification_service,
        "get_unread_count",
        lambda db, emp_id: 5,
    )

    response = client.get("/api/ems/notifications/unread-count")

    assert response.status_code == 200
    assert response.json() == {"count": 5}


def test_mark_read_success(client, monkeypatch, set_current_user, employee_user):
    set_current_user(employee_user)
    monkeypatch.setattr(
        notification_router.notification_service,
        "mark_notification_read",
        lambda db, notification_id, emp_id: None,
    )

    response = client.put("/api/ems/notifications/10/read")

    assert response.status_code == 200
    assert response.json() == {"message": "Marked as read"}


def test_mark_all_read_success(client, monkeypatch, set_current_user, employee_user):
    set_current_user(employee_user)
    monkeypatch.setattr(
        notification_router.notification_service,
        "mark_all_read",
        lambda db, emp_id: None,
    )

    response = client.put("/api/ems/notifications/read-all")

    assert response.status_code == 200
    assert response.json() == {"message": "All marked as read"}


def test_notifications_require_authentication(client, set_current_user):
    set_current_user(None)

    response = client.get("/api/ems/notifications/my")

    assert response.status_code == 401
