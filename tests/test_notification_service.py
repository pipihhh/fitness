"""notification 域 service 单测（不真发信）。

覆盖：
- import 阶段无任何 SMTP 副作用（修 CR #9：不在 import/实例化时连接）。
- 后台线程内尝试连接 + 登录 + 发送各一次（异步默认路径）。
- SMTP 抛异常时函数不抛、返回 False、并记 error 日志（同步路径便于断言）。
- 关键配置缺失时不发送、返回 False。
- 空邮箱直接返回 False。
"""
import importlib
import logging
import smtplib

import pytest

from ezgym.support.notification import service as notification_service


class FakeSMTP:
    """记录调用序列的假 SMTP 客户端；构造即连接（模拟真实 SMTP_SSL 语义）。"""

    instances = []

    def __init__(self, host=None, port=None, timeout=None):
        self.host = host
        self.port = port
        self.timeout = timeout
        self.logged_in = False
        self.sent = []
        self.quit_called = False
        FakeSMTP.instances.append(self)

    def login(self, username, password):
        self.logged_in = True
        self.username = username

    def sendmail(self, sender, receivers, msg):
        self.sent.append((sender, tuple(receivers), msg))

    def quit(self):
        self.quit_called = True


@pytest.fixture(autouse=True)
def _reset_fake():
    FakeSMTP.instances = []
    yield


def _configure_mail(app):
    app.config.update(
        MAIL_SERVER="smtp.example.com",
        MAIL_PORT=465,
        MAIL_USE_SSL=True,
        MAIL_USERNAME="bot@example.com",
        MAIL_PASSWORD="secret",
        MAIL_SENDER="bot@example.com",
    )


def test_import_has_no_smtp_side_effect(monkeypatch):
    """import notification.service 不得建立任何 SMTP 连接（CR #9）。"""
    calls = []

    def _boom(*args, **kwargs):
        calls.append(args)
        raise AssertionError("import 阶段不应建立 SMTP 连接")

    monkeypatch.setattr(smtplib, "SMTP_SSL", _boom)
    monkeypatch.setattr(smtplib, "SMTP", _boom)

    importlib.reload(notification_service)

    assert calls == []


def test_send_in_background_thread_connects_logs_in_and_sends_once(app, monkeypatch):
    """异步默认路径：后台线程内连接 + 登录 + 发送各一次。"""
    _configure_mail(app)
    monkeypatch.setattr(smtplib, "SMTP_SSL", FakeSMTP)

    with app.app_context():
        result = notification_service.send_password_reset_email(
            "user@example.com", reset_link="https://x/reset?token=abc"
        )
        # 异步派发成功返回 True
        assert result is True
        # 等待后台线程完成后断言
        thread = notification_service._last_delivery_thread
        assert thread is not None
        thread.join(timeout=5)
        assert not thread.is_alive()

    assert len(FakeSMTP.instances) == 1
    smtp = FakeSMTP.instances[0]
    assert smtp.host == "smtp.example.com"
    assert smtp.port == 465
    assert smtp.logged_in is True
    assert len(smtp.sent) == 1
    sender, receivers, _ = smtp.sent[0]
    assert receivers == ("user@example.com",)
    assert smtp.quit_called is True


def test_smtp_failure_returns_false_and_logs(app, monkeypatch, caplog):
    """SMTP 抛异常时：函数不抛、返回 False、记 error 日志（同步路径断言）。"""
    _configure_mail(app)
    app.config["MAIL_ASYNC"] = False  # 同步执行以便直接断言返回值

    def _raise(*args, **kwargs):
        raise smtplib.SMTPException("boom")

    monkeypatch.setattr(smtplib, "SMTP_SSL", _raise)

    with app.app_context():
        with caplog.at_level(logging.ERROR):
            result = notification_service.send_password_reset_email("user@example.com")

    assert result is False
    assert any("失败" in rec.message or "boom" in rec.getMessage() for rec in caplog.records)


def test_login_failure_returns_false(app, monkeypatch):
    """登录失败也应被捕获：返回 False、不抛。"""
    _configure_mail(app)
    app.config["MAIL_ASYNC"] = False

    class LoginFailSMTP(FakeSMTP):
        def login(self, username, password):
            raise smtplib.SMTPAuthenticationError(535, b"auth failed")

    monkeypatch.setattr(smtplib, "SMTP_SSL", LoginFailSMTP)

    with app.app_context():
        result = notification_service.send_password_reset_email("user@example.com")

    assert result is False


def test_sync_success_returns_true(app, monkeypatch):
    """同步路径成功时返回 True，并完成连接/登录/发送/退出。"""
    _configure_mail(app)
    app.config["MAIL_ASYNC"] = False
    monkeypatch.setattr(smtplib, "SMTP_SSL", FakeSMTP)

    with app.app_context():
        result = notification_service.send_password_reset_email("user@example.com")

    assert result is True
    assert len(FakeSMTP.instances) == 1
    assert FakeSMTP.instances[0].logged_in is True
    assert FakeSMTP.instances[0].quit_called is True


def test_missing_config_returns_false_without_connecting(app, monkeypatch):
    """关键邮件配置缺失时：不建立连接、返回 False。"""
    app.config.update(
        MAIL_SERVER="smtp.example.com",
        MAIL_USERNAME="",
        MAIL_PASSWORD="",
        MAIL_SENDER="",
    )
    monkeypatch.setattr(smtplib, "SMTP_SSL", FakeSMTP)

    with app.app_context():
        result = notification_service.send_password_reset_email("user@example.com")

    assert result is False
    assert FakeSMTP.instances == []


def test_empty_email_returns_false(app):
    """空邮箱直接返回 False。"""
    _configure_mail(app)
    with app.app_context():
        assert notification_service.send_password_reset_email("") is False


def test_non_ssl_uses_plain_smtp(app, monkeypatch):
    """MAIL_USE_SSL=False 时使用普通 SMTP。"""
    _configure_mail(app)
    app.config["MAIL_USE_SSL"] = False
    app.config["MAIL_ASYNC"] = False
    monkeypatch.setattr(smtplib, "SMTP", FakeSMTP)

    with app.app_context():
        result = notification_service.send_password_reset_email("user@example.com")

    assert result is True
    assert len(FakeSMTP.instances) == 1
