#!/usr/bin/env python
"""测试：打印视频页面完整 body 文本，找到互动数据位置"""
import time
from playwright.sync_api import sync_playwright

aweme_id = '7483955919230509609'

with sync_playwright() as p:
    browser = p.chromium.launch(channel='msedge', headless=False,
        args=['--disable-blink-features=AutomationControlled'])
    context = browser.new_context(
        viewport={'width': 1920, 'height': 1080},
        user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/143.0.0.0 Safari/537.36 Edg/143.0.0.0')
    page = context.new_page()

    page.goto('https://www.douyin.com/', timeout=30000, wait_until='domcontentloaded')
    time.sleep(6)
    page.goto('https://www.douyin.com/video/' + aweme_id, timeout=30000, wait_until='domcontentloaded')

    for attempt in range(5):
        time.sleep(3)
        try:
            text = page.evaluate('document.body.innerText')
            if text and len(text) > 100:
                # Save to file for inspection
                with open('D:/YIONpro/几何星球AUTO/page_text.txt', 'w', encoding='utf-8') as f:
                    f.write(text)
                print(f'Page text saved ({len(text)} chars)')
                print('First 800 chars:')
                print(text[:800])
                break
        except Exception as e:
            print(f'Attempt {attempt+1}: {str(e)[:60]}')

    browser.close()
