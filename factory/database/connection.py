"""
Conexao com o Banco de Dados - Fabrica de Agentes
"""
from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker, declarative_base
from pathlib import Path

# Diretorio do banco de dados
DATABASE_DIR = Path(__file__).parent
DATABASE_FILE = DATABASE_DIR / "factory.db"

# URL do banco de dados SQLite
DATABASE_URL = f"sqlite:///{DATABASE_FILE}"

# Criar engine
engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False},
    echo=False  # Set True for SQL debugging
)

# Habilitar foreign keys no SQLite
@event.listens_for(engine, "connect")
def set_sqlite_pragma(dbapi_connection, connection_record):
    cursor = dbapi_connection.cursor()
    cursor.execute("PRAGMA foreign_keys=ON")
    cursor.close()

# Session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base para os modelos
Base = declarative_base()


def get_db():
    """Dependency para obter sessao do banco de dados"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db():
    """Inicializa o banco de dados criando todas as tabelas"""
    from . import models  # Import models to register them
    Base.metadata.create_all(bind=engine)
    print(f"[Factory DB] Banco de dados inicializado em: {DATABASE_FILE}")
    return True


def reset_db():
    """Remove e recria todas as tabelas (CUIDADO: perde todos os dados)"""
    from . import models
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    print(f"[Factory DB] Banco de dados resetado em: {DATABASE_FILE}")
    return True


if __name__ == "__main__":
    init_db()
