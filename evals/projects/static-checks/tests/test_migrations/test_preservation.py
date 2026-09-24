"""A collected schema-migration test is not a contract test."""

from tests.environment.migrations import upgrade_database_to


async def test_schema_upgrade(unmigrated_database_url: str) -> None:
    await upgrade_database_to(unmigrated_database_url, "head")
