import streamlit as st
import requests
from bs4 import BeautifulSoup
import time
import random

st.set_page_config(page_title="Zuvio 智慧點名器", page_icon="💊")
st.title("💊 Zuvio 智慧點名 (API 穩定版)")

with st.sidebar:
    st.header("🔑 登入資訊")
    user_email = st.text_input("帳號", value="B1001228@gm.cnu.edu.tw")
    user_password = st.text_input("密碼", type="password")
    course_id = st.text_input("課程代號", value="1460562")
    st.markdown("---")
    lat = st.number_input("緯度", value=22.921056, format="%.6f")
    lng = st.number_input("經度", value=120.228056, format="%.6f")

def run_app():
    session = requests.Session()
    headers = {
        'User-Agent': 'Mozilla/5.0 (iPhone; CPU iPhone OS 16_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.0 Mobile/15E148 Safari/04.1',
    }

    try:
        # 1. 登入
        login_res = session.post("https://irs.zuvio.com.tw/irs/submitLogin", 
                                 data={'email': user_email, 'password': user_password, 'current_role': 'student'})
        
        if "帳號或密碼錯誤" in login_res.text:
            st.error("❌ 登入失敗：請檢查帳號密碼。")
            return
        
        st.success("✅ 登入成功！")

        # 2. 智慧尋找正確的點名網址 (解決 404)
        urls = [
            f"https://irs.zuvio.com.tw/student5/irs/rollcall/{course_id}",
            f"https://irs.zuvio.com.tw/student/irs/rollcall/{course_id}",
            f"https://irs.zuvio.com.tw/student/irs/index/{course_id}"
        ]
        
        active_url = ""
        for u in urls:
            r = session.get(u, headers=headers)
            if r.status_code == 200 and "404" not in r.text:
                active_url = u
                break
        
        if not active_url:
            st.error(f"❌ 找不到課程 {course_id}。請檢查號碼是否填錯。")
            return

        status_box = st.empty()
        while True:
            res = session.get(active_url, headers=headers)
            soup = BeautifulSoup(res.text, "html.parser")
            
            # 偵測簽到狀態
            page_text = soup.text
            if "簽到開放中" in page_text:
                status_box.warning("🎯 偵測到點名開放！")
                
                # 發送簽到
                submit_url = "https://irs.zuvio.com.tw/student5/irs/submitRollcall"
                # 判斷是否需要 GPS (只要頁面有提到 GPS 就送座標)
                is_gps = "GPS" in page_text or "定位" in page_text
                
                payload = {'course_id': course_id, 'type': 'rollcall', 'device': 'ios'}
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
                    st.error("❌ 簽到失敗，請檢查座標或手動簽到。")
                    break
            
            elif "準時" in page_text or "已完成" in page_text:
                status_box.info("✅ 目前已在簽到狀態。")
                break
            else:
                status_box.write(f"⏳ 監控中... ({time.strftime('%H:%M:%S')})")
            
            time.sleep(10)

    except Exception as e:
        st.error(f"發生錯誤：{e}")

if st.button("🚀 開始全自動監控"):
    run_app()
