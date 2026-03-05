import streamlit as st
import requests
from bs4 import BeautifulSoup
import time
import random

st.set_page_config(page_title="Zuvio 終極強化版", page_icon="🎯")
st.title("🎯 Zuvio 智慧點名 (穩定強化版)")

with st.sidebar:
    user_email = st.text_input("帳號", value="B1001228@gm.cnu.edu.tw")
    user_password = st.text_input("密碼", type="password")
    course_id = st.text_input("課程 ID", value="1460562")
    lat = st.number_input("緯度", value=22.921056, format="%.6f")
    lng = st.number_input("經度", value=120.228056, format="%.6f")

def run_checkin():
    session = requests.Session()
    # 模擬更完整的 iPhone 標頭
    headers = {
        'User-Agent': 'Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Mobile/15E148 Safari/604.1',
        'X-Requested-With': 'XMLHttpRequest',
        'Accept': 'application/json, text/javascript, */*; q=0.01',
        'Referer': f'https://irs.zuvio.com.tw/student5/irs/rollcall/{course_id}'
    }

    try:
        # 1. 登入
        session.post("https://irs.zuvio.com.tw/irs/submitLogin", 
                     data={'email': user_email, 'password': user_password, 'current_role': 'student'})
        
        # 2. 探測正確網址
        base_url = f"https://irs.zuvio.com.tw/student5/irs/rollcall/{course_id}"
        if session.get(base_url).status_code != 200:
            base_url = f"https://irs.zuvio.com.tw/student/irs/rollcall/{course_id}"

        st.success("✅ 監控啟動中...")
        msg_slot = st.empty()

        while True:
            res = session.get(base_url, headers=headers)
            soup = BeautifulSoup(res.text, "html.parser")
            
            if "簽到開放中" in soup.text:
                msg_slot.warning("🎯 偵測到點名開放！發送強化封包...")
                
                # 3. 強化封包參數
                submit_url = base_url.replace("rollcall", "submitRollcall")
                payload = {
                    'course_id': course_id,
                    'type': 'rollcall',
                    'lat': lat + random.uniform(-0.00002, 0.00002), # 座標微抖動
                    'lng': lng + random.uniform(-0.00002, 0.00002),
                    'accuracy': random.uniform(15.0, 25.0),        # 模擬真實精確度
                    'device': 'ios'
                }
                
                response = session.post(submit_url, data=payload, headers=headers)
                
                # 4. 解析結果
                try:
                    res_json = response.json()
                    if res_json.get("status") == "yes":
                        st.balloons()
                        st.success("🎉 簽到成功！")
                        break
                    else:
                        # 顯示伺服器給的具體失敗原因
                        error_msg = res_json.get('msg', '未知錯誤')
                        st.error(f"❌ 簽到被拒絕。原因：{error_msg}")
                        break
                except:
                    if "成功" in response.text:
                        st.success("🎉 簽到成功 (文本驗證)！")
                        break
                    else:
                        st.error("❌ 伺服器回傳內容異常")
                        with st.expander("查看原始錯誤訊息"):
                            st.write(response.text)
                        break
            
            elif "準時" in soup.text:
                msg_slot.info("✅ 已完成簽到。")
                break
            else:
                msg_slot.write(f"⏳ 監控中... ({time.strftime('%H:%M:%S')})")
            
            time.sleep(10)

    except Exception as e:
        st.error(f"錯誤：{e}")

if st.button("🚀 開始全自動監控"):
    run_checkin()
