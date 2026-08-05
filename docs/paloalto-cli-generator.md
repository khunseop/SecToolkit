# PA Policy CLI Generator — 기능 문서

팔로알토(PAN-OS) 방화벽의 보안 정책(security rule)·서비스 오브젝트 CLI 명령어를,
엑셀에서 바로 복사/붙여넣기 한 대량 데이터로부터 한 번에 생성해주는 기능. 다른 프로젝트에
이식할 것을 염두에 두고 "무엇을, 왜 이렇게" 만들었는지 정리한다.

## 1. 이 기능이 푸는 문제

방화벽 정책은 보통 엑셀로 관리·전달된다. 실무에서 반복되는 두 가지 불편:

1. **정책 하나가 여러 행에 걸쳐 표현됨** — source/destination/service 등 다중값 객체가 많으면,
   담당자가 엑셀에서 정책 하나를 "첫 행에 이름/기타 컬럼 + 여러 개의 후속 행에 객체값만" 식으로
   입력한다(No/RuleName 등은 반복 입력하지 않음). 이걸 CLI 명령어로 바꾸려면 수작업 정리가 필요했음.
2. **CLI 문법 실수** — `set`/`delete`/`move`마다 필요한 옵션이 다르고, delete는 "필드 1개·값 1개"만
   허용되는 등 PAN-OS 고유의 제약이 있어 손으로 치면 실수가 잦음.

이 기능은 (a) 여러 행에 걸친 원본 데이터를 그대로 붙여넣거나 업로드해도 자동으로 정책 1개=1행으로
병합하고, (b) 액션별로 다른 문법 규칙을 서버 로직으로 강제해서 애초에 잘못된 명령어가 나올 수 없게
만드는 것이 핵심이다.

## 2. 레이어 구성

```
app/schemas/paloalto.py        # 요청/응답 Pydantic 모델 (계약)
app/services/paloalto.py       # CLI 명령어 생성 순수 로직 (PaloAltoService)
app/services/paloalto_excel.py # 엑셀 템플릿 생성 + 파싱 + 다중행 병합 + 기본값 채움
app/api/routers/paloalto.py    # FastAPI 라우터 (4~5개 엔드포인트)
data/paloalto_defaults.json    # 사용자가 저장한 "기본값" 영속 파일 (전역 1개, 세션 구분 없음)

templates/components/views/paloalto.html  # 그리드 UI, 결과 렌더 컨테이너, <template> 마크업
static/js/modules/paloalto.js             # 그리드 상태 관리(=DOM), API 호출, 결과 렌더링
```

상태 관리 철학: **DOM이 곧 상태**다. 별도 상태 라이브러리 없이, 그리드의 각 `<div class="pa-row">`가
행 하나의 값을 들고 있고, "생성" 버튼을 누를 때만 DOM을 읽어 API에 보낸다. 소규모 사내 도구에는
이 편이 React/상태관리 라이브러리보다 단순하고 유지보수가 쉬웠다.

## 3. 데이터 모델 (`app/schemas/paloalto.py`)

```python
class PolicyRuleRequest(BaseModel):
    action: str  # "set" | "delete" | "move"
    vsys: str = ""
    rule_name: str                     # 필수
    disabled: bool = False
    rule_action: str = "allow"         # PAN-OS의 allow/deny/drop/reset-*
    from_zone: str = "";  source: str = "";        source_user: str = ""
    to_zone: str = "";    destination: str = "";    service: str = "";  application: str = ""
    description: str = ""
    log_end: str = ""          # "", "yes", "no"
    log_setting: str = ""
    move_position: str = ""    # "top" | "bottom" | "before" | "after"
    anchor_rule: str = ""      # before/after일 때만 사용

class ServiceObjectRequest(BaseModel):
    vsys: str = ""
    name: str        # 필수
    protocol: str     # "tcp" | "udp"
    port: str         # 필수, 콤마/범위 등 PAN-OS 문법 그대로 통과
```

다중값 필드(`from_zone`, `source`, `source_user`, `to_zone`, `destination`, `service`,
`application`)는 **콤마 또는 줄바꿈으로 구분된 문자열**을 그대로 받는다. 리스트 타입으로 안 받고
문자열로 받는 이유: 엑셀 셀 복사/붙여넣기(줄바꿈으로 여러 줄이 붙는다) 그대로 입력할 수 있게 하기 위해서다.

## 4. CLI 명령어 생성 로직 (`PaloAltoService.generate_command`)

### 4.1 공통 규칙
- `rule_name`이 비어 있으면 무조건 에러.
- 값에 공백이 있으면 자동으로 큰따옴표로 감싼다(`_quote_if_needed`).
- 다중값은 개수에 따라 문법이 갈린다: 1개면 그냥 값, 2개 이상이면 PAN-OS의 리스트 문법
  `[ a b c ]`로 감싼다(`_format_list_value`).

```python
def _format_list_value(raw: str) -> str:
    items = [x.strip() for x in raw.replace(",", "\n").split("\n") if x.strip()]
    if not items: return ""
    quoted = [_quote_if_needed(i) for i in items]
    return quoted[0] if len(quoted) == 1 else "[ " + " ".join(quoted) + " ]"
```

### 4.2 `set` (생성/수정)
```
set [vsys <vsys>] rulebase security rules "<rule_name>"
    disabled yes|no
    action <rule_action>
    from ... source ... source-user ... to ... destination ... service ... application ...
    description "..."
    log-end yes|no
    log-setting "..."
```
- **`disabled`는 항상 명시적으로 `yes` 또는 `no`를 출력한다.** 처음엔 `disabled`가 true일 때만
  `disabled yes`를 넣었는데, 그러면 기존에 disabled였던 룰을 다시 활성화하려는 `set` 명령에서
  `disabled no`가 빠져 실제로는 재활성화가 안 되는 버그가 있었다. → **항상 명시**하는 게 안전.
- 값이 없는 다중값 필드는 아예 그 옵션을 생략한다(빈 문자열로 넣지 않음).
- `rule_action`(대소문자 섞여 들어와도) 소문자로 정규화해서 PAN-OS 문법을 맞춘다.

### 4.3 `delete`
```
delete [vsys <vsys>] rulebase security rules "<rule_name>"              # 필드 전부 비었으면 rule 전체 삭제
delete [vsys <vsys>] rulebase security rules "<rule_name>" source "1.1.1.1"  # 객체 하나만 삭제
```
PAN-OS의 `delete` 문법은 **한 번에 필드 1개, 값 1개**만 지정할 수 있다. 서버 로직이 이걸 강제:
```python
set_fields = [f for f in LIST_FIELDS if getattr(request, f).strip()]
if len(set_fields) > 1:
    return {"error": "삭제 시 한 번에 하나의 필드만 지정할 수 있습니다."}
if len(items_in_that_field) != 1:
    return {"error": "삭제 시 값은 하나만 입력하세요."}
```
→ 이 제약을 **UI에서도 구조적으로 강제**했다(6장 참고): delete 행은 "필드 선택 셀렉트 1개 + 값 입력 1칸"
만 보여줘서, 애초에 여러 필드/여러 값을 입력할 수 있는 UI 자체가 없다. 백엔드 검증은 안전망으로 유지.

### 4.4 `move`
```
move [vsys <vsys>] rulebase security rules "<rule_name>" top|bottom
move [vsys <vsys>] rulebase security rules "<rule_name>" before|after "<anchor_rule>"
```
- `before`/`after`는 `anchor_rule`(기준이 되는 다른 정책명) 기준 상대 위치다. 사용자들이 자주
  헷갈려해서 UI에 "before = anchor_rule 바로 **위**로 · after = anchor_rule 바로 **아래**로"라는
  고정 안내문을 넣었다. select option에도 `before (기준 정책 위)`처럼 뜻을 병기.

### 4.5 서비스 오브젝트 생성 (`generate_service_command`)
```
set [vsys <vsys>] service <name> protocol tcp|udp port <port>
```
필드 3개(name, protocol, port)뿐이라 규칙이 단순함. `protocol`이 tcp/udp가 아니면 에러.

### 4.6 검증용 "개수" 반환
`set` 명령 생성 시, 다중값 필드별로 **몇 개의 값이 들어갔는지**(`counts: {"source": 3, "service": 2, ...}`)
같이 반환한다. 엑셀에서 여러 행을 병합해 만든 결과가 의도한 개수만큰 합쳐졌는지 사용자가 결과 화면에서
바로 눈으로 검증할 수 있게 하기 위함 — "여러 행을 하나로 합치는" 기능은 항상 "제대로 합쳐졌는지 확인할
방법"을 같이 줘야 신뢰할 수 있다는 게 이번에 얻은 교훈.

## 5. 대량 생성 UX (그리드)

한 화면에 **행 1개 = 명령어 1개**를 매핑하는 그리드. 행이 1개면 단일 생성, 여러 개면 대량 생성 —
"단일 생성"과 "대량 생성"을 별도 탭으로 나누지 않고 통합했다(초기엔 나눠져 있었는데, 결국 대량
생성에 1개만 입력하면 단일 생성과 같아서 탭 분리가 무의미했음).

핵심 설계 포인트 4가지:

**(1) 액션별 조건부 필드 노출.** `set`/`delete`/`move`가 필요로 하는 필드가 완전히 다른데, 처음엔
17개 컬럼짜리 고정 테이블을 만들어서 모든 행에 무관한 컬럼까지 다 보였다(가로 스크롤 지옥). →
행마다 공통 필드(작업유형/vsys/rule_name) + 액션별 필드 그룹 3개를 두고, JS로 `display:none`
토글. 액션별 그룹은 감싸는 `<div>`에 `display: contents`를 줘서, 보일 때는 부모 flex 컨테이너에
자식들이 그대로 합류하게(테두리·레이아웃 부담 없이) 만들었다.

```css
.pa-fields-row { display: flex; flex-wrap: nowrap; overflow-x: auto; }  /* 행은 항상 한 줄 높이 */
.pa-fields-set, .pa-fields-delete, .pa-fields-move { display: contents; }  /* JS가 style.display로 토글 */
.pa-row-buttons { position: sticky; left: 0; }  /* 복제/삭제 버튼은 스크롤해도 항상 보이게 */
```
`set`은 필드가 12개라 아무리 넓혀도 한 줄에 다 안 들어간다 — 이 경우 **행 높이를 한 줄로 고정하고
넘치는 필드는 그 행 안에서만 가로 스크롤**되게 했다(페이지 전체 스크롤이 아니라 행 단위 스크롤).
"자리를 적게 차지하면서 필드는 다 보여줘야 한다"는 요구를 동시에 만족시키는 절충안.

**(2) delete 행은 필드 select + 값 1칸만.** 4.3에서 설명한 "필드 1개·값 1개" 제약을 UI 구조로
원천 차단. 자유 텍스트 필드 7개를 다 채워보고 제출 후에야 에러를 아는 것보다 훨씬 낫다.

**(3) 반복 입력 최소화.**
- "1행 값을 기본값으로 저장" → `data/paloalto_defaults.json`에 저장, 새 행 추가 시 자동 프리필.
- "모든 행에 기본값 적용" → 이미 만들어진 모든 행에 저장된 기본값을 일괄 덮어씀.
- 행 [복제] 버튼 → 현재 행 값 그대로 복사해 바로 아래 삽입.

**(4) 제출 전 인라인 검증.** `rule_name`이 빈 행은 alert 하나로 끝내지 않고, 해당 행 테두리를
빨갛게 표시 + 그 행으로 스크롤. "어떤 행이 문제인지" 바로 보여주는 게 핵심.

**(5) 결과는 성공/에러를 섞지 않는다.** 결과 리스트는 줄마다 성공(녹색)/에러(빨강) 배지, 명령어
텍스트, 개별 복사 버튼, 그리고 (4.6의) 객체 개수 요약을 보여준다. "전체 복사"는 **성공한 줄만** 골라
복사한다(에러 줄이 섞여 나가면 안 되니까).

## 6. 엑셀 업로드 — 다중 행 → 1행 병합 알고리즘 (핵심)

이 기능에서 가장 이식 가치가 높은 부분. `app/services/paloalto_excel.py::rows_from_sheet_values`는
**순수 함수**(엑셀 라이브러리에 의존하지 않음, `list[list]` → `list[dict]`)로 짜여 있어서 다른
프로젝트에 그대로 옮기기 쉽다.

### 6.1 컬럼 매핑은 헤더 이름 기반 (순서 무관)
```python
COLUMN_FIELD_MAP = [("작업유형", "action"), ("vsys", "vsys"), ("rule_name", "rule_name"), ...]
header_to_field = dict(COLUMN_FIELD_MAP)
field_by_col = [header_to_field.get(h) for h in header_row]   # 헤더 텍스트로 컬럼 위치를 찾음
```
헤더 행을 먼저 읽어서 "이 컬럼이 어떤 필드인지"를 정하기 때문에, 엑셀에서 컬럼 순서를 바꿔도
그대로 동작한다. 헤더 텍스트가 매핑 테이블에 없으면 그 컬럼은 조용히 무시된다(오타 주의 — 알려주는
경고는 없음, 개선 여지로 남겨둠).

### 6.2 "연속 행(continuation row)" 병합
```python
current = None
for raw_row in data_rows:
    row_dict = {필드명: 셀값, ...}   # 헤더 매핑대로 파싱

    if not row_dict["rule_name"].strip() and current is not None:
        # rule_name이 빈 행 = 바로 위 정책의 연속. 값이 있는 다중값 필드만 콤마로 이어붙인다.
        for field in LIST_FIELDS:   # from/source/source-user/to/destination/service/application
            value = row_dict.get(field, "").strip()
            if value:
                current[field] = f"{current[field]},{value}" if current[field] else value
        continue   # 별도 행으로 만들지 않음

    current = row_dict
    rows.append(current)
```
규칙은 단 하나: **`rule_name`이 비어 있으면 "이전 행과 같은 정책"**. 그 행에 값이 채워진 다중값
컬럼만 콤마로 이어붙이고, 나머지 컬럼(설명, disabled 등)은 건드리지 않는다. 완전히 빈 행은 그
이전에 별도로 걸러진다.

```
원본 (여러 행)                          →  병합 결과 (1행)
No RuleName    Source          Service      RuleName=Web_Access
1  Web_Access  10.10.10.0/24   TCP_80       Source=10.10.10.0/24,10.10.20.0/24
              10.10.20.0/24                Service=TCP_80,TCP_8080
                              TCP_8080
```

이식 시 고려할 점: `rule_name`이 병합 키(anchor)라는 게 이 도메인 특화 규칙이다. 다른 데이터에
적용할 땐 "이 행이 새 레코드인지 연속인지"를 판별하는 필드를 무엇으로 할지부터 정해야 한다(보통
PK/식별자 컬럼이 비어 있는지로 판별하면 됨).

### 6.3 빈/누락 컬럼 → 저장된 기본값으로 채우기
```python
def apply_defaults(rows, defaults):
    for row in rows:
        if not row.get("action", "").strip():
            row["action"] = "set"                      # 액션 컬럼 없으면 set으로 간주
        for field in DEFAULT_FILLABLE_FIELDS:
            value = row.get(field)
            is_blank = value is None or (isinstance(value, str) and not value.strip())
            if is_blank and field in defaults:
                row[field] = defaults[field]            # 컬럼이 아예 없어도, 셀이 비어도 채워짐
```
"컬럼 자체가 없음"과 "셀이 비어 있음"을 동일하게 취급한다(`row.get(field)`가 `None`이든 `""`이든
blank로 판정). 이미 값이 채워진 필드(직접 입력 또는 병합 결과)는 덮어쓰지 않는다.

### 6.4 대소문자 정규화
`rule_action`("Allow"/"Deny"처럼 대문자로 들어와도) PAN-OS가 소문자만 허용하므로 `strip().lower()`.
`disabled`는 `TRUE/YES/Y/1`(대소문자 무시) → bool.

### 6.5 실제 엑셀 파일 파싱 (환경 종속적인 부분 — 이식 시 이 부분만 교체하면 됨)
```python
def parse_uploaded_excel(file_bytes: bytes) -> list:
    import xlwings as xw          # 실제 Excel 앱을 백그라운드로 띄워서 연다
    ...
    app = xw.App(visible=False, add_book=False)
    book = app.books.open(temp_path)
    values = book.sheets[0].used_range.value
    ...
    return rows_from_sheet_values(values)   # 실제 파싱은 순수 함수에 위임
```
이 프로젝트는 회사 DRM이 걸린 xlsx를 열어야 해서 `xlwings`(로컬에 MS Excel 설치 필요)를 쓴다.
**DRM이 없는 일반 환경이라면 `openpyxl.load_workbook(...).active.iter_rows()`로 2차원 값을 뽑아서
그대로 `rows_from_sheet_values`에 넘기면 되고, xlwings/Excel 설치 의존성 자체가 필요 없다.**
이식할 프로젝트가 Linux 서버라면 반드시 openpyxl 경로를 쓸 것 — xlwings는 Windows/macOS +
Excel 설치가 필수라 서버 배포에 못 쓴다.

## 7. Excel 없이 "붙여넣기"로 대량 생성 (서비스 오브젝트)

정책 그리드는 xlsx 업로드가 있지만, 서비스 오브젝트처럼 **컬럼이 3~4개뿐인 단순한 데이터**는
굳이 파일 업로드까지 안 가고 **엑셀에서 복사한 셀을 텍스트박스에 그대로 붙여넣는** 방식으로도
충분하다. 엑셀에서 셀 범위를 복사하면 클립보드에 "탭으로 컬럼 구분, 줄바꿈으로 행 구분"된 텍스트가
들어가므로, 이를 그대로 파싱한다 — **xlwings/openpyxl 등 서버 사이드 엑셀 의존성이 전혀 필요 없다.**

```js
function fillServiceRowsFromPaste() {
    const lines = textarea.value.split(/\r?\n/).map(l => l.trim()).filter(Boolean);
    for (const line of lines) {
        const cells = (line.includes('\t') ? line.split('\t') : line.split(',')).map(c => c.trim());
        // 3칸 = name/protocol/port, 4칸 = vsys/name/protocol/port
        const [vsys, name, protocol, port] = cells.length >= 4
            ? cells : ['', cells[0] || '', cells[1] || '', cells[2] || ''];
        // ...행으로 추가, protocol이 tcp/udp가 아니면 tcp로 기본값 처리
    }
}
```
탭이 없으면 콤마로도 시도한다(CSV 붙여넣기 대응). **간단한 표 데이터를 대량 입력받아야 하는데
서버에 실제 엑셀 파싱 라이브러리를 두고 싶지 않다면, 파일 업로드보다 이 "붙여넣기 파싱"이 훨씬
가볍고 이식하기 쉬운 패턴이다.**

## 8. API 엔드포인트 요약

| Method | Path | 설명 |
|---|---|---|
| GET | `/api/paloalto/defaults` | 저장된 기본값 조회 |
| POST | `/api/paloalto/defaults` | 기본값 저장 (그리드 프리필용) |
| POST | `/api/paloalto/generate-bulk` | 정책 행 배열 → 명령어 배열 (그리드용) |
| POST | `/api/paloalto/generate-service-bulk` | 서비스 오브젝트 행 배열 → 명령어 배열 |
| GET | `/api/paloalto/template` | 정책용 xlsx 템플릿 다운로드 (헤더 + 예시행 + 연속행 예시) |
| POST | `/api/paloalto/generate-bulk-excel` | xlsx 업로드 → 병합·기본값 채움·명령어 생성까지 한 번에 |

모든 bulk 엔드포인트의 응답 형태는 동일하게 통일:
```json
{"results": [{"row_index": 0, "command": "...", "error": null, "counts": {"source": 2}}]}
```
행 하나가 실패해도 나머지는 계속 처리된다(하나의 잘못된 행이 전체 요청을 막지 않음) — 대량
입력에서 중요한 원칙.

## 9. 다른 프로젝트에 이식할 때 가져가면 좋은 것 / 이 프로젝트라서 특수한 것

**그대로 가져가도 좋은 범용 패턴**
- `rows_from_sheet_values`의 연속 행 병합 로직 (헤더 기반 매핑 + "키 컬럼이 비면 이전 레코드에 병합")
- `apply_defaults`의 "컬럼 없음과 셀 빈값을 동일하게 취급해서 저장된 기본값으로 채우기"
- 액션(또는 레코드 타입)별로 필요한 필드만 보여주는 조건부 UI 그리드 + `display: contents` 트릭
- delete처럼 "값 조합에 제약이 있는" 액션은 자유 입력을 주지 말고 UI 구조로 제약을 강제하기
- bulk 응답에서 행 하나 실패해도 나머지는 계속 처리, `row_index`로 매핑해서 결과 보여주기
- "여러 값을 병합/집계하는 기능"에는 반드시 "개수 등으로 검증할 수 있는 정보"를 같이 반환하기
- 대용량 파일 업로드보다, 클립보드 텍스트(탭 구분) 붙여넣기가 더 가벼운 대안일 수 있다는 점

**이 프로젝트 특수 사항 (그대로 이식하면 안 되는 부분)**
- `xlwings` 기반 파싱은 회사 DRM 대응용. 일반 환경/서버 배포에는 `openpyxl`로 교체할 것.
- CLI 명령어 문법(`set rulebase security rules ...`, `[ a b ]` 리스트 표기 등)은 PAN-OS 고유 문법.
- `data/paloalto_defaults.json` 단일 파일에 전역 기본값 저장 — 다중 사용자 환경이라면 사용자별/
  세션별로 분리해야 함(현재는 로컬 1인 도구 가정).

## 10. 알려진 제약 (이식 시 고려)

- 엑셀 헤더 오타 시 조용히 무시됨(경고 없음) — 이식할 때는 "알 수 없는 컬럼" 경고를 추가하는 걸 권장.
- rule_name/anchor_rule 등에 큰따옴표(`"`)가 포함되면 이스케이프 처리가 없어 CLI가 깨질 수 있음.
- `data/paloalto_defaults.json` 저장에 파일 락이 없어 동시 저장 시 경쟁 조건 가능(단일 사용자 도구라 실질 위험은 낮음).
- 엑셀은 항상 첫 번째 시트만 읽음.

## 11. 참고 파일

- `app/services/paloalto.py` — 명령어 생성 로직 (가장 먼저 읽을 파일)
- `app/services/paloalto_excel.py` — 병합/기본값/엑셀 파싱
- `app/schemas/paloalto.py` — 요청 계약
- `app/api/routers/paloalto.py` — 엔드포인트
- `static/js/modules/paloalto.js` — 그리드 상태/렌더링
- `templates/components/views/paloalto.html` — 마크업 + `<template>` 정의
- `tests/test_paloalto.py` — 위 로직 전체에 대한 유닛 테스트 (동작 규격서로도 활용 가능)
