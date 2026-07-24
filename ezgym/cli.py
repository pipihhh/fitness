"""click CLI 命令（替代废弃的 flask_script/manage.py）。

- flask init-db：create_all 建表（无迁移时快速起库）。
- flask seed：造演示种子数据（admin + 普通用户 + 课程/挑战/动态）。
"""
import uuid
from datetime import datetime, timedelta

import click
from flask import Flask

from ezgym.core.database import db
from ezgym.core.security import Permission, hash_password

__all__ = ["register_cli"]


def _new_number() -> str:
    return uuid.uuid4().hex[:20]


def register_cli(app: Flask) -> None:
    @app.cli.command("init-db")
    def init_db():
        """create_all 建表。"""
        db.create_all()
        click.echo("init-db: 所有表已创建。")

    @app.cli.command("seed")
    def seed():
        """造演示种子数据（幂等：已存在 admin 则跳过）。"""
        from ezgym.domains.challenge.models import Challenge
        from ezgym.domains.content.models import Blog
        from ezgym.domains.course.models import Course, CourseAction
        from ezgym.domains.identity.models import User, UserInfo

        db.create_all()

        if User.query.filter_by(account="admin").first():
            click.echo("seed: admin 已存在，跳过。")
            return

        # 管理员
        admin = User(
            account="admin",
            password_hash=hash_password("admin123"),
            permission=int(Permission.ADMIN),
            number=_new_number(),
        )
        admin.info = UserInfo(nick_name="管理员", email="admin@ezgym.local", gender=1)
        db.session.add(admin)

        # 普通用户
        normal_users = []
        for i in range(1, 4):
            u = User(
                account=f"user{i}",
                password_hash=hash_password(f"user{i}pass"),
                permission=int(Permission.NORMAL),
                number=_new_number(),
            )
            u.info = UserInfo(nick_name=f"健身达人{i}", gender=(i % 2) + 1, age=20 + i)
            normal_users.append(u)
            db.session.add(u)
        db.session.flush()  # 拿到 id

        # 课程 + 动作
        courses = [
            Course(type="力量", name="新手全身训练", level="初级", burning=300),
            Course(type="有氧", name="燃脂 HIIT", level="中级", burning=450),
        ]
        db.session.add_all(courses)
        db.session.flush()
        db.session.add_all([
            CourseAction(course_id=courses[0].id, content="深蹲 x15", sequence=1),
            CourseAction(course_id=courses[0].id, content="俯卧撑 x12", sequence=2),
            CourseAction(course_id=courses[1].id, content="开合跳 30s", sequence=1),
        ])

        # 挑战
        now = datetime.utcnow()
        db.session.add_all([
            Challenge(
                content="30 天平板支撑挑战", picture="/media/images/plank.jpg",
                start_time=now, end_time=now + timedelta(days=30),
                pageviews=0, number=_new_number(),
            ),
        ])

        # 动态
        db.session.add_all([
            Blog(
                user_id=normal_users[0].id, title="今天练腿",
                content="腿快废了，但很爽！", like_count=0,
            ),
            Blog(
                user_id=normal_users[1].id, title="打卡第一天",
                content="加入健身论坛，冲！", like_count=0,
            ),
        ])

        db.session.commit()
        click.echo(
            "seed: 完成。admin/admin123，user1/user1pass ... 已创建课程/挑战/动态。"
        )
