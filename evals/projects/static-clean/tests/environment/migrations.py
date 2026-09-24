"""Migration lifecycle belongs to environment setup, not collected tests."""

from alembic import command


def upgrade_database(alembic_config: object) -> None:
    command.upgrade(alembic_config, "head")
