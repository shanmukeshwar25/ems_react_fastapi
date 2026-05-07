import sys
from pathlib import Path
from sqlalchemy import create_engine, text

# Add backend to path
backend_path = Path(r"d:\EMSfull_python\fullems-main\EmployeeManagementSystem\ems-backend-python")
sys.path.append(str(backend_path))

from core.security import verify_password, hash_password
from core.config import settings

def check_tt0004():
    SQLALCHEMY_DATABASE_URL = f"postgresql://{settings.db_user}:{settings.db_password}@{settings.db_host}:{settings.db_port}/{settings.db_name}"
    engine = create_engine(SQLALCHEMY_DATABASE_URL)
    
    with engine.connect() as conn:
        result = conn.execute(text("SELECT password FROM users WHERE emp_id = 'TT0004'")).fetchone()
        if result:
            hashed = result[0]
            print(f"Hashed password for TT0004: {hashed}")
            match = verify_password("admin@123", hashed)
            print(f"Matches 'admin@123': {match}")
            
            if not match:
                print("UPDATING PASSWORD to 'admin@123'...")
                new_hash = hash_password("admin@123")
                conn.execute(text("UPDATE users SET password = :h WHERE emp_id = 'TT0004'"), {"h": new_hash})
                conn.commit()
                print("Update successful.")
        else:
            print("User TT0004 not found.")

if __name__ == "__main__":
    check_tt0004()
