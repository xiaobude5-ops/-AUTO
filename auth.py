"""认证模块 — 密码哈希 + 登录 + 权限装饰器"""
from functools import wraps
from flask import session, redirect, url_for, flash, jsonify

from werkzeug.security import generate_password_hash, check_password_hash


def hash_password(password: str) -> str:
    return generate_password_hash(password)


def verify_password(password: str, password_hash: str) -> bool:
    return check_password_hash(password_hash, password)


def login_required(f):
    """要求登录的装饰器（页面路由用）"""

    @wraps(f)
    def decorated(*args, **kwargs):
        if "user_id" not in session:
            return redirect(url_for("login"))
        return f(*args, **kwargs)

    return decorated


def api_login_required(f):
    """要求登录的装饰器（API 路由用）"""

    @wraps(f)
    def decorated(*args, **kwargs):
        if "user_id" not in session:
            return jsonify({"success": False, "error": "请先登录"}), 401
        return f(*args, **kwargs)

    return decorated


def admin_required(f):
    """要求管理员权限的装饰器（页面路由用）"""

    @wraps(f)
    def decorated(*args, **kwargs):
        if "user_id" not in session:
            return redirect(url_for("login"))
        if session.get("role") != "admin":
            return "无权限访问", 403
        return f(*args, **kwargs)

    return decorated


def api_admin_required(f):
    """要求管理员权限的装饰器（API 路由用）"""

    @wraps(f)
    def decorated(*args, **kwargs):
        if "user_id" not in session:
            return jsonify({"success": False, "error": "请先登录"}), 401
        if session.get("role") != "admin":
            return jsonify({"success": False, "error": "无权限"}), 403
        return f(*args, **kwargs)

    return decorated
