import pytest
from server.database import SQLiteDBManager, UserModel, DEFAULT_RATING


@pytest.fixture
def orm_db():
    # Use SQLite in-memory database for fast isolated unit tests
    manager = SQLiteDBManager("sqlite:///:memory:")
    yield manager


def test_orm_initialization(orm_db):
    """Verify SQLiteDBManager initializes engine and tables properly."""
    assert orm_db.engine is not None



def test_orm_user_lifecycle(orm_db):
    """Test user registration, querying, password verification, and rating updates."""
    # User does not exist initially
    assert orm_db.find_user("orm_user") is None
    assert orm_db.verify_password("orm_user", "password") is False
    assert orm_db.get_user_rating("orm_user") == DEFAULT_RATING

    # Register user
    assert orm_db.register_user("orm_user", "password123") is True

    # Duplicate registration fails
    assert orm_db.register_user("orm_user", "password123") is False

    # Find user & verify password
    user = orm_db.find_user("orm_user")
    assert user is not None
    assert user.username == "orm_user"
    assert user.rating == DEFAULT_RATING

    assert orm_db.verify_password("orm_user", "password123") is True
    assert orm_db.verify_password("orm_user", "wrong") is False

    # Update rating
    assert orm_db.update_user_rating("orm_user", 1500) is True
    assert orm_db.get_user_rating("orm_user") == 1500

    # Non-existent user rating update returns False
    assert orm_db.update_user_rating("non_existent", 1400) is False
