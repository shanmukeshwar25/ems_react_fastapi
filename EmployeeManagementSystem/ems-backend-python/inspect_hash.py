import sys
from pathlib import Path
from sqlalchemy import create_engine, text

# Add backend to path
backend_path = Path(r"d:\EMSfull_python\fullems-main\EmployeeManagementSystem\ems-backend-python")
sys.path.append(str(backend_path))

from core.config import settings

def inspect_hash():
    SQLALCHEMY_DATABASE_URL = f"postgresql://{settings.db_user}:{settings.db_password}@{settings.db_host}:{settings.db_port}/{settings.db_name}"
    engine = create_engine(SQLALCHEMY_DATABASE_URL)
    
    with engine.connect() as conn:
        try:
            result = conn.execute(text("SELECT password FROM users WHERE emp_id = 'TT0001'")).fetchone()
            if result:
                pw = result[0]
                print(f"Password in DB for TT0001: '{pw}'")
                print(f"Length: {len(pw)}")
            else:
                print("User not found.")
        except Exception as e:
            print(f"Error: {e}")

if __name__ == "__main__":
    inspect_hash()
