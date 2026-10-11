import pytest

import app as app_module
import storage


@pytest.fixture(autouse=True)
def _english_locale(monkeypatch):
    """Force the app into English regardless of the host's LANG/locale."""
    monkeypatch.setenv("LANG", "en")


@pytest.fixture()
def client(tmp_path):
    """Test client with an isolated, minimal data directory."""
    app = app_module.app
    app.config.update(
        TESTING=True,
        DATA=str(tmp_path),
        AVATAR_DIR=tmp_path / "avatars",
    )

    password_hash = app_module.ph.hash("testpassword")

    users = [
        {"username": "bob", "password": password_hash, "full_name": "Bob", "groups": ["Fam1", "Fam2"]},
        {"username": "alice", "password": password_hash, "full_name": "Alice", "groups": ["Fam1"]},
        {"username": "carol", "password": password_hash, "full_name": "Carol", "groups": ["Fam3"]},
        {"username": "dave", "password": password_hash, "full_name": "Dave", "groups": ["Fam2"]},
    ]
    storage.save_users(str(tmp_path), users)

    ideas = [
        {"gift_idea_id": 1, "user_id": "alice", "gift_name": "From self", "description": "", "added_by": "alice", "bought_by": "bob"},
        {"gift_idea_id": 2, "user_id": "alice", "gift_name": "From shared family", "description": "", "added_by": "alice", "bought_by": "dave"},
        {"gift_idea_id": 3, "user_id": "alice", "gift_name": "From stranger", "description": "", "added_by": "alice", "bought_by": "carol"},
    ]
    storage.save_gift_ideas(str(tmp_path), ideas)

    with app.test_client() as c:
        yield c
