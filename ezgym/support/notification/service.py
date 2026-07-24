"""notification 域 service：邮件发送（找回密码）。

设计要点（对应 CR #9 修复）：
- **惰性建立 SMTP 连接**：import / 模块加载 / 函数调用本身都不建立连接；
  仅在真正投递（worker 内）时才 connect + login + send + quit。
- **后台线程发送**：默认异步投递，不阻塞请求线程；发送失败只记
  ``logger`` 日志并返回 False，绝不向上抛致命异常（避免像旧代码那样让
  连"发信"都不做的请求也 500）。
- **线程安全**：不使用可变类/模块变量缓存连接；每次投递用局部连接对象，
  配置值在请求线程内快照后按值传入 worker（worker 内没有 app context）。
"""
import smtplib
import threading
from email.header import Header
from email.mime.text import MIMEText
from email.utils import formataddr

from flask import current_app

__all__ = ["send_password_reset_email"]

# SMTP 握手/收发超时（秒），避免 worker 线程在网络异常时长期挂起。
_SMTP_TIMEOUT = 10

# 最近一次异步投递线程的引用，仅供测试同步（join）用；生产逻辑不依赖它。
_last_delivery_thread: threading.Thread | None = None


def send_password_reset_email(email: str, reset_link: str | None = None) -> bool:
    """发送找回密码邮件。

    :param email: 收件人邮箱
    :param reset_link: 完整的重置链接（含 token）。identity 域应传入带 token 的
        真实链接；缺省时回退为基于 ``USER_HOST`` 的占位链接（notification 域
        不负责签发 token）。
    :return: 异步模式下返回是否成功派发投递任务；同步模式（``MAIL_ASYNC=False``）
        下返回实际投递结果。任何情况下都不抛致命异常。

    注意：不在此函数（更不在 import）阶段建立任何 SMTP 连接。
    """
    global _last_delivery_thread

    logger = current_app.logger

    if not email:
        logger.warning("send_password_reset_email 收到空邮箱，跳过发送")
        return False

    cfg = current_app.config

    server = cfg.get("MAIL_SERVER")
    username = cfg.get("MAIL_USERNAME")
    password = cfg.get("MAIL_PASSWORD")
    sender = cfg.get("MAIL_SENDER") or username

    # 关键配置缺失时不派发，记日志并返回 False（惰性、不抛异常）。
    if not (server and username and password and sender):
        logger.warning(
            "邮件配置不完整（MAIL_SERVER/MAIL_USERNAME/MAIL_PASSWORD/MAIL_SENDER），"
            "跳过发送找回密码邮件到 %s",
            email,
        )
        return False

    if reset_link is None:
        user_host = cfg.get("USER_HOST", "")
        reset_link = f"{user_host}/password-reset?email={email}"

    snapshot = {
        "server": server,
        "port": int(cfg.get("MAIL_PORT", 465)),
        "use_ssl": bool(cfg.get("MAIL_USE_SSL", True)),
        "username": username,
        "password": password,
        "sender": sender,
        "title": cfg.get("MAIL_TITLE", "找回密码"),
    }

    message = _build_message(snapshot["sender"], snapshot["title"], email, reset_link)

    # MAIL_ASYNC 为可注入开关（默认 True，异步）；测试可置 False 走同步以断言返回值。
    run_async = bool(cfg.get("MAIL_ASYNC", True))

    if not run_async:
        return _deliver(snapshot, message, email, logger)

    thread = threading.Thread(
        target=_deliver,
        args=(snapshot, message, email, logger),
        name="password-reset-email",
        daemon=True,
    )
    thread.start()
    _last_delivery_thread = thread
    return True


def _build_message(sender: str, title: str, receiver: str, reset_link: str) -> MIMEText:
    """构造找回密码 HTML 邮件（沿用 conf/email_template.html 语义：正文含重置 URL）。"""
    html = (
        "<div>"
        "<p>您好，</p>"
        "<p>您正在申请找回 ezgym 论坛账号的密码，请点击下方链接重置密码：</p>"
        f'<p><a href="{reset_link}">{reset_link}</a></p>'
        "<p>若非本人操作，请忽略本邮件。</p>"
        "</div>"
    )
    message = MIMEText(html, "html", "utf-8")
    message["Subject"] = Header(title, "utf-8")
    message["From"] = formataddr((str(Header("ezgym", "utf-8")), sender))
    message["To"] = receiver
    return message


def _deliver(snapshot: dict, message: MIMEText, receiver: str, logger) -> bool:
    """真正建立 SMTP 连接并投递（惰性、局部连接、无共享状态）。

    在后台线程内执行；此处没有 Flask app context，只用传入的快照与 logger。
    发送失败记日志、返回 False，不抛异常。
    """
    smtp = None
    try:
        if snapshot["use_ssl"]:
            smtp = smtplib.SMTP_SSL(
                snapshot["server"], snapshot["port"], timeout=_SMTP_TIMEOUT
            )
        else:
            smtp = smtplib.SMTP(
                snapshot["server"], snapshot["port"], timeout=_SMTP_TIMEOUT
            )
        smtp.login(snapshot["username"], snapshot["password"])
        smtp.sendmail(snapshot["sender"], [receiver], message.as_string())
        logger.info("找回密码邮件已发送至 %s", receiver)
        return True
    except Exception as exc:  # noqa: BLE001 - 发信失败不得致命
        logger.error("发送找回密码邮件到 %s 失败: %s", receiver, exc)
        return False
    finally:
        if smtp is not None:
            try:
                smtp.quit()
            except Exception:  # noqa: BLE001 - 关闭失败忽略
                pass
