import sqlalchemy
import sqlalchemy.ext.declarative as declaritive
import sqlalchemy.orm as orm


POSTGRES_USER="postgres"
POSTGRES_PASSWORD="password"
POSTGRES_SERVER="PG"
POSTGRES_PORT="5432"
POSTGRES_DB="postgres"

Db_URL = f"postgresql://{POSTGRES_USER}:{POSTGRES_PASSWORD}@{POSTGRES_SERVER}:{POSTGRES_PORT}/{POSTGRES_DB}"
engine = sqlalchemy.create_engine(Db_URL, echo=True)