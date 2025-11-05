# HTML 셀렉터 검증 결과

## 코드에서 사용하는 셀렉터와 HTML 요소 매칭

### ✅ 확인된 요소들

#### 1. 검색 관련 요소
- **`select_key`** (line 145)
  - HTML: `<select name="select_key">` ✓ 존재
  - 위치: 검색 영역 하단
  
- **`s_keyword`** (line 149)
  - HTML: `<input type="text" name="s_keyword" value="" ...>` ✓ 존재
  - 위치: 검색 영역 하단

- **`btn_s_keyword`** (line 155)
  - HTML: `<input type="button" name="btn_s_keyword" value="검색" ...>` ✓ 존재
  - 위치: 검색 영역 하단

#### 2. 테이블 관련 요소
- **테이블 행** (line 160)
  - CSS Selector: `table tr.list_text, table tr.graycell`
  - HTML: 
    ```html
    <tr class="list_text">
    <tr class="graycell">
    ```
  - ✓ 존재

- **이름 링크** (line 166)
  - CSS Selector: `td a[name='nb']`
  - HTML: `<td onclick="..."><a style="..." name="nb" href="javascript:view('...')">장건우</a></td>`
  - ✓ 존재 (name 속성이 있음)

- **연락처 추출** (line 170-172)
  - HTML 구조: `<td>` 요소들 (8개 컬럼)
  - 연락처는 마지막 `<td>` (인덱스 7)
  - ✓ 구조 확인됨

- **체크박스** (line 177)
  - CSS Selector: `input[type='checkbox'][name='nb']`
  - HTML: `<input type="checkbox" name="nb" value="..." onclick="...">`
  - ✓ 존재

#### 3. 배정하기 버튼 (line 205)
- XPath: `//input[@value='배정하기']`
- HTML: `<input type="button" class="btn_style01" name="" value="배정하기" onclick="javascript:upta_view();">`
- ✓ 존재 (value 속성으로 찾을 수 있음)

### ⚠️ 주의사항

#### 1. 배정하기 버튼의 name 속성
- HTML에서 `name=""` (빈 문자열)
- 코드는 `value='배정하기'`로 찾으므로 문제 없음 ✓

#### 2. 연락처 컬럼 위치
- 코드는 `tds[7]` (8번째 컬럼)에서 연락처를 추출
- HTML 구조 확인:
  ```html
  <th>성명</th>
  <th>다락방</th>
  <th>순</th>
  <th>나이</th>
  <th>공동체직임</th>
  <th>상태</th>
  <th>휴대폰</th>  <!-- 7번째 컬럼 (인덱스 6) -->
  ```
- ⚠️ **문제 발견**: 휴대폰은 7번째 컬럼이지만, 체크박스가 첫 번째 컬럼이므로 실제 인덱스는:
  - 체크박스: 0
  - 성명: 1
  - 다락방: 2
  - 순: 3
  - 나이: 4
  - 공동체직임: 5
  - 상태: 6
  - 휴대폰: 7 ✓ (코드가 맞음)

#### 3. 팝업 창 처리
- 배정하기 버튼 클릭 시 팝업 창이 열릴 수 있음
- 코드에서 `window_handles` 체크로 처리하고 있음 ✓

### ✅ 팝업 창 요소 (배정하기 클릭 후 열리는 창)

#### 1. 다락방 선택 (line 227-259)
- **Select 요소**: `By.NAME, "dlb_nm"`
  - HTML: `<select name="dlb_nm" size="13" onclick="javascript:soonlist(this.selectedIndex)">` ✓ 존재
  - Option 구조: `<option value="86694">권세은</option>`
  - 코드: `Select(dlb_select).select_by_visible_text(d_group)` ✓ 올바름
  - **soonlist 함수 호출**: `driver.execute_script(f"soonlist({selected_index});")` ✓ 올바름
  - HTML에서 `onclick="javascript:soonlist(this.selectedIndex)"`이므로 함수 호출이 필요 ✓

#### 2. 순장 선택 (line 264-274)
- **Select 요소**: `By.NAME, "soon_nm"`
  - HTML: `<select name="soon_nm" size="10" onclick="javascript:soonclick();">` ✓ 존재
  - 초기에는 비어있고, 다락방 선택 후 JavaScript로 채워짐
  - 코드: `Select(soon_select).select_by_visible_text(leader_name)` ✓ 올바름
  - **주의**: 다락방 선택 후 `soonlist()` 함수가 실행되어 순 목록이 채워져야 함 ✓

#### 3. 저장 버튼 (line 276-280)
- **순 저장 버튼**: `By.ID, "btnsoon"`
  - HTML: `<input type="button" id="btnsoon" name="btnsoon" value="저장" onclick="javascript:organize(this.name,document.form.soon_nm.value);">` ✓ 존재
  - 코드: `By.ID, "btnsoon"` ✓ 올바름
  - **주의**: 다락방 저장 버튼(`id="btndlb"`)이 아닌 순 저장 버튼 사용 ✓

#### 4. 팝업 창 전환 (line 211-215)
- `window_handles` 체크로 팝업 창 감지 ✓
- `driver.switch_to.window(window_handles[-1])` ✓ 올바름

## 권장 수정 사항

### 1. 연락처 추출 로직 개선
현재 코드는 `tds[7]`을 사용하는데, 더 안전하게 하려면:
```python
# 연락처 추출을 더 안전하게
phone_td = None
for td in tds:
    td_text = td.text.strip().replace("-", "").replace(" ", "")
    if len(td_text) >= 10 and td_text.startswith("010"):
        phone_td = td
        break
```

### 2. 체크박스 선택 로직 개선
체크박스가 이미 선택되어 있을 수 있으므로:
```python
checkbox = row.find_element(By.CSS_SELECTOR, "input[type='checkbox'][name='nb']")
if not checkbox.is_selected():
    driver.execute_script("arguments[0].click();", checkbox)
```

## 결론

✅ **모든 페이지의 주요 요소들이 확인됨**

### commPsMod.do 페이지 (메인)
- 검색 관련 요소: ✓
- 테이블 구조: ✓
- 체크박스: ✓
- 배정하기 버튼: ✓

### 팝업 창 (배정하기 클릭 후)
- 다락방 Select: ✓
- 순장 Select: ✓
- 저장 버튼: ✓
- soonlist 함수 호출: ✓

## ⚠️ 주의사항 및 테스트 포인트

### 1. 다락방 선택 후 순 목록 업데이트
- 다락방을 선택하면 `soonlist(selectedIndex)` 함수가 호출되어 순 목록이 채워짐
- 코드에서 `driver.execute_script(f"soonlist({selected_index});")` 호출 ✓
- 1.5초 대기 시간 설정됨 ✓

### 2. 여러 명 배정 시 팝업 처리
- 현재 코드는 각 사람마다 배정을 진행하지만, 팝업이 닫힌 후 다시 열려야 할 수 있음
- 실제 테스트에서 팝업이 닫히는지 확인 필요
- 팝업이 닫히면 메인 페이지로 돌아가서 다음 사람을 선택해야 할 수 있음

### 3. 순 목록의 동적 로딩
- 순 목록은 JavaScript로 동적으로 채워지므로, 다락방 선택 후 충분한 대기 시간 필요
- 현재 1.5초 대기 설정됨 (필요시 조정 가능)

## 최종 검증 결과

✅ **모든 셀렉터가 HTML 구조와 일치함**
- 코드는 실제 HTML 구조를 올바르게 반영하고 있음
- 실제 테스트 시 정상 작동할 것으로 예상됨
- 단, 여러 명 배정 시 팝업 창 처리 로직은 실제 테스트로 검증 필요

