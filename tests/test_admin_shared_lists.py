import storage


def _promote_admin(tmp_path, username):
    users = storage.load_users(str(tmp_path))
    for u in users:
        if u["username"] == username:
            u["admin"] = True
    storage.save_users(str(tmp_path), users)


def _add_shared_list(tmp_path, owner="bob", name="My Shared List", username="shared_family_list"):
    users = storage.load_users(str(tmp_path))
    users.append(
        {
            "username": username,
            "full_name": name,
            "admin": False,
            "guest": False,
            "shared_list": True,
            "list_owner": owner,
            "list_members": [owner],
            "avatar": "icons/avatar1.png",
        }
    )
    storage.save_users(str(tmp_path), users)

    ideas = storage.load_gift_ideas(str(tmp_path))
    ideas.append(
        {
            "gift_idea_id": max(i["gift_idea_id"] for i in ideas) + 1,
            "user_id": username,
            "gift_name": "List idea",
            "description": "",
            "added_by": owner,
            "bought_by": "",
        }
    )
    storage.save_gift_ideas(str(tmp_path), ideas)


def login(client, username):
    return client.post("/login", data={"username": username, "password": "testpassword"})


def test_admin_dashboard_requires_login(client):
    resp = client.get("/admin/shared_lists")
    assert resp.status_code == 302
    assert "/login" in resp.headers["Location"]


def test_non_admin_cannot_access_admin_dashboard(client):
    login(client, "alice")
    resp = client.get("/admin/shared_lists")
    assert resp.status_code == 302
    assert "/dashboard" in resp.headers["Location"]


def test_admin_shared_lists_page_shows_shared_lists(client, tmp_path):
    _add_shared_list(tmp_path)
    _promote_admin(tmp_path, "bob")
    login(client, "bob")

    resp = client.get("/admin/shared_lists")
    assert resp.status_code == 200
    html = resp.get_data(as_text=True)
    assert "My Shared List" in html
    assert "shared_family_list" in html


def test_non_admin_cannot_delete_shared_list(client, tmp_path):
    _add_shared_list(tmp_path)
    login(client, "alice")

    resp = client.post("/admin/delete_shared_list/shared_family_list")
    assert resp.status_code == 302
    assert "/dashboard" in resp.headers["Location"]

    users = storage.load_users(str(tmp_path))
    assert any(u["username"] == "shared_family_list" for u in users)


def test_admin_delete_shared_list_removes_user_and_ideas(client, tmp_path):
    _add_shared_list(tmp_path)
    _promote_admin(tmp_path, "bob")
    login(client, "bob")

    resp = client.post("/admin/delete_shared_list/shared_family_list")
    assert resp.status_code == 302
    assert "/admin/shared_lists" in resp.headers["Location"]

    users = storage.load_users(str(tmp_path))
    assert not any(u["username"] == "shared_family_list" for u in users)

    ideas = storage.load_gift_ideas(str(tmp_path))
    assert not any(i["user_id"] == "shared_family_list" for i in ideas)


def test_admin_delete_missing_shared_list_flashes_error(client, tmp_path):
    _promote_admin(tmp_path, "bob")
    login(client, "bob")

    resp = client.post("/admin/delete_shared_list/does_not_exist", follow_redirects=True)
    assert resp.status_code == 200
    assert "Shared list not found" in resp.get_data(as_text=True)
