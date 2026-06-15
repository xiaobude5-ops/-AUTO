"""应用配置常量"""
import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, "geometry_star.db")
PORT = 5150
DEBUG = False

# Flask Session 密钥（首次启动自动生成随机值）
SECRET_KEY = os.environ.get("SECRET_KEY", os.urandom(24).hex())

# 抓取配置
SCRAPE_TIMEOUT = 60
SCRAPE_RETRY_MAX = 2

# 月度统计：当月1号至次月2号
MONTH_END_DAY_OFFSET = 2

# 定时自动刷新
AUTO_REFRESH_ENABLED = True
AUTO_REFRESH_TIMES = ["16:00"]
