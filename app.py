import streamlit as st
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.by import By
from bs4 import BeautifulSoup
import time
import random

st.title("🛡️ Zuvio 終極穩定版 (Selenium)")

# 側邊欄設定
with st.sidebar:
    st.header("🔑 帳號設定")
    user_id = st.text_input("帳號", value="B1001228@gm.cnu.edu.tw")
    user_pw = st.text_input("密碼", type="password")
    
    st.header("📍 課程與定位")
    course_id = st.text_input("課程代號", value="1460562")
    lat = st.number_input("緯度", value=22.921056, format="%.6f")
    lng = st.number_input("經度", value=120.228056, format="%.6f")

if st.button("開始模擬點名"):
    options = Options()
    options.add_argument("--headless")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_experimental_option("prefs", {"profile.default_content_setting_values.geolocation": 1})

    try:
        with st.status("啟動模擬瀏覽器...", expanded=True) as status:
            driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
            
            # 1. 模擬 GPS (加入微小抖動防止被抓)
            driver.execute_cdp_cmd("Emulation.setGeolocationOverride", {
                "latitude": lat + random.uniform(-0.00001, 0.00001),
                "longitude": lng + random.uniform(-0.00001, 0.00001),
                "accuracy": 100
            })

            # 2. 登入
            driver.get("https://irs.zuvio.com.tw/")
            time.sleep(2)
            driver.find_element(By.ID, "email").send_keys(user_id)
            driver.find_element(By.ID, "password").send_keys(user_pw)
            driver.find_element(By.CLASS_NAME, "submit-button").click()
            time.sleep(3)

            # 3. 嘗試多個網址 (解決 404)
            urls_to_try = [
                f"https://irs.zuvio.com.tw/student5/irs/rollcall/{course_id}",
                f"https://irs.zuvio.com.tw/student/irs/rollcall/{course_id}"
            ]
            
            worked_url = ""
            for test_url in urls_to_try:
                driver.get(test_url)
                time.sleep(2)
                if "Zuvio 404" not in driver.title:
                    worked_url = test_url
                    break
            
            if not worked_url:
                st.error(f"❌ 課程代號 {course_id} 確定是錯的！請在 Zuvio 網頁點進課程，看網址最後的數字。")
                driver.quit()
                st.stop()

            st.success(f"✅ 連線成功！正在監控：{course_id}")
            
            # 4. 監控循環
            while True:
                soup = BeautifulSoup(driver.page_source, "html.parser")
                text = soup.text
                
                if "簽到開放中" in text:
                    # 判斷是否需要點擊
                    btn = driver.find_elements(By.ID, "submit-make-rollcall")
                    if btn:
                        driver.execute_script("arguments[0].click();", btn[0])
                        st.balloons()
                        st.success("🎉 點名成功！")
                        break
                
                elif "準時" in text or "已簽到" in text:
                    st.info("✅ 偵測到已完成簽到。")
                    break
                
                status.update(label=f"⏳ 監控中...最後更新：{time.strftime('%H:%M:%S')}")
                time.sleep(15)
                driver.refresh()
                
            driver.quit()
    except Exception as e:
        st.error(f"發生錯誤：{e}")
