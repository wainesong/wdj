import streamlit as st
import requests
from bs4 import BeautifulSoup
import time
import random

# 網頁設定
st.set_page_config(page_title="Zuvio 終極簽到助手", page_icon="🎯")

st.title("🎯 Zuvio 簽到助手 (終極強化版)")
st.caption("針對『伺服器未確認成功』進行了封包優化")

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

def start_monitoring():
    session = requests.Session()
    # 模擬 iOS 設備的 Headers
    headers = {
        'User-Agent': 'Mozilla/5.0 (iPhone; CPU iPhone OS 16_6 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.6 Mobile/15E148 Safari/604.1',
        'X-Requested-With': 'XMLHttpRequest',
        'Accept': 'application/json, text/javascript, */*; q=0.01',
        'Referer': f'https://irs.zuvio.com.tw/student5/irs/rollcall/{course_id}',
        'Origin': 'https://irs.zuvio.com.tw'
    }
    
    # 1. 登入
    login_url = "https://irs.zuvio.com.tw/irs/submitLogin"
    login_data = {'email': user_email, 'password': user_password, 'current_role': 'student'}
    
    try:
        login_res = session.post(login_url, data=login_data, headers=headers)
        if "帳號或密碼錯誤" in login_res.text:
            st.error("❌ 登入失敗：請檢查帳密。")
            return

        st.success(f"✅ 登入成功！監控中...")
        status_info = st.empty()

        while True:
            rollcall_url = f"https://irs.zuvio.com.tw/student5/irs/rollcall/{course_id}"
            check_res = session.get(rollcall_url, headers=headers)
            soup = BeautifulSoup(check_res.text, "html.parser")
            
            rollcall_box = soup.find("div", class_="irs-rollcall")
            text_content = rollcall_box.text if rollcall_box else ""

            if "簽到開放中" in text_content:
                status_info.warning("🎯 偵測到簽到開放！準備發送強化封包...")
                
                # 2. 發送強化封包 (模擬真實 GPS 抖動與設備標籤)
                submit_url = "https://irs.zuvio.com.tw/student5/irs/submitRollcall"
                # 稍微抖動座標小數點後 6 位，讓它看起來更像真實手機訊號
                real_lat = lat + random.uniform(-0.00001, 0.00001)
                real_lng = lng + random.uniform(-0.00001, 0.00001)
                
                submit_data = {
                    'course_id': course_id,
                    'type': 'rollcall',
                    'lat': real_lat,
                    'lng': real_lng,
                    'accuracy': random.uniform(15.0, 30.0), # 真實手機的精確度通常在 15-30 之間
                    'device': 'ios'
                }
                
                response = session.post(submit_url, data=submit_data, headers=headers)
                
                # 3. 解析伺服器回傳的 JSON
                try:
                    res_json = response.json()
                    if res_json.get("status") == "yes":
                        st.balloons()
                        st.success(f"🎉 點名成功！(回傳：{res_json})")
                        break
                    else:
                        # 這是最關鍵的一行，會告訴你為什麼失敗
                        fail_msg = res_json.get('msg', '未知原因')
                        st.error(f"❌ 簽到失敗。原因：{fail_msg}")
                        st.info("💡 如果原因顯示『不在範圍內』，請嘗試重新設定更精確的教室座標。")
                        break
                except:
                    if "成功" in response.text:
                        st.success("🎉 點名成功 (HTML 解析)！")
                        break
                    else:
                        st.error("❌ 伺服器回傳異常。")
                        st.text(response.text[:200]) # 顯示前 200 字 debug
                        break
            
            elif "準時" in text_content:
                status_info.info("✅ 目前狀態：已完成簽到。")
                break
            else:
                status_info.write(f"⏳ 監控中... ({time.strftime('%H:%M:%S')})")
            
            time.sleep(interval)

    except Exception as e:
        st.error(f"⚠️ 發生錯誤：{e}")

if st.button("🚀 開始全自動監控", type="primary"):
    if not user_email or not user_password:
        st.warning("請填寫帳號密碼。")
    else:
        start_monitoring()
