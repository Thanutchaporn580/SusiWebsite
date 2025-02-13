from flask import redirect, url_for, request, session, render_template
from flask_login import current_user, LoginManager, login_required, logout_user
from werkzeug.exceptions import Forbidden, Unauthorized
import models
from functools import wraps

# สร้าง LoginManager
login_manager = LoginManager()


# กำหนดการตั้งค่า login_manager
def init_acl(app):
    login_manager.init_app(app)

    # โหลดผู้ใช้จาก ID
    @login_manager.user_loader
    def load_user(user_id):
        return models.User.query.get(int(user_id))  # กำหนดการโหลดผู้ใช้จาก ID

    # กำหนดเส้นทางหน้าเข้าสู่ระบบ
    login_manager.login_view = "login"  # กำหนด URL สำหรับหน้า login


# ฟังก์ชันตรวจสอบสิทธิ์การเข้าถึงตามบทบาท
def roles_required(*roles):
    def wrapper(func):
        @wraps(func)
        def wrapped(*args, **kwargs):
            if not current_user.is_authenticated:
                raise Unauthorized("You must be logged in to access this resource.")

            # ตรวจสอบบทบาทของผู้ใช้
            user_roles = {role.name for role in current_user.roles}
            if any(role in user_roles for role in roles):
                return func(*args, **kwargs)

            # หากไม่มีบทบาทที่ตรงกัน
            raise Forbidden("You do not have permission to access this resource.")

        return wrapped

    return wrapper
