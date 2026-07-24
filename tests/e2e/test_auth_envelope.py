"""跨域鉴权响应契约：JWT 鉴权失败也必须走统一 {errno,code,data} 信封。

覆盖 core.security.register_jwt_error_handlers（缺失/无效 token → 401 + 契约 body）。
"""


def _assert_envelope(body):
    assert set(body.keys()) == {"errno", "code", "data"}


def test_missing_token_returns_contract_envelope_401(client):
    """无 Authorization 头访问需登录端点：401 且 body 是契约信封（非 flask-jwt 默认 {msg}）。"""
    resp = client.put("/api/users/me", json={"nick_name": "x"})
    assert resp.status_code == 401
    body = resp.get_json()
    _assert_envelope(body)
    assert body["errno"] == 1
    assert body["code"] == 401
    assert "msg" not in body  # 不再是 flask-jwt-extended 默认信封


def test_invalid_token_returns_contract_envelope_401(client):
    """伪造 token：401 且契约信封。"""
    resp = client.put(
        "/api/users/me",
        json={"nick_name": "x"},
        headers={"Authorization": "Bearer not-a-real-token"},
    )
    assert resp.status_code == 401
    body = resp.get_json()
    _assert_envelope(body)
    assert body["errno"] == 1
