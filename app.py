import streamlit as st
import requests
from bs4 import BeautifulSoup
import time

# 網頁基本設定
st.set_page_config(page_title="Zuvio 自動點名助手", page_icon="🏫")

st.title("🏫 Zuvio 網頁點名 App")
st.info("輸入資訊後，點擊「開始監控」，網頁會自動幫你盯著點名系統。")

# 介面佈局
col1, col2 = st.columns(2)
with col1:
    user_email = st.text_input("帳號 (Email)", value="B1001228@gm.cnu.edu.tw")
    course_id = st.text_input("課程代號", value="1460562")
with col2:
    user_password = st.text_input("密碼", type="password")
    interval = st.slider("檢查頻率 (秒)", 5, 60, 10)

st.subheader("📍 GPS 座標設定")
lat = st.number_input("緯度", value=22.921056, format="%.6f")
lng = st.number_input("經度", value=120.228056, format="%.6f")

if st.button("開始監控點名", type="primary"):
    session = requests.Session()
    
    # 登入邏輯
    login_url = "https://irs.zuvio.com.tw/irs/submitLogin"
    login_data = {'email': user_email, 'password': user_password, 'current_role': 'student'}
    
    try:
        res = session.post(login_url, data=login_data)
        if "帳號或密碼錯誤" in res.text:
            st.error("❌ 登入失敗，請檢查帳號密碼。")
        else:
            st.success("✅ 登入成功！開始監控中...")
            
            status_box = st.empty() # 建立一個動態更新的區塊
            
            while True:
                # 檢查點名狀態
                rollcall_url = f"https://irs.zuvio.com.tw/student5/irs/rollcall/{course_id}"
                check_res = session.get(rollcall_url)
                soup = BeautifulSoup(check_res.text, "html.parser")
                text = soup.find("div", class_="irs-rollcall").text if soup.find("div", class_="irs-rollcall") else ""

                if "簽到開放中" in text:
                    # 發送簽到要求
                    submit_url = "https://irs.zuvio.com.tw/student5/irs/submitRollcall"
                    submit_data = {'course_id': course_id, 'lat': lat, 'lng': lng, 'accuracy': 100}
                    session.post(submit_url, data=submit_data)
                    st.balloons()
                    st.success(f"🎉 點名成功！時間：{time.strftime('%H:%M:%S')}")
                    break
                
                elif "準時" in text:
                    status_box.warning("⚠️ 已完成簽到（顯示為準時）。")
                    break
                
                else:
                    status_box.info(f"⏳ 尚未開放... 最後檢查：{time.strftime('%H:%M:%S')}")
                
                time.sleep(interval)
                
    except Exception as e:
        st.error(f"連線出錯：{e}")
