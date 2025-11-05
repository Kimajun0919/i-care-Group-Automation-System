# ==========================================
# 아이케어(iOnnuri) 순배정 자동화 샘플 코드
# ==========================================

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
from webdriver_manager.chrome import ChromeDriverManager
import time, json, os

# ------------------------------------------
# 0. 설정
# ------------------------------------------
LOGIN_URL = "https://icare.ionnuri.org"  # 로그인 페이지
COMMUNITY_URL = "https://icare.ionnuri.org/admin/community/assign"  # 순배정 페이지 URL (실제 맞게 수정)

ADMIN_ID = "YOUR_ID_HERE"
ADMIN_PW = "YOUR_PASSWORD_HERE"

TARGET_NAME = "김하준"
TARGET_PHONE = "01012345678"
D_GROUP = "하늘다락"  # 다락방 이름
LEADER_NAME = "박명아"  # 순장 이름

# ------------------------------------------
# 1. 드라이버 초기화
# ------------------------------------------
print("🚀 드라이버 초기화 중...")
options = webdriver.ChromeOptions()
options.add_argument("--start-maximized")
driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
wait = WebDriverWait(driver, 10)
print("✅ 크롬 실행 완료")

# ------------------------------------------
# 2. 로그인 (쿠키 자동 사용)
# ------------------------------------------
if os.path.exists("cookies.json"):
    print("🍪 쿠키 로그인 시도 중...")
    driver.get(LOGIN_URL)
    with open("cookies.json", "r", encoding="utf-8") as f:
        cookies = json.load(f)
    for cookie in cookies:
        if "sameSite" in cookie:
            cookie.pop("sameSite")
        driver.add_cookie(cookie)
    driver.refresh()
    print("✅ 자동 로그인 완료")
else:
    print("🔐 수동 로그인 중...")
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
    print("💾 로그인 쿠키 저장 완료")

# ------------------------------------------
# 3. 공동체 → 순배정 메뉴 이동
# ------------------------------------------
print("📂 공동체 → 순배정 이동 중...")
try:
    driver.get(COMMUNITY_URL)
    wait.until(EC.presence_of_element_located((By.TAG_NAME, "body")))
    print("✅ 순배정 페이지 로드 완료")
except TimeoutException:
    print("❌ 순배정 페이지 로딩 실패")
    driver.quit()
    exit()

# ------------------------------------------
# 4. 이름 검색
# ------------------------------------------
try:
    print(f"🔍 이름 검색: {TARGET_NAME}")
    search_input = wait.until(EC.presence_of_element_located((By.NAME, "keyword")))
    search_input.clear()
    search_input.send_keys(TARGET_NAME)
    driver.find_element(By.CSS_SELECTOR, ".btn-search").click()
    time.sleep(1)
except Exception:
    print("❌ 검색 과정 오류 발생")
    driver.quit()
    exit()

# ------------------------------------------
# 5. 검색 결과 선택 및 검증
# ------------------------------------------
try:
    print("🧾 검색 결과 선택 중...")
    first_result = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "table tr")))
    name_cell = first_result.find_element(By.CSS_SELECTOR, "td.name")
    phone_cell = first_result.find_element(By.CSS_SELECTOR, "td.phone")

    name_text = name_cell.text.strip()
    phone_text = phone_cell.text.replace("-", "").strip()

    if name_text == TARGET_NAME and phone_text == TARGET_PHONE:
        print(f"✅ 검증 완료: {name_text} / {phone_text}")
        name_cell.click()
    else:
        print(f"⚠️ 정보 불일치: {name_text}, {phone_text}")
        driver.quit()
        exit()
except TimeoutException:
    print("❌ 검색 결과를 찾을 수 없습니다.")
    driver.quit()
    exit()

# ------------------------------------------
# 6. 배정하기 버튼 클릭
# ------------------------------------------
try:
    print("➡️ 배정하기 버튼 클릭 중...")
    wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, ".btn-assign"))).click()
    print("✅ 배정창 열림")
except TimeoutException:
    print("❌ 배정하기 버튼을 찾지 못했습니다.")
    driver.quit()
    exit()

# ------------------------------------------
# 7. 다락방 선택
# ------------------------------------------
try:
    print(f"🏠 다락방 선택: {D_GROUP}")
    group_cell = wait.until(
        EC.presence_of_element_located((By.XPATH, f"//td[contains(text(), '{D_GROUP}')]"))
    )
    group_cell.click()
    print("✅ 다락방 선택 완료")
except TimeoutException:
    print("❌ 다락방 이름을 찾을 수 없습니다.")
    driver.quit()
    exit()

# ------------------------------------------
# 8. 순장 선택
# ------------------------------------------
try:
    print(f"👤 순장 선택: {LEADER_NAME}")
    leader_cell = wait.until(
        EC.presence_of_element_located((By.XPATH, f"//td[contains(text(), '{LEADER_NAME}')]"))
    )
    leader_cell.click()
    print("✅ 순장 선택 완료")
except TimeoutException:
    print("❌ 순장을 찾을 수 없습니다.")
    driver.quit()
    exit()

# ------------------------------------------
# 9. 저장 버튼 클릭
# ------------------------------------------
try:
    print("💾 저장 버튼 클릭 중...")
    save_btn = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, ".btn-save")))
    save_btn.click()

    # 저장 완료 문구 대기
    wait.until(EC.text_to_be_present_in_element((By.TAG_NAME, "body"), "저장되었습니다"))
    print("✅ 저장 완료!")
except TimeoutException:
    print("⚠️ 저장 완료 문구를 찾을 수 없습니다. (AJAX 구조일 수도 있음)")
finally:
    print("\n🎉 순배정 자동화 완료")
    input("Enter 키를 누르면 브라우저를 닫습니다...")
    driver.quit()
