import streamlit as st
import requests
from bs4 import BeautifulSoup
import time
import random

st.set_page_config(page_title="Zuvio 終極修正版", page_icon="🛡️")
st.title("🛡️ Zuvio 簽到助手 (防禦性更新版)")

with st.sidebar:
    st.header("🔑 帳戶設定")
    user_email = st.text_input("帳號", value="B1001228@gm.cnu.edu.tw")
    user_password = st.text_input("密碼", type="password")
    course_id = st.text_input("課程代號", value="1460562")
    lat = st.number_input("緯度", value=22.921056, format="%.6f")
    lng = st.number_input("經度", value=120.228056, format="%.6f")
    interval = st.slider("檢查頻率 (秒)", 5, 30, 10)

def start_monitoring():
    session = requests.Session()
    headers = {
        'User-Agent': 'Mozilla/5.0 (iPhone; CPU iPhone OS 16_6 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.6 Mobile/15E148 Safari/604.1',
        'X-Requested-With': 'XMLHttpRequest'
    }

    try:
        # 1. 登入
        login_res = session.post("https://irs.zuvio.com.tw/irs/submitLogin", 
                                 data={'email': user_email, 'password': user_password, 'current_role': 'student'})
        
        if "帳號或密碼錯誤" in login_res.text:
            st.error("❌ 登入失敗：請檢查帳號密碼。")
            return
        
        st.success("✅ 登入成功！")
        status_info = st.empty()

        # 2. 自動尋找正確網址
        urls_to_try = [
            f"https://irs.zuvio.com.tw/student5/irs/rollcall/{course_id}",
            f"https://irs.zuvio.com.tw/student/irs/rollcall/{course_id}"
        ]
        
        final_url = ""
        for u in urls_to_try:
            if session.get(u).status_code == 200:
                final_url = u
                break
        
        if not final_url:
            st.error("❌ 找不到點名頁面，請確認課程代號是否正確。")
            return

        while True:
            res = session.get(final_url, headers=headers)
            soup = BeautifulSoup(res.text, "html.parser")
            rollcall_box = soup.find("div", class_="irs-rollcall")
            text_content = rollcall_box.text if rollcall_box else ""

            if "簽到開放中" in text_content:
                # 判斷是否需要 GPS
                is_gps = any(k in text_content for k in ["GPS", "定位", "距離"])
                status_info.warning(f"🎯 偵測到{'GPS' if is_gps else '一般'}簽到開放！")
                
                submit_url = final_url.replace("rollcall", "submitRollcall")
                submit_data = {'course_id': course_id, 'type': 'rollcall', 'device': 'ios'}
                
                if is_gps:
                    submit_data.update({
                        'lat': lat + random.uniform(-0.00001, 0.00001),
                        'lng': lng + random.uniform(-0.00001, 0.00001),
                        'accuracy': random.uniform(15, 25)
                    })

                # 執行簽到
                response = session.post(submit_url, data=submit_data, headers=headers)
                
                # --- 強化判斷邏輯 ---
                # 優先檢查 JSON
                try:
                    res_json = response.json()
                    if res_json.get("status") == "yes":
                        st.balloons(); st.success("🎉 簽到成功！")
                        break
                except:
                    pass # 非 JSON 格式則往下檢查文本
                
                # 檢查 HTML 文本關鍵字
                if any(word in response.text for word in ["成功", "已經簽到", "ok", "yes"]):
                    st.balloons(); st.success("🎉 簽到成功 (透過文本驗證)！")
                    break
                else:
                    st.error("❌ 簽到可能失敗，請展開下方日誌檢查內容。")
                    with st.expander("查看伺服器回傳內容 (Debug)"):
                        st.code(response.text)
                    break
            
            elif any(word in text_content for word in ["準時", "已簽到"]):
                status_info.info("✅ 偵測到已完成簽到。")
                break
            else:
                status_info.write(f"⏳ 監控中... ({time.strftime('%H:%M:%S')})")
            
            time.sleep(interval)

    except Exception as e:
        st.error(f"發生錯誤：{e}")

if st.button("🚀 開始全自動監控"):
    start_monitoring()
