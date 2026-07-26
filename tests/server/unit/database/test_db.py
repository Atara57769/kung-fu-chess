import os
import pytest
from server.database.db_manager import DBManager

TEST_DB = os.path.join("tests", "server", "unit", "database", "test_kung_fu_chess.db")

@pytest.fixture
def db():
    # Clear any previous test DB leftovers before running
    if os.path.exists(TEST_DB):
        try:
            os.remove(TEST_DB)
        except Exception:
            pass
            
    manager = DBManager(TEST_DB)
    yield manager

    # Teardown: remove DB file
    if os.path.exists(TEST_DB):
        try:
            os.remove(TEST_DB)
        except Exception:
            pass

def test_db_initialization(db):
    """Verify that tables are created on database initialization."""
    assert os.path.exists(TEST_DB)

def test_register_and_authenticate(db):
    """Verify that a user can register and authenticate via the current DBManager API."""
    # New user should not exist yet
    assert db.find_user("alice_test") is None

    # Register the user
    registered = db.register_user("alice_test", "pass123")
    assert registered is True

    # User should now be found
    user = db.find_user("alice_test")
    assert user is not None
    assert user.username == "alice_test"
    assert user.rating == 1200

    # Correct password should verify
    assert db.verify_password("alice_test", "pass123") is True

    # Wrong password should not verify
    assert db.verify_password("alice_test", "wrong_pass") is False

def test_duplicate_registration(db):
    """Verify that duplicate registrations fail integrity checks."""
    assert db.register_user("bob_dup", "pass") is True
    assert db.register_user("bob_dup", "other_pass") is False

def test_rating_update(db):
    """Verify that ratings can be set and fetched."""
    db.register_user("charlie", "pass")
    assert db.get_user_rating("charlie") == 1200
    
    db.update_user_rating("charlie", 1350)
    assert db.get_user_rating("charlie") == 1350
