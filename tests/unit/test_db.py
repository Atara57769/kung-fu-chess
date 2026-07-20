import os
import pytest
from database.db_manager import DBManager

TEST_DB = "test_kung_fu_chess.db"

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
    
    # Teardown: clear connections and remove DB
    if os.path.exists(TEST_DB):
        try:
            os.remove(TEST_DB)
        except Exception:
            pass

def test_db_initialization(db):
    """Verify that tables are created on database initialization."""
    assert os.path.exists(TEST_DB)

def test_register_and_authenticate(db):
    """Verify that a user can register and authenticate."""
    res = db.authenticate_or_register("alice_test", "pass123")
    assert res is not None
    assert res.username == "alice_test"
    assert res.rating == 1200

    # Test authentication with correct credentials
    auth_ok = db.authenticate_or_register("alice_test", "pass123")
    assert auth_ok is not None
    assert auth_ok.username == "alice_test"

    # Test authentication with incorrect credentials
    auth_bad = db.authenticate_or_register("alice_test", "wrong_pass")
    assert auth_bad is None

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
