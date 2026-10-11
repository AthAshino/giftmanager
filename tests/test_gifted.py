import storage


def _load_ideas(tmp_path):
    return storage.load_gift_ideas(str(tmp_path))


def _ideas_panel(html):
    return html.split('<section id="tab-ideas"', 1)[1].split('</section>', 1)[0]


def test_mark_as_gifted_only_buyer(client, tmp_path):
    # bob bought idea 1 -> allowed
    login(client, "bob")
    resp = client.post("/mark_as_gifted/1")
    assert resp.status_code == 302
    assert "/user_gift_ideas/alice?tab=history" in resp.headers["Location"]

    ideas = _load_ideas(tmp_path)
    idea = next(i for i in ideas if i["gift_idea_id"] == 1)
    assert idea.get("gifted") is True
    assert idea.get("date_gifted")


def test_mark_as_gifted_non_buyer_forbidden(client, tmp_path):
    # idea 1 is bought by bob, alice is the recipient/idea-giver but not the buyer
    login(client, "alice")
    resp = client.post("/mark_as_gifted/1")
    assert resp.status_code == 302

    ideas = _load_ideas(tmp_path)
    idea = next(i for i in ideas if i["gift_idea_id"] == 1)
    assert not idea.get("gifted")


def test_ideas_tab_excludes_gifted_and_history_tab_shows_them(client, tmp_path):
    login(client, "bob")
    client.post("/mark_as_gifted/1")
    resp = client.get("/user_gift_ideas/alice?tab=history")
    assert resp.status_code == 200
    html = resp.get_data(as_text=True)
    # the gifted idea appears on the page (history panel)...
    assert "From self" in html
    # ...but not in the actual-ideas panel
    assert "From self" not in _ideas_panel(html)
    # bob is the gifter -> can switch back
    assert "Switch back to bought" in html


def test_history_anonymizes_gifter_for_unrelated_user(client, tmp_path):
    # carol shares no family with bob (the gifter) and is neither gifter nor idea-giver
    login(client, "bob")
    client.post("/mark_as_gifted/1", follow_redirects=True)  # consume bob's flash
    login(client, "carol")
    resp = client.get("/user_gift_ideas/alice?tab=history")
    assert resp.status_code == 200
    html = resp.get_data(as_text=True)
    # the gifter's identity stays hidden for unrelated users
    assert "Bob" not in html
    assert "Anonymous" in html


def test_mark_as_not_gifted_switch_back(client, tmp_path):
    login(client, "bob")
    client.post("/mark_as_gifted/1")
    resp = client.post("/mark_as_not_gifted/1")
    assert resp.status_code == 302
    ideas = _load_ideas(tmp_path)
    idea = next(i for i in ideas if i["gift_idea_id"] == 1)
    assert idea.get("gifted") is False
    assert "date_gifted" not in idea
    # stays bought
    assert idea["bought_by"] == "bob"


def test_mark_as_not_gifted_only_authorized(client, tmp_path):
    login(client, "bob")
    client.post("/mark_as_gifted/1")
    # carol is neither the gifter nor the idea-giver
    login(client, "carol")
    client.post("/mark_as_not_gifted/1")
    ideas = _load_ideas(tmp_path)
    idea = next(i for i in ideas if i["gift_idea_id"] == 1)
    assert idea.get("gifted") is True


def test_delete_gifted_restricted(client, tmp_path):
    login(client, "bob")
    client.post("/mark_as_gifted/1")
    # carol (unrelated) cannot delete a gifted idea
    login(client, "carol")
    resp = client.delete("/delete_idea/1")
    assert resp.status_code == 403
    ideas = _load_ideas(tmp_path)
    assert any(i["gift_idea_id"] == 1 for i in ideas)

    # the gifter (bob) can delete it
    login(client, "bob")
    resp = client.delete("/delete_idea/1")
    assert resp.status_code == 204
    ideas = _load_ideas(tmp_path)
    assert not any(i["gift_idea_id"] == 1 for i in ideas)


def login(client, username):
    return client.post("/login", data={"username": username, "password": "testpassword"})
