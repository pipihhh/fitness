"""course 域 e2e：打真实端点，断言 HTTP status + {errno, code, data} 契约。

覆盖：鉴权（未登录 401 / NORMAL 建课 403 / ADMIN 成功）、建课字段完整回读（修 CR #4）、
name 冲突 409、软登录列表、公开动作列表、sequence 冲突 409、收藏与取消、
删除动作返回明确 data（修 CR #26）。
"""


def _assert_contract(body, expected_code):
    assert set(body.keys()) == {"errno", "code", "data"}
    assert body["errno"] == 0
    assert body["code"] == expected_code


def _create_course(client, headers, name="课程X", type="有氧", level="初级", burning=200):
    return client.post("/api/courses", json={
        "name": name, "type": type, "level": level, "burning": burning,
    }, headers=headers)


# ---------- 鉴权 ----------
def test_normal_user_cannot_create_course(user_client):
    client, headers = user_client
    resp = _create_course(client, headers)
    assert resp.status_code == 403
    assert resp.get_json()["errno"] == 1


def test_get_course_requires_login(client, admin_client):
    admin, admin_headers = admin_client
    created = _create_course(admin, admin_headers, name="需登录课")
    course_id = created.get_json()["data"]["id"]
    resp = client.get(f"/api/courses/{course_id}")
    assert resp.status_code == 401


# ---------- 建课（修 CR #4 回归）----------
def test_admin_create_course_success_and_readback(admin_client):
    client, headers = admin_client
    resp = _create_course(client, headers, name="燃脂课", type="有氧",
                          level="高级", burning=450)
    assert resp.status_code == 201
    body = resp.get_json()
    _assert_contract(body, 201)
    data = body["data"]
    assert data["name"] == "燃脂课"
    assert data["type"] == "有氧"
    assert data["level"] == "高级"
    assert data["burning"] == 450

    # 回读所有字段（#4 回归）
    read = client.get(f"/api/courses/{data['id']}", headers=headers)
    assert read.status_code == 200
    read_data = read.get_json()["data"]
    assert read_data["name"] == "燃脂课"
    assert read_data["type"] == "有氧"
    assert read_data["level"] == "高级"
    assert read_data["burning"] == 450


def test_create_course_duplicate_name_conflict(admin_client):
    client, headers = admin_client
    _create_course(client, headers, name="重复名课")
    resp = _create_course(client, headers, name="重复名课")
    assert resp.status_code == 409
    assert resp.get_json()["errno"] == 1


def test_create_course_validation_error(admin_client):
    client, headers = admin_client
    resp = client.post("/api/courses", json={"type": "有氧"}, headers=headers)
    assert resp.status_code == 400
    assert resp.get_json()["errno"] == 1


# ---------- 软登录列表 ----------
def test_list_courses_soft_login(client, admin_client, user_client):
    admin, admin_headers = admin_client
    _create_course(admin, admin_headers, name="列表课")

    # 匿名访问：200，不带 is_collected
    anon = client.get("/api/courses")
    assert anon.status_code == 200
    body = anon.get_json()
    _assert_contract(body, 200)
    assert isinstance(body["data"]["items"], list)
    assert "is_collected" not in body["data"]["items"][0]

    # 登录访问：带 is_collected
    user, user_headers = user_client
    logged = client.get("/api/courses", headers=user_headers)
    assert logged.status_code == 200
    assert "is_collected" in logged.get_json()["data"]["items"][0]


# ---------- 动作 ----------
def test_actions_list_public_and_sequence_conflict(admin_client, client):
    admin, headers = admin_client
    course_id = _create_course(admin, headers, name="动作课").get_json()["data"]["id"]

    r1 = admin.post(f"/api/courses/{course_id}/actions", json={
        "content": "深蹲", "picture": "/media/images/a.jpg", "sequence": 1,
    }, headers=headers)
    assert r1.status_code == 201

    # sequence 重复 -> 409
    r2 = admin.post(f"/api/courses/{course_id}/actions", json={
        "content": "俯卧撑", "picture": None, "sequence": 1,
    }, headers=headers)
    assert r2.status_code == 409

    # 公开列表
    listed = client.get(f"/api/courses/{course_id}/actions")
    assert listed.status_code == 200
    data = listed.get_json()["data"]
    assert data["course"]["id"] == course_id
    assert len(data["actions"]) == 1


def test_delete_action_returns_data(admin_client):
    """修 CR #26：删除动作成功要返回明确 data。"""
    client, headers = admin_client
    course_id = _create_course(client, headers, name="删动作课").get_json()["data"]["id"]
    action_id = client.post(f"/api/courses/{course_id}/actions", json={
        "content": "平板", "picture": None, "sequence": 1,
    }, headers=headers).get_json()["data"]["id"]

    resp = client.delete(f"/api/actions/{action_id}", headers=headers)
    assert resp.status_code == 200
    body = resp.get_json()
    _assert_contract(body, 200)
    assert body["data"] is not None
    assert body["data"]["id"] == action_id
    assert body["data"]["deleted"] is True


# ---------- 收藏 ----------
def test_collect_and_uncollect(admin_client, user_client):
    admin, admin_headers = admin_client
    course_id = _create_course(admin, admin_headers, name="收藏课").get_json()["data"]["id"]

    user, user_headers = user_client
    created = user.post("/api/collections", json={"course_id": course_id},
                        headers=user_headers)
    assert created.status_code == 201
    body = created.get_json()
    _assert_contract(body, 201)
    collection_id = body["data"]["id"]
    assert body["data"]["course_id"] == course_id

    removed = user.delete(f"/api/collections/{collection_id}", headers=user_headers)
    assert removed.status_code == 200
    _assert_contract(removed.get_json(), 200)
    assert removed.get_json()["data"]["deleted"] is True


def test_collect_requires_login(client, admin_client):
    admin, admin_headers = admin_client
    course_id = _create_course(admin, admin_headers, name="需登录收藏").get_json()["data"]["id"]
    resp = client.post("/api/collections", json={"course_id": course_id})
    assert resp.status_code == 401
