import streamlit as st
import requests
from bs4 import BeautifulSoup
import time
import json

# 網頁設定
st.set_page_config(page_title="Zuvio 點名助手專業版", page_icon="🚀")

st.title("🚀 Zuvio 網頁點名助手 (API 強力版)")
st.markdown("---")

# 介面設定
with st.sidebar:
    st.header("🔑 帳戶設定")
    user_email = st.text_input("帳號 (Email)", value="B1001228@gm.cnu.edu.tw")
    user_password = st.text_input("密碼", type="password")
    
    st.header("📍 課程與定位")
    course_id = st.text_input("課程代號 (數字)", value="1460562")
    lat = st.number_input("緯度 (Latitude)", value=22.921056, format="%.6f")
    lng = st.number_input("經度 (Longitude)", value=120.228056, format="%.6f")
    
    interval = st.slider("檢查頻率 (秒)", 5, 30, 10)

# 核心點名功能
def start_monitoring():
    session = requests.Session()
    # 偽裝成 iPhone Safari 瀏覽器
    headers = {
        'User-Agent': 'Mozilla/5.0 (iPhone; CPU iPhone OS 16_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.0 Mobile/15E148 Safari/04.1',
        'Referer': 'https://irs.zuvio.com.tw/',
        'Origin': 'https://irs.zuvio.com.tw'
    }
    
    # 1. 登入
    login_url = "https://irs.zuvio.com.tw/irs/submitLogin"
    login_data = {
        'email': user_email,
        'password': user_password,
        'current_role': 'student'
    }
    
    try:
        login_res = session.post(login_url, data=login_data, headers=headers)
        if "帳號或密碼錯誤" in login_res.text:
            st.error("❌ 登入失敗：帳號或密碼錯誤，請重新確認。")
            return

        st.success(f"✅ 登入成功！正在監控課程：{course_id}")
        
        status_info = st.empty()
        log_area = st.expander("詳細日誌 (Debug Log)")

        while True:
            rollcall_url = f"https://irs.zuvio.com.tw/student5/irs/rollcall/{course_id}"
            check_res = session.get(rollcall_url, headers=headers)
            soup = BeautifulSoup(check_res.text, "html.parser")
            
            # 判斷目前頁面狀態
            rollcall_box = soup.find("div", class_="irs-rollcall")
            text_content = rollcall_box.text if rollcall_box else ""

            if "簽到開放中" in text_content:
                status_info.warning("🎯 偵測到簽到開放！準備發送封包...")
                
                # 2. 發送簽到封包
                submit_url = "https://irs.zuvio.com.tw/student5/irs/submitRollcall"
                submit_data = {
                    'course_id': course_id,
                    'type': 'rollcall',
                    'lat': lat,
                    'lng': lng,
                    'accuracy': 100
                }
                
                response = session.post(submit_url, data=submit_data, headers=headers)
                
                # 3. 嚴謹解析結果
                try:
                    result_json = response.json()
                    # Zuvio 通常回傳 {"status": "yes"} 或包含 "成功" 文字
                    if result_json.get("status") == "yes" or result_json.get("msg") == "success":
                        st.balloons()
                        st.success(f"🎉 點名成功！(伺服器回傳：{result_json})")
                        break
                    else:
                        st.error(f"❌ 簽到失敗。伺服器回傳：{result_json}")
                        break
                except:
                    # 如果不是回傳 JSON，檢查 HTML
                    if "成功" in response.text:
                        st.balloons()
                        st.success(f"🎉 點名成功！(HTML 驗證成功)")
                        break
                    else:
                        st.error(f"❌ 雖然送出了，但伺服器未確認成功。請檢查座標。")
                        log_area.code(response.text[:500])
                        break
            
            elif "準時" in text_content:
                status_info.info("✅ 目前狀態：已完成簽到（準時簽到）。")
                break
            
            else:
                status_info.write(f"⏳ 監控中... (最後檢查：{time.strftime('%H:%M:%S')})")
            
            time.sleep(interval)

    except Exception as e:
        st.error(f"⚠️ 發生錯誤：{e}")

# 按鈕啟動
if st.button("開始自動點名", type="primary"):
    if not user_email or not user_password:
        st.warning("請先填寫帳號密碼。")
    else:
        start_monitoring()
