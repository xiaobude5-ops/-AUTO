"""工具函数：URL 解析 + 月边界计算"""
import re
from datetime import datetime

import urllib.request
import urllib.error

DOUYIN_VIDEO_RE = re.compile(
    r"(?:https?://)?(?:www\.)?(?:ies)?douyin\.com/(?:share/)?(?:video|note)/(\d+)"
)
DOUYIN_SHORT_RE = re.compile(
    r"(?:https?://)?v\.douyin\.com/([A-Za-z0-9_-]+)"
)


def _resolve_short_url(short_code: str) -> str | None:
    """跟随 v.douyin.com 短链重定向，返回真实 aweme_id。失败返回 None。"""
    url = f"https://v.douyin.com/{short_code}/"
    try:
        req = urllib.request.Request(url, headers={
            "User-Agent": "Mozilla/5.0 (iPhone; CPU iPhone OS 16_0 like Mac OS X) "
                          "AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.0 "
                          "Mobile/15E148 Safari/604.1",
        })
        with urllib.request.urlopen(req, timeout=10) as resp:
            final = resp.geturl()
    except (urllib.error.URLError, TimeoutError, OSError):
        return None
    m = DOUYIN_VIDEO_RE.search(final)
    return m.group(1) if m else None


def extract_aweme_id(url: str) -> str | None:
    """从抖音视频链接提取 aweme_id。支持长短两种格式。"""
    url = url.strip()
    m = DOUYIN_VIDEO_RE.search(url)
    if m:
        return m.group(1)
    m = DOUYIN_SHORT_RE.search(url)
    if m:
        return _resolve_short_url(m.group(1))
    return None


def get_month_boundaries(year: int, month: int) -> tuple[datetime, datetime]:
    """月查询范围 = X月1号 00:00:00 ~ 次月2号 23:59:59"""
    start = datetime(year, month, 1, 0, 0, 0)
    if month == 12:
        end = datetime(year + 1, 1, 2, 23, 59, 59)
    else:
        end = datetime(year, month + 1, 2, 23, 59, 59)
    return start, end
