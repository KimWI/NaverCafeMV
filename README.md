# Naver Cafe Attachment Downloader (MV/MV2/ZIP)

네이버 카페 게시글의 **첨부파일** 중 MV 또는 MV2 타입(구형 동영상 및 관련 ZIP 파일)을 **Playwright**와 **curl**을 이용해 자동 감지하고 다운로드하는 Python3 스크립트입니다.

---

## 📦 주요 특징

- **MV/MV2 및 ZIP 지원**: 
  - `type=MV` 또는 `type=MV2` 파라미터가 포함된 직접 첨부파일 감지.
  - 파일명(타이틀)에 "mv", "mv2"가 포함된 **ZIP 압축 파일** 자동 필터링.
  - 레거시 영상 서버(`mv.naver.com`, `mv2.naver.com`) 주소 감지.
- **자동 세션 관리**: NID 쿠키를 감지하여 세션 캐시(`naver_state.json`)를 생성하고 재사용합니다.
- **스마트 추출**: `cafe_main` 프레임 내부의 첨부파일 목록 버튼을 자동으로 클릭하여 숨겨진 링크까지 파싱합니다.
- **검색 모드**: `--skip-download` 옵션을 통해 실제 다운로드 없이 감지된 파일 목록만 미리 확인할 수 있습니다.

---

## 📋 사전 준비 및 설치

### 1. 필수 프로그램
- **Python 3.7+**
- **curl**: 파일 다운로드용 (macOS/Linux 기본 포함)

### 2. 라이브러리 설치
```bash
# 가상환경 생성 및 활성화 (권장)
python3 -m venv .venv
source .venv/bin/activate

# 필수 패키지 설치
pip install playwright
playwright install chromium
```

---

## 🚀 사용법

```bash
python naver_cafe_vod.py --url "게시글_URL" [옵션]
```

### ⚙️ 주요 옵션

| 옵션 | 설명 | 기본값 |
| --- | --- | --- |
| `--url` | 카페 게시글 URL (필수) | - |
| `--out` | 저장 폴더 경로 또는 파일명 베이스 | `./downloads` |
| `--mv-only` | MV/MV2 관련 파일만 필터링하여 다운로드 | `True` |
| `--all` | 필터링 없이 모든 첨부파일 다운로드 | `False` |
| `--skip-download` | 실제 다운로드 없이 감지된 목록 및 URL만 출력 | `False` |
| `--tag` | 파일명에 붙을 커스텀 태그 (미지정 시 현재 시각 사용) | `""` |
| `--state-path` | 세션 캐시(JSON) 저장 경로 | `./naver_state.json` |
| `--fresh-login` | 기존 세션을 무시하고 새로 로그인 진행 | `False` |
| `--headless` | 브라우저 창을 숨긴 상태로 실행 | `False` |
| `--detect-window` | 페이지 로딩 및 동적 요소 감지 대기 시간(초) | `5` |

---

## 💡 실행 예제

```bash
# 1. MV/MV2 관련 파일(동영상, ZIP 등) 자동 감지 및 다운로드
python naver_cafe_vod.py --url "https://cafe.naver.com/mycafe/12345"

# 2. 실제 다운로드 전 목록만 확인 (테스트용)
python naver_cafe_vod.py --url "https://cafe.naver.com/mycafe/12345" --skip-download

# 3. MV 타입 외에 모든 첨부파일을 한꺼번에 다운로드
python naver_cafe_vod.py --url "https://cafe.naver.com/mycafe/12345" --all

# 4. 저장 위치 및 세션 태그 지정
python naver_cafe_vod.py --url "https://cafe.naver.com/mycafe/12345" --out "~/Downloads" --tag "test_session"
```

---

## 📂 동작 방식

1. **로그인**: `naver_state.json`이 있으면 세션을 재사용하고, 없으면 직접 로그인을 대기합니다.
2. **프레임 전환**: 카페 게시글이 로드되면 실제 본문이 들어있는 `cafe_main` 프레임으로 전환합니다.
3. **요소 클릭**: '첨부파일' 목록 버튼을 자동으로 찾아 클릭하여 링크를 노출시킵니다.
4. **패턴 매칭**: 
   - DOM에서 `ArticleFileDownload` 링크 중 MV 패턴 매칭.
   - 네트워크 요청 중 `mv.naver.com` 서버 호출 감지.
5. **다운로드**: 추출된 URL을 `curl` 명령어로 전달하여 세션 쿠키와 함께 안전하게 저장합니다.

---

## 🔗 참고 및 감사의 말

본 스크립트는 **[lunDreame/NaverCafeVOD](https://github.com/lunDreame/NaverCafeVOD)**의 원본 소스코드를 바탕으로, MV/MV2 타입의 첨부파일 및 ZIP 압축 파일 다운로드 기능을 추가하고 고도화한 버전입니다. 훌륭한 원본 소스를 공유해주신 **lunDreame**님께 감사드립니다.

---

## ⚠️ 주의사항

- **로그인 필수**: 카페 멤버에게만 공개된 게시글은 반드시 로그인이 완료되어야 접근 가능합니다.
- **저작권 준수**: 다운로드한 파일은 반드시 **개인 소장용**으로만 사용하십시오. 무단 배포 및 상업적 이용은 저작권법에 의해 처벌받을 수 있습니다.
- **책임 고지**: 본 스크립트 사용으로 발생하는 모든 법적 문제 및 계정 제재에 대해 개발자는 책임지지 않습니다.
