import logging
from logging.config import fileConfig

from flask import current_app

from alembic import context
from sqlalchemy import engine_from_config, pool, create_engine

config = context.config

fileConfig(config.config_file_name)
logger = logging.getLogger('alembic.env')

import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))


try:
    from app.models import Base
    target_metadata = Base.metadata
except ImportError as e:
    logger.error(f"Error importing app.models: {e}. Check your PYTHONPATH and module structure.")
    target_metadata = None



def get_database_url_from_flask_config():

    url = current_app.config.get("SQLALCHEMY_DATABASE_URI")
    if not url:
        url = current_app.config.get("DATABASE_URL")

    if not url:
        raise Exception("No database URL (SQLALCHEMY_DATABASE_URI or DATABASE_URL) found in Flask config.")
    return url


config.set_main_option('sqlalchemy.url', get_database_url_from_flask_config())

def run_migrations_offline():
    """Run migrations in 'offline' mode.

    This configures the context with just a URL
    and not an Engine, though an Engine is acceptable
    here as well.  By skipping the Engine creation
    we don't even need a DBAPI to be available.

    Calls to context.execute() here emit the given string to the
    script output.

    """
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online():
    """Run migrations in 'online' mode.

    In this scenario we need to create an Engine
    and associate a connection with the context.

    """

    def process_revision_directives(context, revision, directives):
        if getattr(config.cmd_opts, 'autogenerate', False):
            script = directives[0]
            if script.upgrade_ops.is_empty():
                directives[:] = []
                logger.info('No changes in schema detected.')

    conf_args = current_app.extensions['migrate'].configure_args
    if conf_args.get("process_revision_directives") is None:
        conf_args["process_revision_directives"] = process_revision_directives


    connectable = create_engine(get_database_url_from_flask_config())

    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            **conf_args
        )

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()