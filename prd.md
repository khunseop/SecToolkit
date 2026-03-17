# [PRD] SecToolkit: 폐쇄망용 보안 업무 자동화 및 분석 도구

## 1. 프로젝트 개요 (Project Overview)
- **프로젝트명:** SecToolkit
- **개발 환경:** Python 3.9+, FastAPI
- **프론트엔드:** HTML5, CSS3, Bootstrap 5 (Local Asset 사용)
- **배경:** 보안팀 폐쇄망 환경에서 외부 도구 사용이 제한됨에 따라, 분석에 필요한 필수 유틸리티를 자체 구축하여 데이터 유출 위험을 방지하고 업무 효율을 극대화함.
- **핵심 가치:** 오프라인 완결성(Self-contained), 보안성(Security), 경량화(Lightweight).

---

## 2. 제품 목표 (Product Goals)
1. **완벽한 폐쇄망 지원:** 외부 연결(CDN, API) 없이 모든 기능이 서버 내부에서 동작.
2. **분석 가독성 향상:** 복잡한 인코딩 데이터 및 트래픽 로그의 즉각적인 가시화.
3. **업무 표준화:** 팀 내 산재한 개별 스크립트를 하나의 웹 인터페이스로 통합.

---

## 3. 상세 기능 요구사항 (Functional Requirements)

### 3.1. 데이터 변환 및 카운터 (Transform & Count)
- **Multi-Decoder:** URL 및 Base64 디코딩. (추후 Hex, HTML Entity 확장 고려)
- **Byte Counter:** 텍스트 입력 시 바이트 크기 계산 (UTF-8/EUC-KR 등 선택 가능).
    - HTTP `Content-Length` 수동 검증 및 정책 설정 시 참고.

### 3.2. 분석 및 계산 (Analysis & Metrics)
- **Network Unit Converter:** - Mbps ↔ MB/s 변환 및 데이터 용량 단위 변환.
    - 대역폭 산정 및 트래픽 분석 시 활용.
- **JSON Beautifier:** 폐쇄망 내 로그 분석을 위한 JSON 정렬 및 문법 강조(Syntax Highlighting).
- **HAR Header Extractor:**
    - HAR 파일 업로드 및 서버 측 파싱.
    - `Authorization`, `Cookie`, `X-Forwarded-For` 등 주요 헤더값만 추출하여 표(Table) 형태로 출력.

---

## 4. 기술 스택 및 UI 설계 (Technical Stack & UI)

### 4.1. Backend (FastAPI)
- **구조:** 기능별 Service 모듈 분리. `static` 폴더를 통해 로컬 자원 서빙.
- **API 문서:** FastAPI가 자동 생성하는 `/docs` 활용 (오프라인 환경에서도 동작).

### 4.2. Frontend (Bootstrap 5)
- **Local Assets:** `bootstrap.min.css`, `bootstrap.bundle.min.js` 등 필수 파일을 프로젝트 내에 포함하여 배포.
- **UI Layout:** - **Sidebar/Tabs:** 기능 이동이 편리하도록 왼쪽 사이드바 또는 상단 탭 구성.
    - **Dark Mode:** 장시간 분석 업무를 고려한 어두운 테마 기본 지원 또는 선택 가능.
    - **Result Display:** 결과값 복사 버튼(Copy to Clipboard) 필수 포함.

---

## 5. 단계별 로드맵 (Roadmap)

### Phase 1: Core Framework (MVP)
- FastAPI 및 Bootstrap 5 로컬 환경 설정.
- URL/Base64 디코더 및 Byte Counter 웹 인터페이스 구현.

### Phase 2: Analysis Suite
- Mbps 단위 변환 계산기 추가.
- JSON 정렬 기능 및 HAR 파일 업로드/헤더 리스트업 기능 구현.

### Phase 3: Extension & Security
- 폐쇄망 내 업무용 IP 기반 접근 제어 기능 추가.
- JWT 디코더 및 보안 페이로드 생성기(XSS/SQLi) 추가.

---

## 6. 기대 효과 (Expected Benefits)
- **데이터 보안:** 외부 온라인 인코더/디코더 사용 차단으로 민감 정보 유출 방지.
- **분석 속도:** 도구 실행 및 결과 확인까지의 뎁스(Depth) 단축.
- **자산화:** 보안팀 고유의 기술 자산 확보 및 지속적인 기능 확장.

