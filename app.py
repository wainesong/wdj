import streamlit as st
import requests
from bs4 import BeautifulSoup
import time
import random

# 網頁設定
st.set_page_config(page_title="Zuvio 終極簽到助手", page_icon="🎯")

st.title("🎯 Zuvio 簽到助手 (智慧判體版)")
st.caption("自動識別『一般簽到』或『GPS 簽到』模式")

# 介面設定
with st.sidebar:
    st.header("🔑 帳戶設定")
    user_email = st.text_input("帳號 (Email)", value="B1001228@gm.cnu.edu.tw")
    user_password = st.text_input("密碼", type="password")
    
    st.header("📍 課程與定位")
    course_id = st.text_input("課程代號 (數字)", value="1460562")
    
    st.markdown("---")
    st.subheader("GPS 簽到參數")
    st.info("若為一般簽到，以下座標將自動忽略")
    lat = st.number_input("緯度 (Latitude)", value=22.921056, format="%.6f")
    lng = st.number_input("經度 (Longitude)", value=120.228056, format="%.6f")
    
    interval = st.slider("檢查頻率 (秒)", 5, 30, 10)

def start_monitoring():
    session = requests.Session()
    headers = {
        'User-Agent': 'Mozilla/5.0 (iPhone; CPU iPhone OS 16_6 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.6 Mobile/15E148 Safari/604.1',
        'X-Requested-With': 'XMLHttpRequest',
        'Accept': 'application/json, text/javascript, */*; q=0.01',
        'Origin': 'https://irs.zuvio.com.tw'
    }
    
    # 1. 登入
    login_url = "https://irs.zuvio.com.tw/irs/submitLogin"
    login_data = {'email': user_email, 'password': user_password, 'current_role': 'student'}
    
    try:
        login_res = session.post(login_url, data=login_data, headers=headers)
        if "帳號或密碼錯誤" in login_res.text:
            st.error("❌ 登入失敗：請檢查帳號密碼。")
            return

        st.success("✅ 登入成功！自動監控啟動...")
        status_info = st.empty()

        # 自動偵測網址 (解決 404 問題)
        possible_urls = [
            f"https://irs.zuvio.com.tw/student5/irs/rollcall/{course_id}",
            f"https://irs.zuvio.com.tw/student/irs/rollcall/{course_id}"
        ]
        
        final_url = ""
        for url in possible_urls:
            check_url_res = session.get(url, headers=headers)
            if check_url_res.status_code == 200:
                final_url = url
                break
        
        if not final_url:
            st.error("❌ 找不到點名頁面 (404)。請確認課程代號是否正確。")
            return

        headers['Referer'] = final_url

        while True:
            res = session.get(final_url, headers=headers)
            soup = BeautifulSoup(res.text, "html.parser")
            rollcall_box = soup.find("div", class_="irs-rollcall")
            text_content = rollcall_box.text if rollcall_box else ""

            if "簽到開放中" in text_content:
                # --- 核心判斷邏輯 ---
                is_gps = "GPS" in text_content or "定位" in text_content
                mode_text = "GPS 簽到" if is_gps else "一般簽到"
                status_info.warning(f"🎯 偵測到【{mode_text}】開放中！發送封包...")
                
                submit_url = final_url.replace("rollcall", "submitRollcall")
                
                # 基本封包
                submit_data = {
                    'course_id': course_id,
                    'type': 'rollcall',
                    'device': 'ios'
                }
                
                # 如果是 GPS 模式才加入座標
                if is_gps:
                    submit_data.update({
                        'lat': lat + random.uniform(-0.00001, 0.00001),
                        'lng': lng + random.uniform(-0.00001, 0.00001),
                        'accuracy': random.uniform(15.0, 30.0)
                    })
                
                response = session.post(submit_url, data=submit_data, headers=headers)
                
                try:
                    res_json = response.json()
                    if res_json.get("status") == "yes":
                        st.balloons()
                        st.success(f"🎉 {mode_text}成功！")
                        break
                    else:
                        st.error(f"❌ 簽到失敗。原因：{res_json.get('msg', '未知')}")
                        break
                except:
                    if "成功" in response.text:
                        st.success(f"🎉 {mode_text}成功 (HTML 解析)！")
                        break
                    else:
                        st.error("❌ 伺服器回傳格式異常，請檢查是否已簽到過。")
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
