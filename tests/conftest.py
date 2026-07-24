"""pytest 基架 fixtures。

设计目标（服务于接口级 e2e 一等公民）：
- app / client：TestingConfig（内存 SQLite），每个测试独立 create_all/drop_all，
  用例间自动重置、互不污染。
- 工厂 helper：make_user / auth_headers / admin_headers，用真实 core.security 造 token。
- e2e 便捷入口：user_client / admin_client 返回 (client, headers)，测试直接用
  真实 Authorization 头打真实端点，请求穿透 resources->schemas->service->models。
"""
import uuid

import pytest

from ezgym import create_app
from ezgym.core.database import db as _db
from ezgym.core.security import Permission, create_token, hash_password


@pytest.fixture()
def app():
    """每个测试一个全新 app + 全新内存库；结束 drop_all，保证用例间隔离。"""
    app = create_app("testing")
    with app.app_context():
        _db.create_all()
        try:
            yield app
        finally:
            _db.session.remove()
            _db.drop_all()
            # 释放连接，避免内存 SQLite 连接在 GC 时报 ResourceWarning
            _db.engine.dispose()


@pytest.fixture()
def client(app):
    return app.test_client()


@pytest.fixture()
def session(app):
    """db.session，供 service 层单测直接操作。"""
    return _db.session


@pytest.fixture()
def make_user(app):
    """工厂：造并入库一个 User(+UserInfo)，返回该 User。

    用法：user = make_user()  或  admin = make_user(admin=True)
    每次调用生成唯一 account/number，避免唯一约束冲突。
    """
    from ezgym.domains.identity.models import User, UserInfo

    def _make(account: str | None = None, password: str = "pass1234",
              admin: bool = False, nick_name: str | None = None) -> User:
        suffix = uuid.uuid4().hex[:8]
        account = account or f"u_{suffix}"
        user = User(
            account=account,
            password_hash=hash_password(password),
            permission=int(Permission.ADMIN if admin else Permission.NORMAL),
            number=uuid.uuid4().hex[:20],
        )
        user.info = UserInfo(nick_name=nick_name or account)
        _db.session.add(user)
        _db.session.commit()
        return user

    return _make


@pytest.fixture()
def auth_headers(app):
    """把 User 转成带真实 JWT 的请求头。用法：auth_headers(user)。"""
    def _headers(user) -> dict:
        token = create_token(user)
        return {"Authorization": f"Bearer {token}"}

    return _headers


@pytest.fixture()
def admin_headers(make_user, auth_headers):
    """现成的 admin 请求头。"""
    admin = make_user(admin=True)
    return auth_headers(admin)


@pytest.fixture()
def user_client(client, make_user, auth_headers):
    """e2e 便捷入口：返回 (client, headers)，headers 带普通用户真实 JWT。"""
    user = make_user()
    return client, auth_headers(user)


@pytest.fixture()
def admin_client(client, make_user, auth_headers):
    """e2e 便捷入口：返回 (client, headers)，headers 带 admin 真实 JWT。"""
    admin = make_user(admin=True)
    return client, auth_headers(admin)
