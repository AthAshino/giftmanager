def login(client, username):
    return client.post("/login", data={"username": username, "password": "testpassword"})


def add_idea(client, selected_user, recipient, name, visible_groups=None):
    data = {"user": recipient, "name": name}
    if visible_groups is not None:
        data["visible_groups"] = visible_groups
    resp = client.post(f"/add_idea/{selected_user}", data=data)
    # Consume the "Idea added" flash message so it does not leak into the
    # next user's page in the test.
    client.get("/dashboard")
    return resp


def test_idea_restricted_to_family_hidden_for_other_families(client):
    # carol (Fam3) adds a secret idea for alice, visible only to Fam1
    login(client, "carol")
    resp = add_idea(client, "alice", "alice", "Family secret", visible_groups=["Fam1"])
    assert resp.status_code == 302

    # dave (Fam2) does not share Fam1 and did not add the idea -> hidden
    login(client, "dave")
    html = client.get("/user_gift_ideas/alice").get_data(as_text=True)
    assert "Family secret" not in html

    # bob is a member of Fam1 -> visible
    login(client, "bob")
    html = client.get("/user_gift_ideas/alice").get_data(as_text=True)
    assert "Family secret" in html


def test_idea_creator_always_sees_their_restricted_idea(client):
    # carol (Fam3) adds an idea restricted to Fam2; she is not a member of Fam2
    login(client, "carol")
    resp = add_idea(client, "alice", "alice", "Creator only", visible_groups=["Fam2"])
    assert resp.status_code == 302

    # the creator always keeps access even without the family
    login(client, "carol")
    html = client.get("/user_gift_ideas/alice").get_data(as_text=True)
    assert "Creator only" in html

    # dave (Fam2) sees it via family membership
    login(client, "dave")
    html = client.get("/user_gift_ideas/alice").get_data(as_text=True)
    assert "Creator only" in html


def test_unrestricted_idea_visible_to_all(client):
    login(client, "carol")
    resp = add_idea(client, "alice", "alice", "Public idea")
    assert resp.status_code == 302

    for username in ("bob", "dave", "carol"):
        login(client, username)
        html = client.get("/user_gift_ideas/alice").get_data(as_text=True)
        assert "Public idea" in html
