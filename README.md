# Naver Cafe Attachment Downloader (MV/MV2)

네이버 카페 게시글의 **첨부파일** 중 MV 또는 MV2 타입(주로 구형 동영상 파일)을 **Playwright**와 **curl**을 이용해 다운로드하는 Python3 스크립트입니다.

---

## 📦 특징

- **MV/MV2 지원**: `type=MV` 또는 `type=MV2` 파라미터가 포함된 첨부파일 또는 legacy 영상 서버(`mv.naver.com`) 주소를 자동 감지합니다.
- **자동 로그인 지원**: NID 쿠키를 감지하여 세션 캐시를 재사용 (state 파일 저장)
- **첨부파일 목록 추출**: 게시글 본문의 첨부파일 목록을 파싱하여 다운로드 링크를 추출합니다.
- **레거시 서버 감지**: 영상 재생 시 호출되는 구형 서버 주소를 네트워크 단에서 감지합니다.

---

## 📋 설치

### 1. Python 환경 준비
```bash
python3 -m venv .venv
source .venv/bin/activate
pip install playwright
pip install --upgrade pip
```

### 2. Playwright 브라우저 설치
```bash
playwright install chromium
```

### 3. 필수 프로그램
- curl (macOS 기본 포함 / Ubuntu: sudo apt install curl)

---

## 🚀 사용법

```bash
python naver_cafe_vod.py \
  --url "https://cafe.naver.com/카페명/게시글번호" \
  --out "./downloads"
```

### 주요 옵션

|옵션 |설명 |기본값 |
| --- | --- | --- |
| --url | 카페 글 URL | 필수 |
| --out | 저장 폴더 경로 또는 파일명 베이스 | ./downloads |
| --mv-only | MV/MV2 타입만 필터링하여 다운로드 | True |
| --all | MV/MV2 뿐만 아니라 모든 첨부파일 다운로드 | False |
| --tag | 파일명에 붙을 타임스탬프 태그 (미지정 시 현재 시각) | 빈 문자열 |
| --state-path | Playwright 세션 캐시(JSON) 저장 경로 | ./naver_state.json |
| --fresh-login | 세션 무시하고 새 로그인 | False |
| --headless | 브라우저 창 숨김 (로그인엔 비권장) | False |
| --detect-window | 페이지 로딩 및 감지 대기 시간(초) | 5 |

---

## 📂 동작 방식

1. Playwright 브라우저 실행 및 네이버 로그인 (세션 재사용 가능)
2. 게시글 이동 및 `cafe_main` 프레임 대기
3. 첨부파일 목록 버튼 클릭 및 링크 추출
4. `mv.naver.com` 등 레거시 서버 요청 감지
5. MV/MV2 패턴에 맞는 파일들을 `curl`로 다운로드
6. 결과 저장

### 💡 예제

```bash
# MV/MV2 첨부파일만 다운로드
python naver_cafe_vod.py --url "https://cafe.naver.com/f-e/123456"

# 모든 첨부파일 다운로드
python naver_cafe_vod.py --url "https://cafe.naver.com/f-e/123456" --all

# 특정 폴더에 저장
python naver_cafe_vod.py --url "https://cafe.naver.com/f-e/123456" --out "~/Movies/Naver"
```

---

## ⚠️ 주의사항

- 네이버 카페 정책에 따라 로그인 후에만 접근 가능한 게시글은 반드시 로그인이 필요합니다.
- 저작권이 있는 파일의 무단 다운로드 및 배포는 법적 제재를 받을 수 있습니다.
- **본 스크립트는 개인 학습용이며, 사용 결과에 대한 책임은 사용자에게 있습니다.**
