import sys
from pathlib import Path
from sqlalchemy import create_engine, text

# Add backend to path
backend_path = Path(r"d:\EMSfull_python\fullems-main\EmployeeManagementSystem\ems-backend-python")
sys.path.append(str(backend_path))

from core.config import settings

def check_roles_v2():
    SQLALCHEMY_DATABASE_URL = f"postgresql://{settings.db_user}:{settings.db_password}@{settings.db_host}:{settings.db_port}/{settings.db_name}"
    engine = create_engine(SQLALCHEMY_DATABASE_URL)
    
    with engine.connect() as conn:
        try:
            # Check columns in user_roles
            cols = conn.execute(text("SELECT column_name FROM information_schema.columns WHERE table_name = 'user_roles'")).fetchall()
            print("Columns in user_roles:", [c[0] for c in cols])
            
            # Maybe it's a join with roles table?
            # Or role_id?
            result = conn.execute(text("SELECT * FROM user_roles WHERE emp_id = 'TT0001'")).fetchall()
            print(f"Raw data for TT0001 in user_roles: {result}")
            
        except Exception as e:
            print(f"Error: {e}")

if __name__ == "__main__":
    check_roles_v2()
