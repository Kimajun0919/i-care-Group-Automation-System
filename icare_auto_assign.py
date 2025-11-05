# ==========================================
# 아이케어(iOnnuri) 순배정 자동화 샘플 코드
# ==========================================

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait, Select
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
from webdriver_manager.chrome import ChromeDriverManager
import time, json, os, csv
from datetime import datetime

# ------------------------------------------
# 0. 설정
# ------------------------------------------
LOGIN_URL = "https://icare.ionnuri.org"  # 로그인 페이지
COMMUNITY_URL = "https://icare.ionnuri.org/admin/community/assign"  # 순배정 페이지 URL (실제 맞게 수정)

ADMIN_ID = "YOUR_ID_HERE"
ADMIN_PW = "YOUR_PASSWORD_HERE"

# CSV 파일에서 데이터 읽기
def load_data_from_csv(filename="data.csv"):
    """CSV 파일에서 다락방, 순장, 이름, 연락처 정보 읽기"""
    data_list = []
    try:
        with open(filename, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                data_list.append({
                    "d_group": row["다락방"].strip(),
                    "leader_name": row["순장"].strip(),
                    "name": row["이름"].strip(),
                    "phone": row["연락처"].strip().replace("-", "")
                })
        print(f"✅ CSV 파일에서 {len(data_list)}명의 데이터 로드 완료")
        return data_list
    except Exception as e:
        print(f"❌ CSV 파일 읽기 오류: {e}")
        return []

# CSV 데이터 로드
TARGET_DATA = load_data_from_csv()

# 진행상황 로그 함수
def log_progress(message, status="info"):
    """진행상황을 타임스탬프와 함께 출력"""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    status_symbol = {
        "info": "ℹ️",
        "success": "✅",
        "error": "❌",
        "warning": "⚠️",
        "progress": "🔄"
    }.get(status, "ℹ️")
    print(f"[{timestamp}] {status_symbol} {message}")

# ------------------------------------------
# 1. 드라이버 초기화
# ------------------------------------------
log_progress("드라이버 초기화 시작", "info")
options = webdriver.ChromeOptions()
options.add_argument("--start-maximized")
driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
wait = WebDriverWait(driver, 10)
log_progress("크롬 브라우저 실행 완료", "success")

# ------------------------------------------
# 2. 로그인 (쿠키 자동 사용)
# ------------------------------------------
log_progress("로그인 프로세스 시작", "progress")
if os.path.exists("cookies.json"):
    log_progress("쿠키 파일 발견 - 자동 로그인 시도", "info")
    driver.get(LOGIN_URL)
    with open("cookies.json", "r", encoding="utf-8") as f:
        cookies = json.load(f)
    for cookie in cookies:
        if "sameSite" in cookie:
            cookie.pop("sameSite")
        driver.add_cookie(cookie)
    driver.refresh()
    log_progress("쿠키 로그인 완료", "success")
    time.sleep(2)
else:
    log_progress("쿠키 파일 없음 - 수동 로그인 진행", "info")
    driver.get(LOGIN_URL)

    # ID / PW 입력
    wait.until(EC.presence_of_element_located((By.ID, "userid"))).send_keys(ADMIN_ID)
    driver.find_element(By.NAME, "password").send_keys(ADMIN_PW)

    # 로그인 버튼 클릭
    driver.find_element(By.ID, "loginBtn").click()
    time.sleep(3)

    # 쿠키 저장
    cookies = driver.get_cookies()
    with open("cookies.json", "w", encoding="utf-8") as f:
        json.dump(cookies, f)
    log_progress("로그인 쿠키 저장 완료", "success")

# ------------------------------------------
# 3. 아이케어 페이지로 이동
# ------------------------------------------
log_progress("아이케어 페이지로 이동 중...", "progress")
CARE_STATE_URL = "https://icare.ionnuri.org/yecare/careState.do"
driver.get(CARE_STATE_URL)
wait.until(EC.presence_of_element_located((By.TAG_NAME, "body")))
log_progress("아이케어 페이지 로드 완료", "success")
time.sleep(2)

# ------------------------------------------
# 4. 공동체 순배정 수정 페이지로 이동
# ------------------------------------------
log_progress("공동체 순배정 수정 페이지로 이동 중...", "progress")
COMM_PS_MOD_URL = "https://icare.ionnuri.org/yecare/commPsMod.do"
driver.get(COMM_PS_MOD_URL)
wait.until(EC.presence_of_element_located((By.TAG_NAME, "body")))
log_progress("공동체 순배정 수정 페이지 로드 완료", "success")
time.sleep(2)

# ------------------------------------------
# 5. CSV 데이터 기반 이름 검색 및 선택
# ------------------------------------------
if not TARGET_DATA:
    log_progress("CSV 데이터가 없습니다. 프로그램을 종료합니다.", "error")
    log_progress("브라우저는 유지됩니다. 수동으로 종료하세요.", "info")
    input("계속하려면 Enter 키를 누르세요...")
    exit()

log_progress(f"총 {len(TARGET_DATA)}명의 데이터 처리 시작", "info")
selected_count = 0
selected_list = []

for idx, person in enumerate(TARGET_DATA, 1):
    name = person["name"]
    phone = person["phone"]
    
    log_progress(f"[{idx}/{len(TARGET_DATA)}] 검색 중: {name} ({phone})", "progress")
    
    try:
        # 검색 타입을 "이름"으로 설정
        select_key = wait.until(EC.presence_of_element_located((By.NAME, "select_key")))
        driver.execute_script("arguments[0].value = 'name';", select_key)
        
        # 검색어 입력
        search_input = wait.until(EC.presence_of_element_located((By.NAME, "s_keyword")))
        search_input.clear()
        search_input.send_keys(name)
        time.sleep(0.5)
        
        # 검색 버튼 클릭
        search_btn = wait.until(EC.element_to_be_clickable((By.NAME, "btn_s_keyword")))
        search_btn.click()
        time.sleep(2)
        
        # 검색 결과 테이블에서 이름과 연락처 일치하는 행 찾기
        table_rows = driver.find_elements(By.CSS_SELECTOR, "table tr.list_text, table tr.graycell")
        
        found = False
        for row in table_rows:
            try:
                # 이름 추출 (a 태그 내부)
                name_link = row.find_element(By.CSS_SELECTOR, "td a[name='nb']")
                name_text = name_link.text.strip()
                
                # 연락처 추출 (마지막 td 또는 010으로 시작하는 셀)
                tds = row.find_elements(By.TAG_NAME, "td")
                if len(tds) >= 8:
                    # 마지막 td에서 연락처 추출 (인덱스 7 = 8번째 컬럼)
                    phone_text = tds[7].text.strip().replace("-", "").replace(" ", "")
                    
                    # 이름과 연락처가 일치하는지 확인
                    if name_text == name and phone_text == phone:
                        # 체크박스 선택
                        checkbox = row.find_element(By.CSS_SELECTOR, "input[type='checkbox'][name='nb']")
                        if not checkbox.is_selected():
                            driver.execute_script("arguments[0].click();", checkbox)
                            log_progress(f"  선택 완료: {name_text} / {phone_text}", "success")
                            selected_count += 1
                            selected_list.append(name)
                            found = True
                            break
            except Exception as e:
                continue
        
        if not found:
            log_progress(f"  일치하는 항목을 찾을 수 없습니다: {name} / {phone}", "warning")
            
    except Exception as e:
        log_progress(f"  검색 중 오류 발생: {e}", "error")
        continue

log_progress(f"총 {selected_count}명 선택 완료", "success")
if selected_list:
    log_progress(f"선택된 인원: {', '.join(selected_list)}", "info")

# ------------------------------------------
# 6. 배정하기 버튼 클릭
# ------------------------------------------
if selected_count > 0:
    try:
        log_progress("배정하기 버튼 클릭 중...", "progress")
        assign_btn = wait.until(EC.element_to_be_clickable((By.XPATH, "//input[@value='배정하기']")))
        assign_btn.click()
        time.sleep(2)
        log_progress("배정창 열림", "success")
        
        # 팝업 창으로 전환 (새 창이 열린 경우)
        window_handles = driver.window_handles
        if len(window_handles) > 1:
            driver.switch_to.window(window_handles[-1])
            wait.until(EC.presence_of_element_located((By.TAG_NAME, "body")))
            log_progress("팝업 창으로 전환 완료", "success")
        
        # 각 사람에 대해 다락방과 순장 선택
        log_progress(f"{len(TARGET_DATA)}명에 대한 배정 시작", "progress")
        for idx, person in enumerate(TARGET_DATA, 1):
            d_group = person["d_group"]
            leader_name = person["leader_name"]
            
            log_progress(f"[{idx}/{len(TARGET_DATA)}] 배정 중: {person['name']} → {d_group} / {leader_name}", "progress")
            
            try:
                # 다락방 선택 (select 요소에서 option 선택)
                log_progress(f"  다락방 선택: {d_group}", "info")
                dlb_select = wait.until(EC.presence_of_element_located((By.NAME, "dlb_nm")))
                dlb_dropdown = Select(dlb_select)
                
                # option의 텍스트로 선택 시도
                try:
                    dlb_dropdown.select_by_visible_text(d_group)
                    # 다락방 선택 시 soonlist 함수 호출하여 순 목록 업데이트
                    # HTML에서 onclick="javascript:soonlist(this.selectedIndex)"이므로
                    selected_index = [i for i, option in enumerate(dlb_select.find_elements(By.TAG_NAME, "option")) 
                                     if option.text.strip() == d_group][0]
                    driver.execute_script(f"soonlist({selected_index});", dlb_select)
                    log_progress(f"  다락방 '{d_group}' 선택 완료 (인덱스: {selected_index})", "success")
                except Exception as e:
                    # 텍스트로 찾지 못하면 JavaScript로 직접 선택
                    log_progress(f"  텍스트로 찾지 못함, JavaScript로 시도: {e}", "warning")
                    selected_index = driver.execute_script(f"""
                        var select = document.getElementsByName('dlb_nm')[0];
                        for(var i = 0; i < select.options.length; i++) {{
                            if(select.options[i].text === '{d_group}') {{
                                select.selectedIndex = i;
                                soonlist(i);
                                return i;
                            }}
                        }}
                        return -1;
                    """)
                    if selected_index == -1:
                        log_progress(f"  다락방 '{d_group}'을 찾을 수 없습니다.", "error")
                        continue
                    time.sleep(1)  # 순 목록 업데이트 대기
                    log_progress(f"  다락방 선택 완료 (JavaScript, 인덱스: {selected_index})", "success")
                
                # 순 목록이 업데이트될 때까지 대기 (JavaScript 실행 시간)
                time.sleep(1.5)
                
                # 순장 선택 (select 요소에서 option 선택)
                log_progress(f"  순장 선택: {leader_name}", "info")
                soon_select = wait.until(EC.presence_of_element_located((By.NAME, "soon_nm")))
                soon_dropdown = Select(soon_select)
                
                try:
                    soon_dropdown.select_by_visible_text(leader_name)
                    log_progress(f"  순장 '{leader_name}' 선택 완료", "success")
                except:
                    log_progress(f"  순장 '{leader_name}'을 찾을 수 없습니다. 해당 다락방의 순 목록을 확인하세요.", "warning")
                    continue
                
                # 순 저장 버튼 클릭 (순을 선택했으므로 순 저장 버튼 사용)
                log_progress(f"  순 배정 저장 중...", "info")
                soon_save_btn = wait.until(EC.element_to_be_clickable((By.ID, "btnsoon")))
                soon_save_btn.click()
                time.sleep(2)
                log_progress(f"  배정 저장 완료: {person['name']} → {d_group} / {leader_name}", "success")
                
                # 팝업이 닫히고 다시 열릴 수 있으므로, 메인 페이지로 돌아가거나 다시 배정하기 버튼 클릭 필요
                # 여러 명을 배정하는 경우, 팝업이 닫혔다가 다시 열려야 함
                time.sleep(1)
                
            except TimeoutException as e:
                log_progress(f"  배정 실패: {e}", "error")
                continue
            except Exception as e:
                log_progress(f"  배정 중 오류 발생: {e}", "error")
                continue
            
    except Exception as e:
        log_progress(f"배정 과정 오류: {e}", "error")
else:
    log_progress("선택된 항목이 없어 배정을 진행할 수 없습니다.", "warning")

log_progress("순배정 자동화 작업 완료", "success")
log_progress("브라우저는 유지됩니다. 수동으로 종료하거나 다음 작업을 진행하세요.", "info")
log_progress("=" * 60, "info")
