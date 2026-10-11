def login(client, username):
    return client.post("/login", data={"username": username, "password": "testpassword"})


def test_index_redirects_to_login(client):
    resp = client.get("/")
    assert resp.status_code == 302
    assert "/login" in resp.headers["Location"]


def test_login_page_loads(client):
    resp = client.get("/login")
    assert resp.status_code == 200
    assert "login" in resp.get_data(as_text=True).lower()


def test_login_success_redirects_to_dashboard(client):
    resp = login(client, "bob")
    assert resp.status_code == 302
    assert "/dashboard" in resp.headers["Location"]


def test_dashboard_loads_after_login(client):
    login(client, "bob")
    resp = client.get("/dashboard")
    assert resp.status_code == 200
    assert "Gift Dashboard" in resp.get_data(as_text=True)


def test_ideas_page_requires_login(client):
    resp = client.get("/user_gift_ideas/alice")
    assert resp.status_code == 302
    assert "/login" in resp.headers["Location"]


def test_ideas_page_hides_buyer_without_shared_family(client):
    login(client, "bob")
    resp = client.get("/user_gift_ideas/alice")
    assert resp.status_code == 200

    html = resp.get_data(as_text=True)

    # Idea bought by the connected user is shown as "Me (...)"
    assert "Me (bob)" in html
    # Buyer sharing a family with the connected user is never anonymised
    assert "Dave" in html
    # Buyer sharing no family with the connected user is anonymised
    assert "Anonymous" in html
    assert "Carol" not in html
