"""抓取模块 — 单视频抓取（持久化上下文，复用扫码登录态）"""
import io
import os
import sys
import time
from datetime import datetime
from playwright.sync_api import sync_playwright

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace") if hasattr(sys.stdout, "buffer") else sys.stdout

from config import SCRAPE_TIMEOUT, BASE_DIR

BROWSER_DATA_DIR = os.path.join(BASE_DIR, ".browser_data")

UA = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/143.0.0.0 Safari/537.36 Edg/143.0.0.0"
)


class NotLoggedInError(RuntimeError):
    """未登录抖音 — 需要先扫码"""


def _has_sessionid(context) -> bool:
    for c in context.cookies():
        if c.get("name") == "sessionid" and c.get("value"):
            return True
    return False


_FETCH_JS = """
async (aweme_id) => {
    const u = '/aweme/v1/web/aweme/detail/?device_platform=webapp&aid=6383'
            + '&channel=channel_pc_web&aweme_id=' + aweme_id
            + '&pc_client_type=1&version_code=290100&version_name=29.1.0'
            + '&cookie_enabled=true&platform=PC&downlink=10';
    try {
        const r = await fetch(u, { credentials: 'include' });
        if (!r.ok) return { __err: 'http_' + r.status };
        return await r.json();
    } catch (e) {
        return { __err: String(e) };
    }
}
"""


def _parse_detail(body: dict, aweme_id: str) -> dict | None:
    a = (body or {}).get("aweme_detail")
    if not a or a.get("aweme_id") != aweme_id:
        return None
    s = a.get("statistics") or {}
    ct = a.get("create_time") or 0
    dt = datetime.fromtimestamp(ct).strftime("%Y-%m-%d") if ct else ""
    return {
        "aweme_id": aweme_id,
        "desc": (a.get("desc") or "")[:200],
        "create_date": dt,
        "likes": s.get("digg_count", 0),
        "comments": s.get("comment_count", 0),
        "shares": s.get("share_count", 0),
        "collects": s.get("collect_count", 0),
    }


def scrape_single_video(aweme_id: str) -> dict | None:
    """
    抓取单条抖音视频的互动数据（登录态下，直接 fetch detail 接口）。
    未登录抛 NotLoggedInError；视频不存在或抓不到返回 None。
    """
    os.makedirs(BROWSER_DATA_DIR, exist_ok=True)
    result: dict | None = None

    with sync_playwright() as p:
        context = p.chromium.launch_persistent_context(
            user_data_dir=BROWSER_DATA_DIR,
            channel="msedge",
            headless=True,
            viewport={"width": 1920, "height": 1080},
            user_agent=UA,
            args=[
                "--disable-blink-features=AutomationControlled",
                "--no-sandbox",
            ],
        )
        page = context.pages[0] if context.pages else context.new_page()

        try:
            # 进入视频页（建立同源上下文 + 必要 cookies）
            page.goto(
                f"https://www.douyin.com/video/{aweme_id}",
                timeout=SCRAPE_TIMEOUT * 1000,
                wait_until="domcontentloaded",
            )

            if not _has_sessionid(context):
                raise NotLoggedInError(
                    "未登录抖音 — 请先双击运行『登录抖音.bat』扫码登录"
                )

            page.wait_for_timeout(2000)
            body = page.evaluate(_FETCH_JS, aweme_id)
            if isinstance(body, dict) and not body.get("__err"):
                result = _parse_detail(body, aweme_id)

        except NotLoggedInError:
            raise
        except Exception as e:
            print(f"  [scraper error] {aweme_id}: {e}")
        finally:
            context.close()

    return result


def scrape_single_video_with_retry(aweme_id: str, retries: int = 2) -> dict | None:
    """带重试的抓取；NotLoggedInError 直接抛出不重试"""
    for attempt in range(retries + 1):
        try:
            result = scrape_single_video(aweme_id)
        except NotLoggedInError:
            raise
        if result:
            return result
        if attempt < retries:
            time.sleep(2)
    return None
