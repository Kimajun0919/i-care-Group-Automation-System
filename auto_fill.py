import time
import pandas as pd
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager

# ==================================
# 1. 사이트 & 로그인 정보
# ==================================
LOGIN_URL = "https://example.com/admin/login"   # ✅ 실제 URL로 교체
ADMIN_ID = "관리자아이디"                        # ✅ 실제 아이디
ADMIN_PW = "관리자비번"                          # ✅ 실제 비번

SEARCH_URL = "https://example.com/admin/member/search"   # ✅ 이름 검색 페이지 주소

# ==================================
# 2. 데이터 파일(CSV)
# ==================================
# CSV 예: name,darak,sun
#       김하준,하늘다락,1순
data = pd.read_csv("data.csv")

# ==================================
# 3. 크롬 브라우저 실행
# ==================================
options = webdriver.ChromeOptions()
options.add_argument("--start-maximized")
driver = webdriver.Chrome(
    service=Service(ChromeDriverManager().install()),
    options=options
)
wait = WebDriverWait(driver, 10)

# ==================================
# 4. 로그인
# ==================================
driver.get(LOGIN_URL)

# ✅ 여기는 네가 복붙한 HTML에 맞춰 selector 수정
wait.until(EC.presence_of_element_located((By.NAME, "userid"))).send_keys(ADMIN_ID)
driver.find_element(By.NAME, "password").send_keys(ADMIN_PW)
driver.find_element(By.CSS_SELECTOR, "button[type='submit']").click()

print("✅ 로그인 완료")
time.sleep(1)

# ==================================
# 5. 반복 입력 시작
# ==================================
for _, row in data.iterrows():
    name = row["name"]
    darak = row["darak"]
    sun = row["sun"]

    print(f"▶ 처리 중: {name}")

    # ----------------------------------------------
    # 5-1. 이름 검색 페이지 이동
    # ----------------------------------------------
    driver.get(SEARCH_URL)

    # ✅ 검색창 선택자 (나중에 HTML 보고 수정)
    search_box = wait.until(
        EC.presence_of_element_located((By.NAME, "keyword"))
    )
    search_box.clear()
    search_box.send_keys(name)

    # ✅ 검색 버튼 선택자 (HTML 보고 수정)
    driver.find_element(By.CSS_SELECTOR, "button.btn-search").click()
    time.sleep(1)

    # ✅ 검색 결과에서 첫 번째 회원 클릭 (선택자 맞춰 수정)
    wait.until(
        EC.element_to_be_clickable((By.CSS_SELECTOR, "table tr td a"))
    ).click()
    time.sleep(1)

    # ----------------------------------------------
    # 5-2. 다락방 / 순 필드만 수정
    # ----------------------------------------------

    # ✅ 다락방 필드 선택자 — 복붙한 HTML 구조 기반으로 커스텀
    darak_field = wait.until(
        EC.presence_of_element_located((By.NAME, "darak"))  
        # 예: By.ID("darakField") 등으로 변경 가능
    )

    # ✅ 순 필드 선택자 — 복붙한 HTML 구조 기반으로 커스텀
    sun_field = driver.find_element(By.NAME, "sun")
    # 예: By.ID("sunOrder"), By.CSS_SELECTOR("[data-field='sun']") 등 가능

    # ✅ 기존값 비교 후 다를 때만 수정 → 다른 필드는 영향 없음
    if darak_field.get_attribute("value") != darak:
        darak_field.clear()
        darak_field.send_keys(darak)

    if sun_field.get_attribute("value") != sun:
        sun_field.clear()
        sun_field.send_keys(sun)

    # ✅ 저장 버튼 (나중에 너가 HTML 보고 selector만 고치면 됨)
    driver.find_element(By.CSS_SELECTOR, "button.btn-save").click()

    print(f"💾 완료: {name}")
    time.sleep(0.8)

# ==================================
# 6. 종료
# ==================================
driver.quit()
print("🎉 전체 처리 완료")
