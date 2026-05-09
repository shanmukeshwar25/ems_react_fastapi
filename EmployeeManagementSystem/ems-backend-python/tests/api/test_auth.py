from routers import auth_router


def test_login_success_sets_tokens(client, monkeypatch):
    def fake_login(db, username, password):
        assert username == "admin@company.com"
        assert password == "secret123"
        return {"token": "access-token", "refreshToken": "refresh-token"}

    monkeypatch.setattr(auth_router.auth_service, "login", fake_login)

    response = client.post(
        "/api/auth/login",
        json={"username": "admin@company.com", "password": "secret123"},
    )

    assert response.status_code == 200
    assert response.json() == {
        "token": "access-token",
        "refreshToken": "refresh-token",
    }
    assert response.cookies.get("access_token") == "access-token"
    assert response.cookies.get("refresh_token") == "refresh-token"


def test_login_validation_error(client):
    response = client.post("/api/auth/login", json={"username": "admin@company.com"})

    assert response.status_code == 422


def test_refresh_success_sets_access_cookie(client, monkeypatch):
    def fake_refresh(db, refresh_token):
        assert refresh_token == "refresh-token"
        return {"token": "new-access", "refreshToken": "refresh-token"}

    monkeypatch.setattr(auth_router.auth_service, "refresh_token_fn", fake_refresh)

    response = client.post("/api/auth/refresh", json={"refreshToken": "refresh-token"})

    assert response.status_code == 200
    assert response.json()["token"] == "new-access"
    assert response.cookies.get("access_token") == "new-access"


def test_logout_clears_cookies(client):
    response = client.post("/api/auth/logout")

    assert response.status_code == 200
    assert response.json() == {"message": "Logged out"}


def test_me_success(client, monkeypatch, set_current_user, admin_user):
    set_current_user(admin_user)

    monkeypatch.setattr(
        auth_router.auth_service,
        "get_current_user_info",
        lambda db, emp_id: {
            "empId": emp_id,
            "name": "Admin User",
            "companyEmail": "admin@company.com",
            "roles": ["ADMIN"],
            "profileImage": None,
        },
    )

    response = client.get("/api/auth/me")

    assert response.status_code == 200
    assert response.json()["empId"] == "EMP001"


def test_me_requires_authentication(client, set_current_user):
    set_current_user(None)

    response = client.get("/api/auth/me")

    assert response.status_code == 401
    assert response.json()["detail"] == "Not authenticated"


def test_change_password_success(client, monkeypatch, set_current_user, employee_user):
    set_current_user(employee_user)
    called = {}

    def fake_change_password(db, emp_id, old_password, new_password):
        called["args"] = (emp_id, old_password, new_password)

    monkeypatch.setattr(auth_router.auth_service, "change_password", fake_change_password)

    response = client.put(
        "/api/auth/changePassword",
        json={"oldPassword": "old123", "newPassword": "new123"},
    )

    assert response.status_code == 200
    assert response.json() == {"message": "Password changed successfully"}
    assert called["args"] == ("EMP003", "old123", "new123")


def test_change_password_bad_old_password_returns_400(
    client, monkeypatch, set_current_user, employee_user
):
    set_current_user(employee_user)

    def fake_change_password(db, emp_id, old_password, new_password):
        raise ValueError("Current password is incorrect")

    monkeypatch.setattr(auth_router.auth_service, "change_password", fake_change_password)

    response = client.put(
        "/api/auth/changePassword",
        json={"oldPassword": "bad-old", "newPassword": "new123"},
    )

    assert response.status_code == 400
    assert response.json()["message"] == "Current password is incorrect"


def test_push_token_success(client, monkeypatch, set_current_user, employee_user):
    set_current_user(employee_user)
    called = {}

    def fake_save_push_token(db, emp_id, token):
        called["args"] = (emp_id, token)

    monkeypatch.setattr(auth_router.auth_service, "save_push_token", fake_save_push_token)

    response = client.put("/api/auth/push-token", json={"pushToken": "push-123"})

    assert response.status_code == 200
    assert response.json() == {"message": "Push token saved"}
    assert called["args"] == ("EMP003", "push-123")


def test_reset_password_success_for_admin(client, monkeypatch, set_current_user, admin_user):
    set_current_user(admin_user)
    called = {}

    def fake_reset_password(db, emp_id):
        called["emp_id"] = emp_id

    monkeypatch.setattr(auth_router.auth_service, "reset_password", fake_reset_password)

    response = client.post("/api/auth/reset-password/EMP100")

    assert response.status_code == 200
    assert response.json() == {"message": "Password reset for EMP100"}
    assert called["emp_id"] == "EMP100"


def test_reset_password_forbidden_for_employee(
    client, set_current_user, employee_user
):
    set_current_user(employee_user)

    response = client.post("/api/auth/reset-password/EMP100")

    assert response.status_code == 403
    assert response.json()["detail"] == "Insufficient permissions"
