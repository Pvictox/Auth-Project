import os

from dotenv import load_dotenv
from sqlmodel import Session, select

from app.core.security import get_password_hash
from app.database import Database
from app.log_config.logging_config import get_logger
from app.models import PerfilModel, UsuarioModel

load_dotenv()

"""
    This module will seed the database with initial data for perfis and an admin user. [For now is the only strictly necessary data to seed, but you can add more if you want]
    It should be run after the database tables have been created. (You can do it after running the migration present in the alembic folder).
"""

logger = get_logger(__name__)


def seed_perfis():
    try:
        with Session(Database().engine) as session:
            perfis = [
                PerfilModel(valor="admin"),
                PerfilModel(valor="usuario"),
                PerfilModel(valor="convidado"),
            ]
            # check if perfis already exist
            existing_perfis = session.exec(select(PerfilModel)).all()
            if existing_perfis:
                logger.info(
                    "[SEED] Perfis already exist. Skipping seeding perfis."
                )
                return
            session.add_all(perfis)
            session.commit()
            logger.info("[SEED] Perfis seeded successfully.")
    except Exception as e:
        logger.error("[SEED - ERROR] Failed to seed perfis: %s", e)


def seed_admin_user():
    try:
        with Session(Database().engine) as session:
            # Check if admin user already exists
            result = session.exec(
                select(PerfilModel).where(PerfilModel.valor == "admin")
            ).first()
            if not result:
                logger.info(
                    "[SEED] Admin perfil not found. Please seed perfis first."
                )
                return

            admin_perfil = result

            # Check if admin user already exists
            existing_admin = session.exec(
                select(UsuarioModel).where(UsuarioModel.uid == "admin")
            ).first()

            if existing_admin:
                logger.info(
                    "[SEED] Admin user already exists. Skipping seeding admin user."
                )
                return

            admin_user = UsuarioModel(
                nome="Admin User",
                uid="admin",
                email="admin@admin.com",
                hashed_pass=get_password_hash(
                    os.getenv("ADMIN_BASE_PASSWORD")
                ),  # type: ignore
                perfil_id=admin_perfil.id_perfil,  # type: ignore
            )

            session.add(admin_user)
            session.commit()
            logger.info("[SEED] Admin user seeded successfully.")
    except Exception as e:
        logger.error("[SEED - ERROR] Failed to seed admin user: %s", e)


def check_and_seed():
    seed_perfis()
    seed_admin_user()
