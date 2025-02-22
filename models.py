from flask import Flask, current_app
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship
from sqlalchemy.sql import func
from sqlalchemy_serializer import SerializerMixin
from sqlalchemy.ext.hybrid import hybrid_property
from flask_bcrypt import Bcrypt
from flask_login import UserMixin
import sqlalchemy as sa
from acl import init_acl
from werkzeug.security import generate_password_hash, check_password_hash

# สร้าง instance ของ SQLAlchemy และ Bcrypt
bcrypt = Bcrypt()

db = SQLAlchemy()

def init_app(app):
    db.init_app(app)
    init_acl(app)
    with app.app_context():
        db.create_all()

# ตารางกลางสำหรับความสัมพันธ์ Many-to-Many ระหว่าง Note และ Tag
note_tag_m2m = sa.Table(
    "note_tag",
    db.metadata,
    sa.Column("note_id", sa.ForeignKey("notes.id"), primary_key=True),
    sa.Column("tag_id", sa.ForeignKey("tags.id"), primary_key=True),
)

# ตารางกลางสำหรับความสัมพันธ์ Many-to-Many ระหว่าง User และ Role
user_roles = sa.Table(
    "user_roles",
    db.metadata,
    sa.Column("user_id", sa.ForeignKey("users.id"), primary_key=True),
    sa.Column("role_id", sa.ForeignKey("roles.id"), primary_key=True),
)

# โมเดล Role
class Role(db.Model):
    __tablename__ = "roles"
    id: Mapped[int] = mapped_column(sa.Integer, primary_key=True)
    name: Mapped[str] = mapped_column(sa.String, nullable=False, default="user")
    created_date = mapped_column(sa.DateTime(timezone=True), server_default=func.now())

# โมเดล User
class User(db.Model, UserMixin):
    __tablename__ = "users"
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String, unique=True, nullable=False)
    name = db.Column(db.String)
    status = db.Column(db.String, default="active")
    _password_hash = db.Column(db.String, nullable=False)
    created_date = mapped_column(sa.DateTime(timezone=True), server_default=func.now())
    updated_date = mapped_column(sa.DateTime(timezone=True), server_default=func.now())

    roles: Mapped[list[Role]] = relationship("Role", secondary=user_roles)

    # ตั้งค่ารหัสผ่าน
    def set_password(self, password):
        self._password_hash = bcrypt.generate_password_hash(password).decode('utf-8')

    # ตรวจสอบรหัสผ่าน
    def check_password(self, password):
        return bcrypt.check_password_hash(self._password_hash, password)

    # ตรวจสอบว่าผู้ใช้มีบทบาทหรือไม่
    def has_role(self, role_name):
        return any(role.name == role_name for role in self.roles)

# โมเดล Tag
class Tag(db.Model):
    __tablename__ = "tags"
    id: Mapped[int] = mapped_column(sa.Integer, primary_key=True)
    name: Mapped[str] = mapped_column(sa.String, nullable=False)
    created_date = mapped_column(sa.DateTime(timezone=True), server_default=func.now())

# โมเดล Note
class Note(db.Model):
    __tablename__ = "notes"
    id: Mapped[int] = mapped_column(sa.Integer, primary_key=True)
    title: Mapped[str] = mapped_column(sa.String, nullable=False)
    description: Mapped[str] = mapped_column(sa.Text)
    tags: Mapped[list[Tag]] = relationship(secondary=note_tag_m2m)
    created_date = mapped_column(sa.DateTime(timezone=True), server_default=func.now())
    updated_date = mapped_column(
        sa.DateTime(timezone=True),
        server_default=func.now(),
        server_onupdate=func.now(),
    )

# โมเดล Upload
class Upload(db.Model):
    __tablename__ = "uploads"
    id = db.Column(db.Integer, primary_key=True)
    filename = db.Column(db.String)
    data = db.Column(db.LargeBinary)
    created_date = mapped_column(sa.DateTime(timezone=True), server_default=func.now())
    updated_date = mapped_column(sa.DateTime(timezone=True), server_default=func.now())
