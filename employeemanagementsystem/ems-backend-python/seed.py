import logging
from sqlalchemy.orm import Session
from core.database import SessionLocal, engine, Base
from models.roles import Roles
from models.employee import Employee
from models.user import User
from models.enums import RolesEnum
from sqlalchemy import text

from core.security import hash_password

logger = logging.getLogger(__name__)

def seed_db():
    db = SessionLocal()
    try:
        # 1. Ensure tables and sequences are created
        Base.metadata.create_all(bind=engine)
        
        db.execute(text("CREATE SEQUENCE IF NOT EXISTS emp_id_seq START 1"))
        db.commit()
        
        # 2. Seed Roles
        for role_name in RolesEnum:
            role = db.query(Roles).filter(Roles.role == role_name).first()
            if not role:
                db.add(Roles(role=role_name))
        db.commit()
        
        # 3. Seed/Update Initial Admin (TT0001)
        admin_emp = db.query(Employee).filter(Employee.emp_id == "TT0001").first()
        if not admin_emp:
            admin_emp = Employee(
                emp_id="TT0001",
                name="Mounish Kakarla",
                company_email="mounish.k@tektalis.com",
                personal_email="mounsihchowdary1432@gmail.com",
                phone_number="7993175737",
                address="Hyderabad",
                department="DEVELOPMENT",
                designation="Software Engineer",
                skills="Java, Spring Boot, PostgreSQL, ReactJS,Docker,Python,AI,HTML,CSS",
                date_of_join="2025-12-15",
                date_of_birth="2003-02-17",
                gender="MALE",
                is_employee_active=True
            )
            db.add(admin_emp)
            db.commit()
            
        admin_user = db.query(User).filter(User.emp_id == "TT0001").first()
        if not admin_user:
            admin_user = User(emp_id="TT0001", password=hash_password("admin@123"), is_user_active=True)
            db.add(admin_user)
        else:
            # Force update password to admin@123
            admin_user.password = hash_password("admin@123")
        db.commit()
            
        # Ensure all roles assigned to admin
        all_roles = db.query(Roles).all()
        from models.roles import UserRoles
        for r in all_roles:
            exists = db.query(UserRoles).filter(UserRoles.emp_id == "TT0001", UserRoles.role_id == r.role_id).first()
            if not exists:
                db.add(UserRoles(emp_id="TT0001", role_id=r.role_id))
        db.commit()

        # 4. Seed User TT0004
        user_04_emp = db.query(Employee).filter(Employee.emp_id == "TT0004").first()
        if not user_04_emp:
            user_04_emp = Employee(
                emp_id="TT0004",
                name="Test User 04",
                company_email="test04@tektalis.com",
                is_employee_active=True
            )
            db.add(user_04_emp)
            db.commit()
            
            user_04 = User(
                emp_id="TT0004",
                password=hash_password("admin@123"),
                is_user_active=True
            )
            db.add(user_04)
            db.commit()
            
            # Assign EMPLOYEE role
            user_role_obj = db.query(Roles).filter(Roles.role == RolesEnum.EMPLOYEE).first()
            if user_role_obj:
                from models.roles import UserRoles
                db.add(UserRoles(emp_id="TT0004", role_id=user_role_obj.role_id))
            db.commit()

            
            # Update sequence
            db.execute(text("ALTER SEQUENCE emp_id_seq RESTART WITH 2"))
            db.commit()

        logger.info("✓ Database seeding completed successfully")
    except Exception as e:
        logger.error(f"✗ Database seeding failed: {e}")
        db.rollback()
    finally:
        db.close()
