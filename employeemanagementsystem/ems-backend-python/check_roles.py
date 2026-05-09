import sys
from pathlib import Path
from sqlalchemy import create_engine, text

# Add backend to path
backend_path = Path(r"d:\EMSfull_python\fullems-main\EmployeeManagementSystem\ems-backend-python")
sys.path.append(str(backend_path))

from core.config import settings

def check_roles():
    SQLALCHEMY_DATABASE_URL = f"postgresql://{settings.db_user}:{settings.db_password}@{settings.db_host}:{settings.db_port}/{settings.db_name}"
    engine = create_engine(SQLALCHEMY_DATABASE_URL)
    
    with engine.connect() as conn:
        try:
            # Query roles for TT0001
            # Assuming roles are in a table related to users/employees
            # Let's check table names first
            tables = conn.execute(text("SELECT table_name FROM information_schema.tables WHERE table_schema = 'public'")).fetchall()
            print("Tables in DB:", [t[0] for t in tables])
            
            result = conn.execute(text("SELECT role_name FROM user_roles WHERE emp_id = 'TT0001'")).fetchall()
            print(f"Roles for TT0001: {[r[0] for r in result]}")
            
        except Exception as e:
            print(f"Error checking roles: {e}")

if __name__ == "__main__":
    check_roles()
