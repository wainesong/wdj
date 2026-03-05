import streamlit as st
import requests
from bs4 import BeautifulSoup
import time
import random

st.set_page_config(page_title="Zuvio 雲端助手", page_icon="💊")
st.title("💊 Zuvio 智慧點名網頁版")

# 側邊欄：使用者設定
with st.sidebar:
    st.header("🔑 帳號設定")
    user_email = st.text_input("Email", value="B1001228@gm.cnu.edu.tw")
    user_password = st.text_input("密碼", type="password")
    
    st.header("📍 課程與定位")
    course_id = st.text_input("課程 ID (數字)", value="1460562")
    lat = st.number_input("緯度", value=22.921056, format="%.6f")
    lng = st.number_input("經度", value=120.228056, format="%.6f")
    
    interval = st.slider("檢查頻率 (秒)", 5, 30, 10)

def start_checkin():
    session = requests.Session()
    # 模擬 iPhone 瀏覽器
    headers = {
        'User-Agent': 'Mozilla/5.0 (iPhone; CPU iPhone OS 16_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.0 Mobile/15E148 Safari/04.1',
        'Referer': 'https://irs.zuvio.com.tw/'
    }

    try:
        # 1. 登入
        login_res = session.post("https://irs.zuvio.com.tw/irs/submitLogin", 
                                 data={'email': user_email, 'password': user_password, 'current_role': 'student'})
        
        if "帳號或密碼錯誤" in login_res.text:
            st.error("❌ 登入失敗：請檢查帳號密碼。")
            return
        
        st.success("✅ 登入成功！")
        
        # 2. 解決 404 問題：自動判斷網址版本
        urls = [
            f"https://irs.zuvio.com.tw/student5/irs/rollcall/{course_id}",
            f"https://irs.zuvio.com.tw/student/irs/rollcall/{course_id}"
        ]
        
        active_url = ""
        for u in urls:
            r = session.get(u, headers=headers)
            if r.status_code == 200 and "404" not in r.text:
                active_url = u
                break
        
        if not active_url:
            st.error(f"❌ 找不到課程代號 {course_id}，請確認數字是否填錯。")
            return

        status_display = st.empty()
        
        # 3. 監控循環
        while True:
            res = session.get(active_url, headers=headers)
            soup = BeautifulSoup(res.text, "html.parser")
            page_text = soup.text

            if "簽到開放中" in page_text:
                # 偵測是否為 GPS 點名
                is_gps = any(word in page_text for word in ["GPS", "定位", "距離"])
                status_display.warning(f"🎯 偵測到點名開放！模式：{'GPS' if is_gps else '一般'}")
                
                # 發送簽到要求
                submit_url = "https://irs.zuvio.com.tw/student5/irs/submitRollcall"
                payload = {
                    'course_id': course_id,
                    'type': 'rollcall',
                    'device': 'ios'
                }
                
                if is_gps:
                    payload.update({
                        'lat': lat + random.uniform(-0.00002, 0.00002),
                        'lng': lng + random.uniform(-0.00002, 0.00002),
                        'accuracy': random.uniform(20, 40)
                    })

                submit_res = session.post(submit_url, data=payload, headers=headers)
                
                if "成功" in submit_res.text or "yes" in submit_res.text:
                    st.balloons()
                    st.success("🎉 點名成功！")
                    break
                else:
                    st.error("❌ 簽到失敗，伺服器拒絕請求。")
                    break
            
            elif "準時" in page_text:
                status_display.info("✅ 目前顯示已簽到。")
                break
            else:
                status_display.write(f"⏳ 監控中... ({time.strftime('%H:%M:%S')})")
            
            time.sleep(interval)

    except Exception as e:
        st.error(f"發生程式錯誤：{e}")

if st.button("🚀 開始點名監控", type="primary"):
    start_checkin()
