import storage


def test_user_friend_and_entry():
    import tempfile, os
    os.environ["DB_PATH"] = tempfile.mktemp(suffix=".db")
    import importlib
    importlib.reload(storage)
    storage.init_db()
    storage.upsert_user(1, "A")
    assert storage.set_friend(1, 2) is True
    assert storage.set_friend(1, 3) is False
    storage.save_entry(1, "good day")
    assert storage.weekly_entries(1)[0][1] == "good day"
