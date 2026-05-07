import logging
from sqlalchemy.orm import Session
from core.database import SessionLocal, engine, Base
from models.roles import Roles
from models.employee import Employee
from models.user import User
from models.enums import RolesEnum
from sqlalchemy import text

logger = logging.getLogger(__name__)

def seed_db():
    db = SessionLocal()
    try:
        # 1. Ensure tables are created
        Base.metadata.create_all(bind=engine)
        
        # 2. Seed Roles
        for role_name in RolesEnum:
            role = db.query(Roles).filter(Roles.role == role_name).first()
            if not role:
                db.add(Roles(role=role_name))
        db.commit()
        
        # 3. Seed Initial Admin (TT0001) if not exists
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
                description="Backend developer with 2 years of experience",
                gender="MALE",
                is_employee_active=True
            )
            db.add(admin_emp)
            db.commit()
            
            # Seed User for admin
            admin_user = User(
                emp_id="TT0001",
                password="$2a$12$5gHPxFcrc4tbgYsIqDWqy.EuT6lnWzQwDQvZwpLBAL/1oj4LRab/C", # Mouni@1702
                is_user_active=True
            )
            db.add(admin_user)
            db.commit()
            
            # Assign all roles to admin
            all_roles = db.query(Roles).all()
            from models.roles import UserRoles
            for r in all_roles:
                user_role = UserRoles(emp_id="TT0001", role_id=r.role_id)
                db.add(user_role)
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
