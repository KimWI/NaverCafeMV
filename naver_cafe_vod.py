#!/usr/bin/env python3
# naver_cafe_attachment.py
# Original script by lunDreame (https://github.com/lunDreame/NaverCafeVOD)
# Modified to support MV/MV2/ZIP attachments.

import asyncio, argparse, subprocess, sys, shlex, time, re, os
from datetime import datetime
from pathlib import Path
from urllib.parse import urlparse, urlunparse, parse_qsl, urlencode, urljoin

from playwright.async_api import async_playwright

LOGIN_URL = "https://nid.naver.com/nidlogin.login?mode=form&url=https%3A%2F%2Fcafe.naver.com%2F"

def ts_now():
    return datetime.now().strftime("%Y%m%d_%H%M%S")

async def wait_login(ctx, timeout_ms=120000):
    """NID_SES 쿠키가 보일 때까지 대기 (이미 로그인 상태면 즉시 True)"""
    end = time.time() + timeout_ms/1000
    while time.time() < end:
        for c in await ctx.cookies():
            if c.get("name") == "NID_SES" and c.get("value"):
                return True
        await asyncio.sleep(0.3)
    return False

def stamp_output_name(out_path: Path, stamp: str, filename: str = None) -> Path:
    """
    최종 출력 파일명 뒤에 _<timestamp> 붙여 고유하게 저장.
    filename이 주어지면 out_path를 디렉토리로 간주하고 그 안에 저장.
    """
    if filename:
        target_dir = out_path if out_path.is_dir() else out_path.parent
        target_dir.mkdir(parents=True, exist_ok=True)
        
        p_filename = Path(filename)
        stem = p_filename.stem
        # 기존 확장자를 최대한 유지하되, 없으면 .mp4 (기본값)
        suffix = p_filename.suffix or ".mp4"
        return target_dir / f"{stem}_{stamp}{suffix}"
    
    out_path.parent.mkdir(parents=True, exist_ok=True)
    stem = out_path.stem
    suffix = out_path.suffix or ".mp4"
    return out_path.with_name(f"{stem}_{stamp}{suffix}")

async def download_file(url, target_path, headers, cookies_str):
    """curl을 사용하여 파일 다운로드"""
    print(f"[i] 다운로드 시작: {url}")
    print(f"[i] 저장 경로: {target_path}")
    
    target_path.parent.mkdir(parents=True, exist_ok=True)
    
    curl_cmd = [
        "curl",
        "-L",
        "-A", headers.get("User-Agent", ""),
        "-H", f"Referer: {headers.get('Referer', '')}",
        "-H", f"Cookie: {cookies_str}",
        url,
        "-o", str(target_path)
    ]
    
    try:
        subprocess.check_call(curl_cmd)
        return True
    except Exception as e:
        print(f"[!] 다운로드 실패: {e}")
        return False

async def run(args):
    async with async_playwright() as p:
        launch_kwargs = dict(headless=args.headless)
        if args.chrome_channel:
            launch_kwargs["channel"] = "chrome"
        browser = await p.chromium.launch(**launch_kwargs)

        state_file = Path(args.state_path).expanduser().resolve()
        use_state = state_file.exists() and not args.fresh_login

        if use_state:
            print(f"[i] 세션 캐시 사용: {state_file}")
            context = await browser.new_context(storage_state=str(state_file))
        else:
            context = await browser.new_context()
        page = await context.new_page()

        # Network Listener for legacy MV/MV2 URLs
        legacy_urls = []
        def on_request(req):
            u = req.url
            if "mv.naver.com" in u or "mv2.naver.com" in u:
                if u not in [x["url"] for x in legacy_urls]:
                    name = Path(urlparse(u).path).name or "legacy_video"
                    legacy_urls.append({"name": name, "url": u})
        page.on("request", on_request)

        # Login Logic
        already_logged_in = await wait_login(context, timeout_ms=1500)
        if already_logged_in and use_state:
            print("[✓] 캐시된 로그인 상태 감지")
        else:
            print(f"[i] 로그인 페이지: {LOGIN_URL}")
            await page.goto(LOGIN_URL, wait_until="domcontentloaded")
            if not await wait_login(context, args.login_timeout):
                print("[!] 로그인 감지 실패 (NID_SES 없음)"); await browser.close(); sys.exit(1)
            print("[✓] 로그인 완료")
            try:
                await context.storage_state(path=str(state_file))
                print(f"[i] 세션 저장: {state_file}")
            except Exception as e:
                print(f"[i] 세션 저장 실패(무시): {e}")

        print(f"[i] 이동: {args.url}")
        await page.goto(args.url, wait_until="domcontentloaded")

        # Cafe Main Iframe switch
        print("[i] 게시글 본문 로딩 대기...")
        frame = None
        for _ in range(15):
            frame = page.frame(name="cafe_main")
            if frame: break
            await asyncio.sleep(1)
        
        if not frame:
            print("[!] cafe_main 프레임을 찾을 수 없습니다.")
            await browser.close(); sys.exit(2)

        print(f"[i] 첨부파일 목록 확인 중 ({args.detect_window}s 대기)...")
        
        # Try to find and click attachment button
        try:
            btn = await frame.wait_for_selector("a.btn_file", timeout=5000)
            if btn:
                await btn.click()
                await asyncio.sleep(2)
        except:
            pass

        # Extract links from DOM
        links = await frame.query_selector_all("ul.list_attach li a.pc")
        if not links:
            links = await frame.query_selector_all("div.ArticleFile a[href*='ArticleFileDownload']")

        found_attachments = []
        mv_patterns = [re.compile(r"mv\d*", re.IGNORECASE)]
        
        for link in links:
            text = (await link.inner_text()).strip()
            href = await link.get_attribute("href")
            if not href: continue
            
            full_url = urljoin("https://cafe.naver.com", href)
            
            # MV/MV2 title or type check
            is_mv = any(p.search(text) or p.search(full_url) for p in mv_patterns) or \
                    "type=MV" in full_url or "type=MV2" in full_url
            
            if is_mv:
                found_attachments.append({"name": text, "url": full_url})
            elif not args.mv_only:
                found_attachments.append({"name": text, "url": full_url})

        # Also add legacy URLs found via network
        for item in legacy_urls:
            if item["url"] not in [x["url"] for x in found_attachments]:
                found_attachments.append(item)

        if not found_attachments:
            print("[!] MV/MV2 첨부파일을 찾지 못했습니다.")
            await browser.close(); sys.exit(3)

        print(f"[✓] {len(found_attachments)}개의 첨부파일을 찾았습니다.")

        if args.skip_download:
            print("\n[i] --skip-download 설정됨. 검색된 목록만 출력합니다:")
            for idx, attach in enumerate(found_attachments):
                print(f"  [{idx+1}] {attach['name']}")
                print(f"      URL: {attach['url']}")
            await browser.close(); return

        # Download headers
        ua = await page.evaluate("() => navigator.userAgent")
        referer = page.url
        ck = await context.cookies()
        cookies_str = "; ".join([f"{c['name']}={c['value']}" for c in ck])
        
        headers = {
            "User-Agent": ua,
            "Referer": referer
        }

        stamp = args.tag if args.tag else ts_now()
        out_path = Path(args.out).expanduser().resolve()
        
        for idx, attach in enumerate(found_attachments):
            print(f"\n[{idx+1}/{len(found_attachments)}] {attach['name']}")
            target = stamp_output_name(out_path, stamp, attach['name'])
            success = await download_file(attach['url'], target, headers, cookies_str)
            if success:
                print(f"[✓] 완료: {target}")
            else:
                print(f"[!] 실패: {attach['name']}")

        await browser.close()

def main():
    ap = argparse.ArgumentParser(description="Naver Cafe Attachment Downloader (MV/MV2/ZIP)")
    ap.add_argument("--url", required=True, help="카페 글 URL")
    ap.add_argument("--out", default="./downloads", help="저장 폴더 또는 파일명")
    ap.add_argument("--tag", default="", help="고정 세션 태그(미지정 시 현재 시각 타임스탬프 사용)")
    ap.add_argument("--mv-only", action="store_true", default=True, help="MV/MV2 타입만 다운로드 (기본값 True)")
    ap.add_argument("--all", action="store_false", dest="mv_only", help="모든 첨부파일 다운로드")
    ap.add_argument("--skip-download", action="store_true", help="실제 다운로드를 진행하지 않고 목록만 출력")

    ap.add_argument("--state-path", default="./naver_state.json",
                    help="Playwright storage_state 파일 경로(쿠키/세션 캐시)")
    ap.add_argument("--fresh-login", action="store_true",
                    help="세션 캐시 무시하고 새 로그인 진행")

    ap.add_argument("--headless", action="store_true", help="브라우저 창 숨김(로그인엔 비권장)")
    ap.add_argument("--chrome-channel", action="store_true", help="설치된 Chrome 채널로 실행(원하면 사용)")
    ap.add_argument("--login-timeout", type=int, default=120000, help="로그인 대기(ms)")
    ap.add_argument("--detect-window", type=int, default=5, help="로딩 및 감지 대기(초)")

    args = ap.parse_args()
    try:
        asyncio.run(run(args))
    except KeyboardInterrupt:
        print("\n[!] 사용자 중단")

if __name__ == "__main__":
    main()
