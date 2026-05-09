from pathlib import Path
import sys

import pytest
from fastapi import FastAPI, HTTPException, status
from fastapi.testclient import TestClient

BACKEND_ROOT = Path(__file__).resolve().parents[1]
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

from chatbot.router import router as chatbot_router
from chatbot.resume_router import router as resume_router
from core.database import get_db
from core.dependencies import get_current_user
from core.exceptions import register_exception_handlers
from routers.auth_router import router as auth_router
from routers.attendance_router import router as attendance_router
from routers.employee_router import router as employee_router
from routers.holiday_router import router as holiday_router
from routers.leave_router import router as leave_router
from routers.notification_router import router as notification_router
from routers.other_routers import audit_router, db_config_router, import_router
from routers.role_router import router as role_router
from routers.timesheet_router import router as timesheet_router


class DummyDB:
    pass


def _build_test_app() -> FastAPI:
    app = FastAPI()
    register_exception_handlers(app)

    app.include_router(auth_router, prefix="/api")
    app.include_router(employee_router, prefix="/api")
    app.include_router(attendance_router, prefix="/api")
    app.include_router(leave_router, prefix="/api")
    app.include_router(timesheet_router, prefix="/api")
    app.include_router(holiday_router, prefix="/api")
    app.include_router(notification_router, prefix="/api")
    app.include_router(role_router, prefix="/api")
    app.include_router(audit_router, prefix="/api")
    app.include_router(db_config_router, prefix="/api")
    app.include_router(import_router, prefix="/api")
    app.include_router(chatbot_router, prefix="/api/chatbot")
    app.include_router(resume_router, prefix="/api/resume")

    @app.get("/api/health")
    def health():
        return {"status": "UP", "service": "ems-backend-python"}

    def _get_test_db():
        yield DummyDB()

    app.dependency_overrides[get_db] = _get_test_db
    return app


@pytest.fixture
def app():
    return _build_test_app()


@pytest.fixture
def client(app):
    with TestClient(app) as test_client:
        yield test_client


@pytest.fixture
def admin_user():
    return {
        "emp_id": "EMP001",
        "roles": ["ADMIN"],
        "email": "admin@company.com",
        "name": "Admin User",
    }


@pytest.fixture
def manager_user():
    return {
        "emp_id": "EMP002",
        "roles": ["MANAGER"],
        "email": "manager@company.com",
        "name": "Manager User",
    }


@pytest.fixture
def employee_user():
    return {
        "emp_id": "EMP003",
        "roles": ["EMPLOYEE"],
        "email": "employee@company.com",
        "name": "Employee User",
    }


@pytest.fixture
def set_current_user(app):
    def _set(user):
        if user is None:
            def _unauthenticated():
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Not authenticated",
                )

            app.dependency_overrides[get_current_user] = _unauthenticated
        else:
            app.dependency_overrides[get_current_user] = lambda: user

    return _set
