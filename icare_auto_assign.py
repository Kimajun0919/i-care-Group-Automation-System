# ==========================================
# 아이케어(iOnnuri) 순배정 자동화 샘플 코드
# ==========================================

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait, Select
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoAlertPresentException
from webdriver_manager.chrome import ChromeDriverManager
import time, json, os, csv
from datetime import datetime
from getpass import getpass

# ------------------------------------------
# 0. 설정
# ------------------------------------------
LOGIN_URL = "https://icare.ionnuri.org"  # 로그인 페이지
COMMUNITY_URL = "https://icare.ionnuri.org/admin/community/assign"  # 순배정 페이지 URL (실제 맞게 수정)

# 아이디와 비밀번호는 실행 시 입력받음
ADMIN_ID = None
ADMIN_PW = None

# 진행상황 로그 함수 (먼저 정의 필요)
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

# CSV 파일에서 데이터 읽기
def load_data_from_csv(filename="data.csv"):
    """CSV 파일에서 다락방, 순장, 이름, 연락처 정보 읽기 (헤더 유연성 추가, 동명이인 필터링)"""
    data_list = []
    try:
        with open(filename, "r", encoding="utf-8-sig") as f:  # BOM 처리
            reader = csv.DictReader(f)
            headers = reader.fieldnames
            
            # 헤더 매핑 (공백 제거 후 비교)
            header_map = {h.strip(): h for h in headers} if headers else {}
            
            for row in reader:
                full_name = row.get(header_map.get("이름", "이름"), "").strip()
                # 이름을 앞 세 글자만 사용
                name_3chars = full_name[:3] if len(full_name) >= 3 else full_name
                data_list.append({
                    "d_group": row.get(header_map.get("다락방", "다락방"), "").strip(),
                    "leader_name": row.get(header_map.get("순장", "순장"), "").strip(),
                    "name": name_3chars,
                    "phone": row.get(header_map.get("연락처", "연락처"), "").strip().replace("-", "").replace(" ", "")
                })
        
        # 동명이인 필터링: 이름이 중복되는 항목들을 모두 제거
        name_count = {}
        for person in data_list:
            name = person["name"]
            if name:
                name_count[name] = name_count.get(name, 0) + 1
        
        # 동명이인 제거
        filtered_list = []
        duplicate_names = set()
        for person in data_list:
            name = person["name"]
            if name and name_count.get(name, 0) == 1:
                filtered_list.append(person)
            elif name and name_count.get(name, 0) > 1:
                duplicate_names.add(name)
        
        if duplicate_names:
            log_progress(f"CSV 데이터에서 동명이인 발견: {', '.join(sorted(duplicate_names))}", "warning")
            log_progress(f"동명이인 {len(duplicate_names)}개 이름의 항목들을 제외합니다.", "info")
        
        removed_count = len(data_list) - len(filtered_list)
        if removed_count > 0:
            log_progress(f"동명이인 {removed_count}명 제외, {len(filtered_list)}명의 데이터 로드 완료", "success")
        else:
            log_progress(f"CSV 파일에서 {len(filtered_list)}명의 데이터 로드 완료", "success")
        
        return filtered_list
    except FileNotFoundError:
        log_progress(f"'{filename}' 파일을 찾을 수 없습니다.", "error")
        return []
    except Exception as e:
        log_progress(f"CSV 파일 읽기 오류: {e}", "error")
        return []

# CSV 데이터 로드
TARGET_DATA = load_data_from_csv()

# Alert 처리 함수
def handle_alert(driver, accept=True):
    """alert 처리"""
    try:
        alert = driver.switch_to.alert
        alert_text = alert.text
        if accept:
            alert.accept()
        else:
            alert.dismiss()
        return alert_text
    except NoAlertPresentException:
        return None

# 안전한 클릭 함수
def wait_and_click(driver, by, value, wait_time=10):
    """요소 대기 후 클릭 (안전한 클릭)"""
    element = WebDriverWait(driver, wait_time).until(
        EC.element_to_be_clickable((by, value))
    )
    driver.execute_script("arguments[0].scrollIntoView(true);", element)
    time.sleep(0.3)
    driver.execute_script("arguments[0].click();", element)
    return element

# ------------------------------------------
# 1. 아이디/비밀번호 입력
# ------------------------------------------
log_progress("로그인 정보 입력", "info")
if ADMIN_ID is None or ADMIN_PW is None:
    ADMIN_ID = input("아이디를 입력하세요: ").strip()
    ADMIN_PW = getpass("비밀번호를 입력하세요: ").strip()
    if not ADMIN_ID or not ADMIN_PW:
        log_progress("아이디 또는 비밀번호가 입력되지 않았습니다.", "error")
        exit()
    log_progress("로그인 정보 입력 완료", "success")

# ------------------------------------------
# 2. 드라이버 초기화
# ------------------------------------------
log_progress("드라이버 초기화 시작", "info")
options = webdriver.ChromeOptions()
options.add_argument("--start-maximized")
options.add_argument("--disable-blink-features=AutomationControlled")
driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
wait = WebDriverWait(driver, 10)
log_progress("크롬 브라우저 실행 완료", "success")

# ------------------------------------------
# 3. 로그인 (쿠키 자동 사용)
# ------------------------------------------
log_progress("로그인 프로세스 시작", "progress")
try:
    if os.path.exists("cookies.json"):
        log_progress("쿠키 파일 발견 - 자동 로그인 시도", "info")
        driver.get(LOGIN_URL)
        with open("cookies.json", "r", encoding="utf-8") as f:
            cookies = json.load(f)
        for cookie in cookies:
            cookie.pop("sameSite", None)
            try:
                driver.add_cookie(cookie)
            except:
                pass
        driver.refresh()
        time.sleep(2)
        
        # 로그인 확인 (로그인 폼이 여전히 있으면 실패)
        if driver.find_elements(By.ID, "userid"):
            log_progress("쿠키 만료 - 수동 로그인 필요", "warning")
            os.remove("cookies.json")
            raise Exception("Cookie expired")
        log_progress("쿠키 로그인 완료", "success")
    else:
        raise Exception("No cookies")
except:
    log_progress("수동 로그인 진행", "info")
    driver.get(LOGIN_URL)

    # ID / PW 입력
    wait.until(EC.presence_of_element_located((By.ID, "userid"))).send_keys(ADMIN_ID)
    driver.find_element(By.NAME, "password").send_keys(ADMIN_PW)

    # 로그인 버튼 클릭
    driver.find_element(By.ID, "loginBtn").click()
    time.sleep(3)
    
    # 로그인 성공 확인
    if driver.find_elements(By.ID, "userid"):
        log_progress("로그인 실패 - ID/PW 확인 필요", "error")
        log_progress("브라우저는 유지됩니다. 수동으로 종료하세요.", "info")
        input("계속하려면 Enter 키를 누르세요...")
        driver.quit()
        exit()

    # 쿠키 저장
    cookies = driver.get_cookies()
    with open("cookies.json", "w", encoding="utf-8") as f:
        json.dump(cookies, f)
    log_progress("로그인 성공 및 쿠키 저장 완료", "success")

# ------------------------------------------
# 4. 아이케어 페이지로 이동
# ------------------------------------------
log_progress("아이케어 페이지로 이동 중...", "progress")
CARE_STATE_URL = "https://icare.ionnuri.org/yecare/careState.do"
driver.get(CARE_STATE_URL)
wait.until(EC.presence_of_element_located((By.TAG_NAME, "body")))
log_progress("아이케어 페이지 로드 완료", "success")
time.sleep(2)

# ------------------------------------------
# 5. 공동체 순배정 수정 페이지로 이동
# ------------------------------------------
log_progress("공동체 순배정 수정 페이지로 이동 중...", "progress")
COMM_PS_MOD_URL = "https://icare.ionnuri.org/yecare/commPsMod.do"
driver.get(COMM_PS_MOD_URL)
wait.until(EC.presence_of_element_located((By.TAG_NAME, "body")))
log_progress("공동체 순배정 수정 페이지 로드 완료", "success")
time.sleep(2)

# ------------------------------------------
# 6. CSV 데이터 기반 이름 검색 및 선택
# ------------------------------------------
if not TARGET_DATA:
    log_progress("CSV 데이터가 없습니다. 프로그램을 종료합니다.", "error")
    log_progress("브라우저는 유지됩니다. 수동으로 종료하세요.", "info")
    input("계속하려면 Enter 키를 누르세요...")
    exit()

log_progress(f"총 {len(TARGET_DATA)}명의 데이터 처리 시작", "info")
processed_count = 0
failed_count = 0
failed_list = []  # 실패한 인원 정보 저장

# 각 사람마다 검색 → 선택 → 배정하기 → 배정을 반복
for idx, person in enumerate(TARGET_DATA, 1):
    name = person["name"]
    phone = person["phone"]
    d_group = person["d_group"]
    leader_name = person["leader_name"]
    
    log_progress(f"\n[{idx}/{len(TARGET_DATA)}] 처리 시작: {name} → {d_group} / {leader_name}", "progress")
    
    try:
        # 페이지 새로고침 (이전 선택 초기화)
        driver.get(COMM_PS_MOD_URL)
        time.sleep(1.5)
        
        # ------------------------------------------
        # 6. 검색 및 선택
        # ------------------------------------------
        log_progress(f"  검색 중: {name}", "info")
        
        # 검색 타입을 "이름"으로 설정
        select_key = wait.until(EC.presence_of_element_located((By.NAME, "select_key")))
        driver.execute_script("arguments[0].value = 'name';", select_key)
        
        # 검색어 입력
        search_input = wait.until(EC.presence_of_element_located((By.NAME, "s_keyword")))
        search_input.clear()
        search_input.send_keys(name)
        time.sleep(0.5)
        
        # 검색 버튼 클릭
        wait_and_click(driver, By.NAME, "btn_s_keyword")
        time.sleep(2)
        
        # 검색 결과 테이블에서 이름 일치하는 행 찾기
        table_rows = driver.find_elements(By.CSS_SELECTOR, "table tr.list_text, table tr.graycell")
        
        if not table_rows:
            log_progress(f"  검색 결과 없음: {name}", "warning")
            failed_list.append({
                "name": name,
                "phone": phone,
                "d_group": d_group,
                "leader_name": leader_name,
                "reason": "검색 결과 없음"
            })
            failed_count += 1
            continue
        
        # 이름이 일치하는 행들을 모두 찾기
        matching_rows = []
        for row in table_rows:
            try:
                # 이름 추출 (a 태그 내부)
                name_link = row.find_element(By.CSS_SELECTOR, "td a[name='nb']")
                name_text = name_link.text.strip()
                # 검색 결과 이름도 앞 세 글자만 비교
                name_text_3chars = name_text[:3] if len(name_text) >= 3 else name_text
                
                # 이름이 일치하는 경우 (앞 세 글자 기준)
                if name_text_3chars == name:
                    matching_rows.append(row)
            except Exception:
                continue
        
        # 동명이인 검증: 여러 명이 검색 결과에 나오면 입력하지 않음
        if len(matching_rows) > 1:
            log_progress(f"  동명이인 발견: {name} ({len(matching_rows)}명)", "warning")
            failed_count += 1
            failed_list.append({
                "name": name,
                "phone": phone,
                "d_group": d_group,
                "leader_name": leader_name,
                "reason": f"동명이인 발견 ({len(matching_rows)}명)"
            })
            continue
        
        # 일치하는 항목이 하나인 경우
        if len(matching_rows) == 1:
            row = matching_rows[0]
            try:
                # 체크박스 선택
                checkbox = row.find_element(By.CSS_SELECTOR, "input[type='checkbox'][name='nb']")
                if not checkbox.is_selected():
                    driver.execute_script("arguments[0].click();", checkbox)
                    log_progress(f"  선택 완료: {name}", "success")
            except Exception as e:
                log_progress(f"  체크박스 선택 실패: {e}", "error")
                failed_count += 1
                failed_list.append({
                    "name": name,
                    "phone": phone,
                    "d_group": d_group,
                    "leader_name": leader_name,
                    "reason": f"체크박스 선택 실패: {str(e)}"
                })
                continue
        else:
            log_progress(f"  일치하는 항목을 찾을 수 없습니다: {name}", "warning")
            failed_count += 1
            failed_list.append({
                "name": name,
                "phone": phone,
                "d_group": d_group,
                "leader_name": leader_name,
                "reason": "검색 결과에서 일치하는 항목을 찾을 수 없음"
            })
            continue
        
        # ------------------------------------------
        # 7. 배정하기 버튼 클릭
        # ------------------------------------------
        log_progress(f"  배정하기 버튼 클릭 중...", "info")
        wait_and_click(driver, By.XPATH, "//input[@value='배정하기']")
        time.sleep(2)
        log_progress(f"  배정창 열림", "success")
        
        # ------------------------------------------
        # 8. 팝업 창으로 전환
        # ------------------------------------------
        window_handles = driver.window_handles
        if len(window_handles) > 1:
            driver.switch_to.window(window_handles[-1])
            wait.until(EC.presence_of_element_located((By.TAG_NAME, "body")))
            log_progress(f"  팝업 창으로 전환 완료", "success")
        
        # ------------------------------------------
        # 9. 다락방과 순장 선택 및 저장
        # ------------------------------------------
        try:
            # 다락방 선택 (JavaScript로 직접 선택 - 더 안정적)
            log_progress(f"  다락방 선택: {d_group}", "info")
            dlb_select = wait.until(EC.presence_of_element_located((By.NAME, "dlb_nm")))
            
            selected_index = driver.execute_script(f"""
                var select = document.getElementsByName('dlb_nm')[0];
                for(var i = 0; i < select.options.length; i++) {{
                    if(select.options[i].text.trim() === '{d_group}') {{
                        select.selectedIndex = i;
                        if(typeof soonlist === 'function') soonlist(i);
                        return i;
                    }}
                }}
                return -1;
            """)
            
            if selected_index == -1:
                log_progress(f"  다락방 '{d_group}'을 찾을 수 없습니다.", "error")
                # 팝업 닫기 및 메인 페이지로 복귀
                try:
                    current_handles = driver.window_handles
                    if len(current_handles) > 1:
                        driver.close()
                        driver.switch_to.window(current_handles[0])
                    else:
                        if current_handles:
                            driver.switch_to.window(current_handles[0])
                except Exception as window_error:
                    log_progress(f"  창 전환 중 오류 (무시): {window_error}", "warning")
                failed_count += 1
                failed_list.append({
                    "name": name,
                    "phone": phone,
                    "d_group": d_group,
                    "leader_name": leader_name,
                    "reason": f"다락방 '{d_group}'을 찾을 수 없음"
                })
                continue
            
            log_progress(f"  다락방 '{d_group}' 선택 완료 (인덱스: {selected_index})", "success")
            
            # 순 목록 업데이트 대기
            time.sleep(1.5)
            
            # 순장 선택
            log_progress(f"  순장 선택: {leader_name}", "info")
            soon_select = wait.until(EC.presence_of_element_located((By.NAME, "soon_nm")))
            soon_dropdown = Select(soon_select)
            
            try:
                soon_dropdown.select_by_visible_text(leader_name)
                log_progress(f"  순장 '{leader_name}' 선택 완료", "success")
            except:
                log_progress(f"  순장 '{leader_name}'을 찾을 수 없습니다.", "warning")
                # 팝업 닫기 및 메인 페이지로 복귀
                try:
                    current_handles = driver.window_handles
                    if len(current_handles) > 1:
                        driver.close()
                        driver.switch_to.window(current_handles[0])
                    else:
                        if current_handles:
                            driver.switch_to.window(current_handles[0])
                except Exception as window_error:
                    log_progress(f"  창 전환 중 오류 (무시): {window_error}", "warning")
                failed_count += 1
                failed_list.append({
                    "name": name,
                    "phone": phone,
                    "d_group": d_group,
                    "leader_name": leader_name,
                    "reason": f"순장 '{leader_name}'을 찾을 수 없음 (다락방: {d_group})"
                })
                continue
            
            # 저장 버튼 클릭
            log_progress(f"  순 배정 저장 중...", "info")
            try:
                wait_and_click(driver, By.ID, "btnsoon")
            except Exception as click_error:
                # 클릭 중 alert가 나타나면 먼저 처리
                try:
                    alert = driver.switch_to.alert
                    alert_text = alert.text
                    alert.accept()
                    log_progress(f"  클릭 중 Alert 처리: {alert_text}", "info")
                    time.sleep(0.5)
                except:
                    pass
                # 클릭 재시도는 하지 않고 계속 진행
            
            # alert 처리 (즉시 대기 및 처리)
            time.sleep(0.5)  # alert가 나타날 시간을 줌
            alert_text = None
            try:
                # alert가 나타날 때까지 짧은 대기
                alert = WebDriverWait(driver, 3).until(EC.alert_is_present())
                alert_text = alert.text
                alert.accept()
                log_progress(f"  Alert: {alert_text}", "info")
                time.sleep(0.5)  # alert 처리 후 대기
            except TimeoutException:
                # alert가 없으면 그냥 진행
                pass
            except Exception as e:
                # alert 처리 중 오류가 발생해도 계속 진행
                log_progress(f"  Alert 처리 중 예외 (무시): {e}", "warning")
            
            time.sleep(1)
            log_progress(f"  배정 저장 완료: {name} → {d_group} / {leader_name}", "success")
            
            # 팝업 닫기 및 메인 페이지로 복귀
            try:
                # alert가 창을 닫았을 수 있으므로 먼저 확인
                current_handles = driver.window_handles
                if len(current_handles) > 1:
                    # 현재 팝업 창이 아직 열려있음
                    try:
                        # 현재 창이 팝업인지 확인
                        driver.switch_to.window(current_handles[-1])
                        driver.close()
                        # 메인 창으로 전환
                        driver.switch_to.window(current_handles[0])
                        time.sleep(1)  # 메인 페이지 로드 대기
                        log_progress(f"  메인 페이지로 복귀 완료", "success")
                    except Exception as close_error:
                        # 창이 이미 닫혔을 수 있음
                        log_progress(f"  팝업 창 닫기 중 오류 (이미 닫혔을 수 있음): {close_error}", "warning")
                        try:
                            if current_handles:
                                driver.switch_to.window(current_handles[0])
                                log_progress(f"  메인 페이지로 복귀 성공", "success")
                        except:
                            pass
                else:
                    # 팝업이 이미 닫혔거나 메인 창만 있는 경우
                    if current_handles:
                        driver.switch_to.window(current_handles[0])
                    log_progress(f"  팝업이 이미 닫혔거나 메인 페이지에 있습니다.", "info")
            except Exception as e:
                # 창 전환 중 오류가 발생하면 메인 페이지로 이동 시도
                log_progress(f"  창 전환 중 오류 (복구 시도): {e}", "warning")
                try:
                    main_handles = driver.window_handles
                    if main_handles:
                        driver.switch_to.window(main_handles[0])
                        log_progress(f"  메인 페이지로 복귀 성공", "success")
                except:
                    pass
            
            processed_count += 1
            
        except TimeoutException as e:
            log_progress(f"  배정 실패: {e}", "error")
            # 팝업 닫기 및 메인 페이지로 복귀
            try:
                current_handles = driver.window_handles
                if len(current_handles) > 1:
                    driver.close()
                    driver.switch_to.window(current_handles[0])
                else:
                    # 메인 창으로 전환 시도
                    if current_handles:
                        driver.switch_to.window(current_handles[0])
            except Exception as window_error:
                log_progress(f"  창 전환 중 오류 (무시): {window_error}", "warning")
            failed_count += 1
            failed_list.append({
                "name": name,
                "phone": phone,
                "d_group": d_group,
                "leader_name": leader_name,
                "reason": f"타임아웃 오류: {str(e)}"
            })
            continue
        except Exception as e:
            log_progress(f"  배정 중 오류 발생: {e}", "error")
            # 팝업 닫기 및 메인 페이지로 복귀
            try:
                current_handles = driver.window_handles
                if len(current_handles) > 1:
                    driver.close()
                    driver.switch_to.window(current_handles[0])
                else:
                    # 메인 창으로 전환 시도
                    if current_handles:
                        driver.switch_to.window(current_handles[0])
            except Exception as window_error:
                log_progress(f"  창 전환 중 오류 (무시): {window_error}", "warning")
            failed_count += 1
            failed_list.append({
                "name": name,
                "phone": phone,
                "d_group": d_group,
                "leader_name": leader_name,
                "reason": f"배정 중 오류: {str(e)}"
            })
            continue
            
    except Exception as e:
        log_progress(f"  처리 중 오류 발생: {e}", "error")
        failed_count += 1
        failed_list.append({
            "name": name,
            "phone": phone,
            "d_group": d_group,
            "leader_name": leader_name,
            "reason": f"처리 중 예외 발생: {str(e)}"
        })
        # 메인 페이지로 복귀 시도
        try:
            current_handles = driver.window_handles
            if len(current_handles) > 1:
                driver.close()
                driver.switch_to.window(current_handles[0])
            else:
                if current_handles:
                    driver.switch_to.window(current_handles[0])
        except Exception as window_error:
            log_progress(f"  창 전환 중 오류 (무시): {window_error}", "warning")
        continue

log_progress(f"\n총 {processed_count}명 처리 완료, {failed_count}명 실패", "success")

# 실패한 인원 상세 정보 출력 및 저장
if failed_list:
    log_progress("\n" + "=" * 60, "info")
    log_progress("실패한 인원 목록", "warning")
    log_progress("=" * 60, "info")
    
    for failed_person in failed_list:
        log_progress(f"  - {failed_person['name']} ({failed_person['phone']})", "warning")
        log_progress(f"    다락방: {failed_person['d_group']}, 순장: {failed_person['leader_name']}", "info")
        log_progress(f"    실패 사유: {failed_person['reason']}", "error")
    
    # 실패한 인원을 CSV 파일로 저장
    failed_csv_filename = "failed_list.csv"
    try:
        with open(failed_csv_filename, "w", encoding="utf-8-sig", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=["이름", "연락처", "다락방", "순장", "실패사유"])
            writer.writeheader()
            for failed_person in failed_list:
                writer.writerow({
                    "이름": failed_person["name"],
                    "연락처": failed_person["phone"],
                    "다락방": failed_person["d_group"],
                    "순장": failed_person["leader_name"],
                    "실패사유": failed_person["reason"]
                })
        log_progress(f"\n실패한 인원 목록이 '{failed_csv_filename}' 파일로 저장되었습니다.", "info")
    except Exception as e:
        log_progress(f"실패 목록 저장 중 오류 발생: {e}", "error")
else:
    log_progress("실패한 인원이 없습니다.", "success")

log_progress("\n순배정 자동화 작업 완료", "success")
log_progress("브라우저는 유지됩니다. 수동으로 종료하거나 다음 작업을 진행하세요.", "info")
log_progress("=" * 60, "info")
input("브라우저 유지. 종료하려면 Enter...")
driver.quit()
