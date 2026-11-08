from alembic import context
from app.db import engine, Base
from app import models
config=context.config
target_metadata=Base.metadata
if context.is_offline_mode():
    context.configure(url=str(engine.url),target_metadata=target_metadata,literal_binds=True)
    with context.begin_transaction(): context.run_migrations()
else:
    with engine.connect() as connection:
        sqlite = connection.dialect.name == 'sqlite'
        if sqlite:
            connection.exec_driver_sql('PRAGMA foreign_keys=OFF')
            connection.commit()
        context.configure(connection=connection,target_metadata=target_metadata,render_as_batch=True)
        try:
            with context.begin_transaction():
                context.run_migrations()
                if sqlite and connection.exec_driver_sql('PRAGMA foreign_key_check').fetchall():
                    raise RuntimeError('Migration produced invalid foreign-key references')
        finally:
            if sqlite:
                connection.exec_driver_sql('PRAGMA foreign_keys=ON')
