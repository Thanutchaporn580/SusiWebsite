from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship
from sqlalchemy.sql import func
from sqlalchemy_serializer import SerializerMixin
from sqlalchemy.ext.hybrid import hybrid_property
from flask_bcrypt import Bcrypt
from flask_login import UserMixin
import sqlalchemy as sa
from acl import init_acl
from itsdangerous import URLSafeTimedSerializer as Serializer
from flask import current_app
from werkzeug.security import generate_password_hash, check_password_hash

# สร้าง instance ของ SQLAlchemy
bcrypt = Bcrypt()


class Base(DeclarativeBase):
    pass


db = SQLAlchemy(model_class=Base)


def init_app(app):
    db.init_app(app)
    bcrypt.init_app(app)
    init_acl(app)
    with app.app_context():
        db.create_all()
        db.reflect()


# ตารางกลางสำหรับความสัมพันธ์ Many-to-Many ระหว่าง Note และ Tag
note_tag_m2m = db.Table(
    "note_tag",
    sa.Column("note_id", sa.ForeignKey("notes.id"), primary_key=True),
    sa.Column("tag_id", sa.ForeignKey("tags.id"), primary_key=True),
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
    username = db.Column(db.String(150), unique=True, nullable=False)
    email = db.Column(db.String(150), unique=True, nullable=False)
    name = db.Column(db.String(150))
    status = db.Column(db.String(50), default="active")
    password_hash = db.Column(db.String(150), nullable=False)
    created_date = db.Column(db.DateTime, default=db.func.current_timestamp())
    updated_date = db.Column(db.DateTime, default=db.func.current_timestamp(), onupdate=db.func.current_timestamp())

    roles: Mapped[list[Role]] = relationship("Role", secondary="user_roles")

    # Password hash management
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def authenticate(self, password):
        try:
            return bcrypt.check_password_hash(self.password_hash, password.encode("utf-8"))
        except Exception as e:
        # Log the error or handle it appropriately
            return False

    def has_role(self, role_name):
        return any(role.name == role_name for role in self.roles)

    def get_reset_password_token(self, expires_in=600):
        s = Serializer(current_app.config['SECRET_KEY'])
        return s.dumps({'user_id': self.id}, salt='password-reset-salt')

    @staticmethod
    def verify_reset_password_token(token):
        s = Serializer(current_app.config['SECRET_KEY'])
        try:
            user_id = s.loads(token, salt='password-reset-salt', max_age=600)['user_id']
        except:
            return None
        return User.query.get(user_id)


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


# ตารางกลางสำหรับการเชื่อมโยงผู้ใช้และบทบาท
user_roles = db.Table(
    "user_roles",
    db.Model.metadata,
    sa.Column("user_id", sa.ForeignKey("users.id"), primary_key=True),
    sa.Column("role_id", sa.ForeignKey("roles.id"), primary_key=True),
)


class Upload(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    filename = db.Column(db.String)
    data = db.Column(db.LargeBinary)
    created_date = mapped_column(sa.DateTime(timezone=True), server_default=func.now())
    updated_date = mapped_column(sa.DateTime(timezone=True), server_default=func.now())
