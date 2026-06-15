"""一次性抖音扫码登录 — 写入 .browser_data 持久化"""
import io
import sys

try:
    if hasattr(sys.stdout, "buffer"):
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
except Exception:
    pass

from playwright.sync_api import sync_playwright

from scraper import BROWSER_DATA_DIR, UA, _has_sessionid


def _say(msg: str):
    try:
        print(msg, flush=True)
    except Exception:
        pass


def main():
    _say("\n  [*] 抖音扫码登录")
    _say("  " + "=" * 40)
    _say("  即将打开浏览器，请用抖音 APP 扫码登录")
    _say("  登录完成后，关闭浏览器窗口即可\n")

    with sync_playwright() as p:
        ctx = p.chromium.launch_persistent_context(
            user_data_dir=BROWSER_DATA_DIR,
            channel="msedge",
            headless=False,
            viewport={"width": 1280, "height": 800},
            user_agent=UA,
            args=["--disable-blink-features=AutomationControlled"],
        )
        page = ctx.pages[0] if ctx.pages else ctx.new_page()
        page.goto("https://www.douyin.com/", wait_until="domcontentloaded")

        try:
            page.wait_for_event("close", timeout=0)
        except Exception:
            pass

        ok = _has_sessionid(ctx)
        try:
            ctx.close()
        except Exception:
            pass

        _say("")
        if ok:
            _say("  [OK] 登录成功，cookies 已保存")
        else:
            _say("  [WARN] 未检测到登录态 — 请重新运行此脚本并完成扫码")


if __name__ == "__main__":
    main()
