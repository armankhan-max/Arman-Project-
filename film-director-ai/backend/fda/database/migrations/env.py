from alembic import context
from sqlalchemy import create_engine, pool

from fda.config import get_settings
from fda.database.models import Base

target_metadata = Base.metadata


def url():
    return context.config.attributes.get("url") or get_settings().database_url


def run_offline():
    context.configure(url=url(), target_metadata=target_metadata, literal_binds=True)
    with context.begin_transaction():
        context.run_migrations()


def run_online():
    eng = create_engine(url(), poolclass=pool.NullPool)
    with eng.connect() as conn:
        context.configure(connection=conn, target_metadata=target_metadata, compare_type=True)
        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_offline()
else:
    run_online()
