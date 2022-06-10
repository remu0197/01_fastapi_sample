# 問題 1
def test_create_user(test_db, client):
    email = "deadpool@example.com"
    password = "chimichangas4life"
    response = client.post(
        "/users/",
        json={"email": email, "password": password},
    )
    assert response.status_code == 200, response.text
    data = response.json()
    user, token = data["user"], data["token"]
    assert user["email"] == "deadpool@example.com"
    assert "id" in user
    user_id = user["id"]

    # 生成されたトークンからユーザにアクセスできるのを確認
    response = client.get(
        "/me/",
        headers={
            'Authorization': "Bearer " + token,
            'accept': "application/json"
        },
    )
    data = response.json()
    assert user["id"] == data["id"]
    assert user["email"] == data["email"]

    response = client.get(f"/users/{user_id}")
    assert response.status_code == 200, response.text
    data = response.json()
    assert data["email"] == "deadpool@example.com"
    assert data["id"] == user_id


# 問題 2
def test_get_my_item(test_db, client):
    # テスト用のユーザ作成
    response = client.post(
        "/users/",
        json={"email": "poga@example.com", "password": "pogapoga"},
    )
    data = response.json()
    user, token = data["user"], data["token"]
    user_id = user["id"]

    test_item_count = 3

    # テスト用のitem作成
    for i in range(test_item_count):
        response = client.post(
            "/users/" + str(user_id) + "/items/",
            json={
                "title": "title" + str(i),
                "description": "description" + str(i),
            }
        )

    # 比較対象のユーザ作成
    client.post(
        "/users/",
        json={"email": "poga@example.com", "password": "pogapoga"},
    )

    test_item_count = 3
    test_item_ids = []

    # 比較対象用のitem作成
    for i in range(test_item_count):
        response = client.post(
            "/users/" + str(user_id) + "/items/",
            json={
                "title": "title" + str(i),
                "description": "description" + str(i),
            }
        )

    # 自分が所有しているItemを取得
    response = client.get(
        "/me/items/",
        headers={
            'Authorization': "Bearer " + token,
            'accept': "application/json"
        },
    )
    assert response.status_code == 200, response.text

    # 取り出したItemが自分のものか確認
    user_items = response.json()
    for item in user_items[:]:
        assert user_id == item['owner_id']

    # 自分のItemがすべて取り出せていることを確認
    response = client.get(
        "/items/"
    )
    all_items = response.json()
    for item in all_items:
        if user_id == item['owner_id']:
            assert item in user_items


# 問題 3
def test_delete_user(test_db, client):
    # テスト用のユーザ作成
    client.post(
        "/users/",
        json={"email": "poga@example.com", "password": "pogapoga"},
    )
    client.post(
        "/users/",
        json={"email": "hoge@example.com", "password": "hogehoge"},
    )
    response = client.post(
        "/users/",
        json={"email": "fuga@example.com", "password": "fugafuga"},
    )

    # 削除対象のユーザIDを保持
    data = response.json()
    user, token = data["user"], data["token"]
    user_id = user["id"]
    test_item_count = 3
    test_item_ids = []

    # テスト用のitem作成
    for i in range(test_item_count):
        response = client.post(
            "/users/" + str(user_id) + "/items/",
            json={
                "title": "title" + str(i),
                "description": "description" + str(i),
            }
        )

        data = response.json()
        test_item_ids.append(data["id"])

    # ユーザ削除の処理が正常終了しているか確認
    response = client.delete(
        "/users/" + str(user_id) + "/delete/",
    )
    assert response.status_code == 200, response.text

    # 削除されたユーザが正しいか確認
    data = response.json()
    assert data["delete_user_id"] == user_id

    # 削除されたユーザが無効化されているのを確認
    response = client.get(
        "/users/" + str(user_id) + "/"
    )
    user_data = response.json()
    assert not user_data["is_active"]

    # Item引継ぎ先のユーザIDが正しいか確認
    response = client.get(
        "/users/"
    )
    users = response.json()
    min_user_id = None
    for user in users:
        if user["is_active"] and (min_user_id is None or user["id"] < min_user_id):
            min_user_id = user["id"]

    assert data["takeovered_user_id"] == min_user_id

    # Itemの引継ぎ先が正しいか確認
    response = client.get(
        "/items/"
    )
    items = response.json()
    for item in items:
        if item["id"] in test_item_ids:
            assert item["owner_id"] == min_user_id