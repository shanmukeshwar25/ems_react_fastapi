import sys
from pathlib import Path
from sqlalchemy import create_engine, text

# Add backend to path
backend_path = Path(r"d:\EMSfull_python\fullems-main\EmployeeManagementSystem\ems-backend-python")
sys.path.append(str(backend_path))

from core.config import settings
from core.security import hash_password

def fix_password():
    SQLALCHEMY_DATABASE_URL = f"postgresql://{settings.db_user}:{settings.db_password}@{settings.db_host}:{settings.db_port}/{settings.db_name}"
    engine = create_engine(SQLALCHEMY_DATABASE_URL)
    
    new_hash = hash_password("Mouni@1702")
    print(f"Generated new hash for 'Mouni@1702': {new_hash}")
    
    with engine.connect() as conn:
        try:
            conn.execute(text("UPDATE users SET password = :new_hash WHERE emp_id = 'TT0001'"), {"new_hash": new_hash})
            conn.commit()
            print("Successfully updated password for TT0001.")
        except Exception as e:
            print(f"Error: {e}")

if __name__ == "__main__":
    fix_password()
