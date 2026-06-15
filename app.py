"""Flask 应用入口 — 几何星球AUTO"""
import os
import sys
import threading
import time
from datetime import datetime, timedelta
from flask import Flask

from config import SECRET_KEY, PORT, DEBUG, AUTO_REFRESH_ENABLED, AUTO_REFRESH_TIMES
from database import init_db, create_user, get_all_users
from auth import hash_password

# 确保工作目录正确
os.chdir(os.path.dirname(os.path.abspath(__file__)))

app = Flask(__name__)
app.secret_key = SECRET_KEY
app.config["TEMPLATES_AUTO_RELOAD"] = True


# 自定义过滤器
@app.template_filter("format_number")
def format_number(value):
    if value is None:
        return "0"
    return f"{int(value):,}"


# 初始化数据库 + 创建默认管理员
init_db()
users = get_all_users()
if not any(u["username"] == "admin" for u in users):
    create_user("admin", hash_password("admin"), "管理员", "admin")
    print("👤 已创建默认管理员账号: admin / admin")
    print("⚠️  请尽快登录修改密码！")


# 注册路由
from routes import register_routes

register_routes(app)


# ── 自动刷新调度器 ──
def _do_refresh():
    """执行一次刷新"""
    from database import get_all_submission_aweme_ids, save_video_snapshot
    from scraper import scrape_single_video_with_retry
    from config import SCRAPE_RETRY_MAX

    print(f"⏰ 自动刷新触发 ({datetime.now().strftime('%Y-%m-%d %H:%M:%S')})")
    items = get_all_submission_aweme_ids()
    for item in items:
        try:
            for attempt in range(SCRAPE_RETRY_MAX + 1):
                data = scrape_single_video_with_retry(item["aweme_id"])
                if data:
                    save_video_snapshot(item["id"], data["likes"], data["comments"],
                                       data["shares"], data["collects"])
                    break
        except Exception as e:
            print(f"  [refresh error] {item['aweme_id']}: {e}")
        time.sleep(0.5)


def auto_refresh_scheduler():
    if not AUTO_REFRESH_ENABLED:
        return

    while True:
        now = datetime.now()
        next_run = None
        for t_str in sorted(AUTO_REFRESH_TIMES):
            h, m = map(int, t_str.split(":"))
            target = now.replace(hour=h, minute=m, second=0, microsecond=0)
            if target <= now:
                target += timedelta(days=1)
            if next_run is None or target < next_run:
                next_run = target

        wait_seconds = (next_run - now).total_seconds()
        while wait_seconds > 30:
            time.sleep(30)
            now = datetime.now()
            wait_seconds = (next_run - now).total_seconds()

        if wait_seconds > 0:
            time.sleep(wait_seconds)

        _do_refresh()
        time.sleep(60)


if __name__ == "__main__":
    if AUTO_REFRESH_ENABLED:
        t = threading.Thread(target=auto_refresh_scheduler, daemon=True)
        t.start()
        times_str = "、".join(AUTO_REFRESH_TIMES)
        print(f"⏰ 自动刷新已启用，每天 {times_str} 自动更新数据")

    print(f"🚀 几何星球AUTO 启动中... http://localhost:{PORT}")
    app.run(host="0.0.0.0", port=PORT, debug=DEBUG)
