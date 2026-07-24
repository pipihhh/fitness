"""地基冒烟测试。

覆盖：app 工厂、健康检查 e2e（纯 API 层样例）、建表、密码哈希往返、
JWT 签发+解码含 permission、验证码生成。
"""
from ezgym import create_app
from ezgym.core.database import db
from ezgym.core.security import (
    Permission,
    create_token,
    hash_password,
    verify_password,
)


def test_create_app_testing():
    app = create_app("testing")
    assert app is not None
    assert app.config["TESTING"] is True
    assert app.config["SQLALCHEMY_DATABASE_URI"] == "sqlite:///:memory:"


def test_health_endpoint_e2e(client):
    """纯 API 层 e2e 样例：打真实端点，断言 HTTP status + {errno,code,data} 契约。"""
    resp = client.get("/api/health")
    assert resp.status_code == 200
    body = resp.get_json()
    assert body["errno"] == 0
    assert body["code"] == 200
    assert body["data"]["status"] == "ok"


def test_all_tables_created(app):
    """create_all 后核心表都存在。"""
    table_names = set(db.metadata.tables.keys())
    expected = {
        "user", "user_info", "course", "course_action", "course_collection",
        "challenge", "blog", "like", "comment", "reply", "follow", "file_map",
    }
    assert expected.issubset(table_names)
    # 反射真实建出来的表
    inspector = db.inspect(db.engine)
    created = set(inspector.get_table_names())
    assert expected.issubset(created)


def test_password_hash_roundtrip(app):
    hashed = hash_password("s3cret!")
    assert hashed != "s3cret!"
    assert verify_password("s3cret!", hashed) is True
    assert verify_password("wrong", hashed) is False


def test_jwt_token_carries_permission(app):
    from flask_jwt_extended import decode_token

    from ezgym.domains.identity.models import User

    user = User(id=42, account="a", password_hash="x",
                permission=int(Permission.ADMIN), number="n42")
    token = create_token(user)
    decoded = decode_token(token)
    assert decoded["sub"] == "42"
    assert decoded["permission"] == int(Permission.ADMIN)


def test_captcha_generate(app):
    from ezgym.core.captcha import generate

    text, png = generate()
    assert isinstance(text, str) and len(text) > 0
    assert isinstance(png, bytes) and len(png) > 0
    assert png[:8] == b"\x89PNG\r\n\x1a\n"  # PNG 魔数


def test_admin_headers_reach_protected_pattern(app, make_user, auth_headers):
    """验证 make_user + auth_headers 能造出带真实 JWT 的头（e2e 前置能力）。"""
    admin = make_user(admin=True)
    headers = auth_headers(admin)
    assert headers["Authorization"].startswith("Bearer ")
