"""course 域模型：Course + CourseAction + CourseCollection。"""
from sqlalchemy import ForeignKey, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from ezgym.core.database import PkMixin, SoftDeleteMixin, TimestampMixin, db

__all__ = ["Course", "CourseAction", "CourseCollection"]


class Course(PkMixin, TimestampMixin, SoftDeleteMixin, db.Model):
    """课程。name 唯一。"""

    __tablename__ = "course"

    type: Mapped[str | None] = mapped_column(String(64))
    name: Mapped[str] = mapped_column(String(128), unique=True, nullable=False)
    level: Mapped[str | None] = mapped_column(String(32))
    burning: Mapped[int | None] = mapped_column(Integer)

    actions: Mapped[list["CourseAction"]] = relationship(
        back_populates="course", cascade="all, delete-orphan"
    )


class CourseAction(PkMixin, TimestampMixin, SoftDeleteMixin, db.Model):
    """课程动作。补软删（原表硬删）。sequence 在课程内排序。"""

    __tablename__ = "course_action"

    course_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("course.id"), nullable=False
    )
    content: Mapped[str | None] = mapped_column(Text)
    picture: Mapped[str | None] = mapped_column(String(255))
    sequence: Mapped[int | None] = mapped_column(Integer)

    course: Mapped["Course"] = relationship(back_populates="actions")


class CourseCollection(PkMixin, TimestampMixin, SoftDeleteMixin, db.Model):
    """用户收藏课程。(user_id, course_id) 唯一。"""

    __tablename__ = "course_collection"
    __table_args__ = (
        UniqueConstraint("user_id", "course_id", name="uq_collection_user_course"),
    )

    user_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("user.id"), nullable=False
    )
    course_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("course.id"), nullable=False
    )
