import storage


def _ideas(tmp_path):
    return storage.load_gift_ideas(str(tmp_path))


def _add_idea(tmp_path, idea):
    ideas = _ideas(tmp_path)
    ideas.append(idea)
    storage.save_gift_ideas(str(tmp_path), ideas)


def login(client, username):
    return client.post("/login", data={"username": username, "password": "testpassword"})


def test_bought_items_filter_by_user(client, tmp_path):
    login(client, "bob")
    _add_idea(tmp_path, {"gift_idea_id": 10, "user_id": "carol", "gift_name": "Carol thing", "description": "", "added_by": "carol", "bought_by": "bob"})

    # everyone: both items shown, dropdown lists every recipient
    resp = client.get("/bought_items")
    assert resp.status_code == 200
    html = resp.get_data(as_text=True)
    assert "From self" in html and "Carol thing" in html
    assert "Everyone" in html
    assert "userFilter" in html
    assert "Mark all as gifted" in html
    assert ">Alice</option>" in html and ">Carol</option>" in html

    # filtered to a single recipient
    resp = client.get("/bought_items?user=carol")
    assert resp.status_code == 200
    html = resp.get_data(as_text=True)
    assert "Carol thing" in html
    assert "From self" not in html
    assert 'value="carol" selected' in html


def test_bought_items_ignore_unknown_user(client, tmp_path):
    login(client, "bob")
    resp = client.get("/bought_items?user=doesnotexist")
    assert resp.status_code == 200
    html = resp.get_data(as_text=True)
    # falls back to everyone
    assert "From self" in html


def test_mark_all_as_gifted(client, tmp_path):
    login(client, "bob")
    _add_idea(tmp_path, {"gift_idea_id": 10, "user_id": "carol", "gift_name": "Carol thing", "description": "", "added_by": "carol", "bought_by": "bob"})

    resp = client.post("/mark_all_as_gifted", data={"next": "/bought_items"})
    assert resp.status_code == 302
    assert "/bought_items" in resp.headers["Location"]

    ideas = _ideas(tmp_path)
    gifted_ids = [i["gift_idea_id"] for i in ideas if i.get("gifted")]
    assert 1 in gifted_ids and 10 in gifted_ids
    # idea 2 is not bought by bob -> untouched
    idea2 = next(i for i in ideas if i["gift_idea_id"] == 2)
    assert not idea2.get("gifted")


def test_mark_all_as_gifted_filtered_by_user(client, tmp_path):
    login(client, "bob")
    _add_idea(tmp_path, {"gift_idea_id": 10, "user_id": "carol", "gift_name": "Carol thing", "description": "", "added_by": "carol", "bought_by": "bob"})

    resp = client.post("/mark_all_as_gifted", data={"user": "carol", "next": "/bought_items?user=carol"})
    assert resp.status_code == 302
    assert "/bought_items?user=carol" in resp.headers["Location"]

    ideas = _ideas(tmp_path)
    assert next(i for i in ideas if i["gift_idea_id"] == 10).get("gifted") is True
    assert next(i for i in ideas if i["gift_idea_id"] == 1).get("gifted") is None


def test_mark_all_as_gifted_noop(client, tmp_path):
    # alice bought nothing -> nothing to mark
    login(client, "alice")
    resp = client.post("/mark_all_as_gifted")
    assert resp.status_code == 302
    assert all(not i.get("gifted") for i in _ideas(tmp_path))


def test_mark_all_button_disabled_when_all_gifted(client, tmp_path):
    login(client, "bob")
    ideas = _ideas(tmp_path)
    for i in ideas:
        if i["gift_idea_id"] == 1:
            i["gifted"] = True
            i["date_gifted"] = "2026-01-01 00:00:00"
    storage.save_gift_ideas(str(tmp_path), ideas)

    # all filtered gifts are gifted -> button is disabled
    resp = client.get("/bought_items")
    html = resp.get_data(as_text=True)
    assert 'id="markAllGifted"' in html and "disabled" in html

    # one non-gifted gift remains -> button is enabled
    ideas = _ideas(tmp_path)
    for i in ideas:
        if i["gift_idea_id"] == 1:
            i["gifted"] = False
            i.pop("date_gifted", None)
    storage.save_gift_ideas(str(tmp_path), ideas)

    resp = client.get("/bought_items")
    html = resp.get_data(as_text=True)
    assert 'id="markAllGifted" class="btn-primary"' in html
