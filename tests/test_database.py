import pytest
from sqlalchemy import select, func
from app.core.database import SessionFactory, transaction_scope, engine
from app.models import Roles, TopicStates, ThesisTypes, Users

def test_database_connection():
    """Test raw connection to MySQL."""
    with engine.connect() as conn:
        assert conn is not None

def test_seed_data_roles():
    """Verify standard system roles seeded in database."""
    with SessionFactory() as session:
        roles_count = session.scalar(select(func.count()).select_from(Roles))
        assert roles_count >= 13, f"Expected at least 13 roles, found {roles_count}"

def test_seed_data_topic_states():
    """Verify topic state catalog seeded in database."""
    with SessionFactory() as session:
        states_count = session.scalar(select(func.count()).select_from(TopicStates))
        assert states_count >= 11, f"Expected at least 11 topic states, found {states_count}"

def test_seed_data_thesis_types():
    """Verify thesis types seeded in database."""
    with SessionFactory() as session:
        types_count = session.scalar(select(func.count()).select_from(ThesisTypes))
        assert types_count >= 3, f"Expected at least 3 thesis types, found {types_count}"

def test_transaction_scope_rollback():
    """Verify transaction_scope rolls back changes when exception occurs."""
    initial_user_count = 0
    with SessionFactory() as session:
        initial_user_count = session.scalar(select(func.count()).select_from(Users))

    with pytest.raises(RuntimeError):
        with transaction_scope() as session:
            dummy_user = Users(
                user_code="TEST_USER_9999",
                email="test_rollback@example.com",
                password_hash="dummy_hash",
                full_name="Test Rollback User",
                is_active=1,
            )
            session.add(dummy_user)
            session.flush()
            # Force an exception to trigger rollback
            raise RuntimeError("Forced error for rollback test")

    # Assert user was NOT committed
    with SessionFactory() as session:
        final_user_count = session.scalar(select(func.count()).select_from(Users))
        assert final_user_count == initial_user_count
