import json
import os
from sqlalchemy import create_engine, Column, Integer, String, Text, inspect
from sqlalchemy.orm import declarative_base, sessionmaker

# =========================
# BASE
# =========================
Base = declarative_base()


# =========================
# MODELS
# =========================
class CHO(Base):
    __tablename__ = "chos"

    id = Column(Integer, primary_key=True)
    custom_id = Column(String, unique=True)
    title = Column(String)


class Memory(Base):
    __tablename__ = "memories"

    id = Column(Integer, primary_key=True)
    custom_id = Column(String, unique=True)
    title = Column(String)
    text = Column(Text)
    file_path = Column(String)
    license = Column(String)


class MetadataSpace(Base):
    __tablename__ = "metadata_spaces"

    id = Column(Integer, primary_key=True)
    name = Column(String, unique=True, nullable=False)
    author = Column(String, nullable=False, default="")
    updated_at = Column(String, nullable=False, default="")
    description = Column(Text, nullable=False, default="")
    fields_json = Column(Text, nullable=False, default="[]")

    @property
    def fields(self):
        try:
            value = json.loads(self.fields_json or "[]")
        except (TypeError, ValueError):
            return []
        return value if isinstance(value, list) else []

    @fields.setter
    def fields(self, value):
        self.fields_json = json.dumps(value or [], ensure_ascii=True)


# =========================
# PATH SETUP 
# =========================
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

MEMORY_DIR = os.path.join(BASE_DIR, "memory_files")

os.makedirs(MEMORY_DIR, exist_ok=True)

DB_PATH = os.path.join(MEMORY_DIR, "000_cordhisk.db")


# =========================
# ENGINE
# =========================
engine = create_engine(f"sqlite:///{DB_PATH}", echo=False)


# =========================
# CREATE TABLES
# =========================
Base.metadata.create_all(engine)


def _ensure_memory_license_column():
    inspector = inspect(engine)
    existing_columns = {column["name"] for column in inspector.get_columns("memories")}
    if "license" not in existing_columns:
        with engine.begin() as connection:
            connection.exec_driver_sql("ALTER TABLE memories ADD COLUMN license VARCHAR")


_ensure_memory_license_column()


# =========================
# SESSION
# =========================
Session = sessionmaker(bind=engine)
session = Session()