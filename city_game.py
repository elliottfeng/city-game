import streamlit as st
from datetime import datetime, timedelta
import json
import os
import hashlib
import pytz
import requests

st.set_page_config(page_title="城池占领游戏", layout="wide")


# ========== 从 Streamlit Secrets 读取配置 ==========
def get_gist_config():
    try:
        gist_id = st.secrets["gist"]["id"]
        github_token = st.secrets["gist"]["token"]
        return gist_id, github_token
    except:
        gist_id = os.environ.get("GIST_ID", "")
        github_token = os.environ.get("GITHUB_TOKEN", "")
        return gist_id, github_token


GIST_ID, GITHUB_TOKEN = get_gist_config()


# ========== 数据持久化函数 ==========
def load_data_from_gist():
    try:
        url = f"https://api.github.com/gists/{GIST_ID}"
        headers = {"Authorization": f"token {GITHUB_TOKEN}"}
        response = requests.get(url, headers=headers, timeout=10)
        if response.status_code == 200:
            gist_data = response.json()
            files = gist_data.get('files', {})
            if 'city_data.json' in files:
                content = files['city_data.json'].get('content', '{}')
                data = json.loads(content) if content else {}
                if data:
                    return data
    except:
        pass
    return load_data_from_local()


def save_data_to_gist(data):
    try:
        url = f"https://api.github.com/gists/{GIST_ID}"
        headers = {"Authorization": f"token {GITHUB_TOKEN}"}
        payload = {
            "files": {
                "city_data.json": {
                    "content": json.dumps(data, ensure_ascii=False, indent=2)
                }
            }
        }
        response = requests.patch(url, headers=headers, json=payload, timeout=10)
        if response.status_code in [200, 201]:
            return True
    except:
        pass
    return save_data_to_local(data)


def load_data_from_local():
    try:
        if os.path.exists("city_data.json"):
            with open("city_data.json", 'r', encoding='utf-8') as f:
                return json.load(f)
    except:
        pass
    return {}


def save_data_to_local(data):
    try:
        with open("city_data.json", 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        return True
    except:
        return False


if GIST_ID and GITHUB_TOKEN:
    def load_data():
        return load_data_from_gist()


    def save_data(data):
        return save_data_to_gist(data)


    storage_mode = "☁️ 云存储"
else:
    def load_data():
        return load_data_from_local()


    def save_data(data):
        return save_data_to_local(data)


    storage_mode = "💾 本地存储"

# ========== 时区设置 ==========
BEIJING_TZ = pytz.timezone('Asia/Shanghai')


def beijing_now():
    return datetime.now(BEIJING_TZ).replace(tzinfo=None)


# ========== 密码配置 ==========
ADMIN_PASSWORD_HASH = hashlib.md5("admin123".encode()).hexdigest()


def check_password(password):
    return hashlib.md5(password.encode()).hexdigest() == ADMIN_PASSWORD_HASH


# 初始化状态
if 'authenticated' not in st.session_state:
    st.session_state.authenticated = False
if 'select_mode' not in st.session_state:
    st.session_state.select_mode = False
if 'single_mode' not in st.session_state:
    st.session_state.single_mode = False
if 'selected' not in st.session_state:
    st.session_state.selected = set()
if 'single_selected_cell' not in st.session_state:
    st.session_state.single_selected_cell = None
if 'data_loaded' not in st.session_state:
    st.session_state.data_loaded = False

# 11x11 城池数据
CITIES = [
    ["1级资源北1区", "3级资源北2区", "1级资源北3区", "2级资源北4区", "安边镇", "3级资源北6区", "定羌寨", "2级资源北8区",
     "2级资源东1区", "1级资源东2区", "1级资源东3区"],
    ["1级资源北9区", "得胜寨", "4级资源北11区", "雄武镇", "4级资源北13区", "1级资源北14区", "4级资源北15区",
     "1级资源北16区", "锁云关", "靖海镇", "3级资源东6区"],
    ["2级资源北17区", "镇龙关", "3级资源北19区", "1级资源北20区", "5级资源北21区", "御龙北城", "2级资源北23区",
     "3级资源北24区", "3级资源东7区", "4级资源东8区", "1级资源东9区"],
    ["2级资源西1区", "1级资源西2区", "3及资源西3区", "7级资源外城1区", "6级资源外城2区", "5级资源外城3区",
     "6级资源外城4区", "7级资源外城5区", "1级资源东10区", "澄海寨", "2级资源东12区"],
    ["镇戎镇", "4级资源西5区", "2级资源西6区", "6级资源外城6区", "10级资源内城1区", "8级资源内城2区", "9级资源内城3区",
     "6级资源外城7区", "5级资源东13区", "4级资源东14区", "横江镇"],
    ["3级资源西7区", "1级资源西8区", "御龙西城", "5级资源外城8区", "8级资源内城4区", "天龙龙城", "8级资源内城5区",
     "5级资源外城9区", "御龙东城", "1级资源东17区", "3级资源东18区"],
    ["清平寨", "4级资源西11区", "5级资源西12区", "6级资源外城10区", "9级资源内城6区", "8级资源内城7区",
     "10级资源内城8区", "6级资源外城11区", "2级资源东19区", "4级资源东20区", "平蛮寨"],
    ["2级资源西13区", "怀远镇", "1级资源西15区", "7级资源外城12区", "6级资源外城13区", "5级资源外城14区",
     "6级资源外城15区", "7级资源外城16区", "3级资源东22区", "1级资源东23区", "2级资源东24区"],
    ["1级资源西16区", "4级资源西17区", "3级资源西18区", "2级资源南1区", "2级资源南2区", "御龙南镇", "5级资源南4区",
     "1级资源南5区", "3级资源南6区", "断岳关", "2级资源南8区"],
    ["3级资源西19区", "广信寨", "裂凤关", "1级资源南9区", "4级资源南10区", "1级资源南11区", "4级资源南12区", "安甫镇",
     "4级资源南14区", "顺接寨", "1级资源南16区"],
    ["1级资源西22区", "1级资源西23区", "2级资源西24区", "2级资源南17区", "石门镇", "3级资源南19区", "永宁寨",
     "2级资源南21区", "1级资源南22区", "3级资源南23区", "1级资源南24区"]
]


def is_special(city):
    if not city or "外城" in city:
        return False
    for kw in ["城", "寨", "关", "镇"]:
        if kw in city:
            return True
    return False


def format_name(city):
    if not city:
        return "", ""
    special_names = ["安边镇", "定羌寨", "得胜寨", "雄武镇", "锁云关", "靖海镇", "镇龙关",
                     "御龙北城", "镇戎镇", "横江镇", "御龙西城", "天龙龙城", "御龙东城",
                     "清平寨", "平蛮寨", "怀远镇", "御龙南镇", "断岳关", "广信寨", "裂凤关",
                     "安甫镇", "顺接寨", "石门镇", "永宁寨"]
    if city in special_names:
        return city, ""
    if "级资源" in city:
        idx = city.find("级资源") + 2
        return city[:idx + 1], city[idx + 1:]
    return city, ""


def init_data():
    loaded_data = load_data()
    st.session_state.data = loaded_data if loaded_data else {}
    st.session_state.data_loaded = True


if not st.session_state.data_loaded:
    init_data()


def get_cell_state(row, col):
    key = f"{row},{col}"
    if key in st.session_state.data:
        item = st.session_state.data[key]
        try:
            expires = datetime.fromisoformat(item['expires'])
            now = beijing_now()
            if now >= expires:
                return "expired", None, None, item.get('side', 'friendly'), item.get('side_icon', '✅')
            else:
                remaining = expires - now
                total_seconds = int(remaining.total_seconds())
                hours = total_seconds // 3600
                mins = (total_seconds % 3600) // 60
                return "occupied", f"{hours}h{mins}m", expires, item.get('side', 'friendly'), item.get('side_icon', '✅')
        except:
            return "free", None, None, None, None
    return "free", None, None, None, None


def occupy_cell(row, col, minutes, side):
    name = CITIES[row][col]
    if not name:
        return False
    expires = beijing_now() + timedelta(minutes=float(minutes))
    side_icon = "✅" if side == "friendly" else "❌"
    st.session_state.data[f"{row},{col}"] = {
        "name": name,
        "expires": expires.isoformat(),
        "side": side,
        "side_icon": side_icon
    }
    save_data(st.session_state.data)
    return True


def delete_cell(row, col):
    key = f"{row},{col}"
    if key in st.session_state.data:
        del st.session_state.data[key]
        save_data(st.session_state.data)
        return True
    return False


def get_remaining_minutes(expires):
    remaining = expires - beijing_now()
    return int(remaining.total_seconds() // 60)


# ========== 批量选择按钮区域 ==========
def render_selection_buttons():
    for i in range(11):
        cols = st.columns(11, gap="small")
        for j in range(11):
            name = CITIES[i][j]
            key = f"{i},{j}"

            if not name:
                with cols[j]:
                    st.empty()
                continue

            state, timer, expires, side, side_icon = get_cell_state(i, j)
            line1, line2 = format_name(name)
            is_sp = is_special(name)
            is_selected = key in st.session_state.selected

            if is_selected:
                bg_color = "#fff9c4"
                text_color = "#333"
                border = "3px solid #ff9800"
            elif state in ["occupied", "expired"]:
                if side == "friendly":
                    bg_color = "#4CAF50"
                    text_color = "white"
                else:
                    bg_color = "#f44336"
                    text_color = "white"
                border = "2px solid #555"
            else:
                bg_color = "#f0f2f6"
                text_color = "#ff0000" if is_sp else "#333"
                border = "2px solid #aaa"

            if state == "occupied":
                if line2:
                    display_text = f"{side_icon} {line1}\n{line2}\n\n{timer}\n{expires.strftime('%H:%M')}"
                else:
                    display_text = f"{side_icon} {line1}\n\n{timer}\n{expires.strftime('%H:%M')}"
            elif state == "expired":
                if line2:
                    display_text = f"{side_icon} {line1}\n{line2}"
                else:
                    display_text = f"{side_icon} {line1}"
            else:
                if line2:
                    display_text = f"{line1}\n{line2}"
                else:
                    display_text = line1

            with cols[j]:
                st.markdown(f"""
                <style>
                div[data-testid="column"]:nth-child({j + 1}) .stButton button {{
                    background-color: {bg_color} !important;
                    color: {text_color} !important;
                    border: {border} !important;
                    width: 100% !important;
                    min-height: 100px !important;
                    white-space: pre-line !important;
                    line-height: 1.4 !important;
                    font-size: 12px !important;
                    font-family: 'SimSun', '宋体', 'Microsoft YaHei', serif !important;
                    border-radius: 8px !important;
                    padding: 8px 4px !important;
                    transition: all 0.2s ease !important;
                }}
                </style>
                """, unsafe_allow_html=True)

                if st.button(display_text, key=f"select_{i}_{j}", use_container_width=True):
                    if st.session_state.authenticated:
                        if st.session_state.select_mode:
                            if key in st.session_state.selected:
                                st.session_state.selected.remove(key)
                            else:
                                st.session_state.selected.add(key)
                            st.rerun()
                        elif st.session_state.single_mode:
                            st.session_state.single_selected_cell = (i, j)
                            st.rerun()


# ========== 显示区域 ==========
def render_display():
    cells_html = []
    for i in range(11):
        for j in range(11):
            name = CITIES[i][j]

            if not name:
                cells_html.append('<div style="background:#f0f0f0; border-radius:8px;"></div>')
                continue

            state, timer, expires, side, side_icon = get_cell_state(i, j)
            line1, line2 = format_name(name)
            is_sp = is_special(name)

            if state in ["occupied", "expired"]:
                if side == "friendly":
                    bg_color = "#4CAF50"
                    text_color = "white"
                else:
                    bg_color = "#f44336"
                    text_color = "white"
            else:
                bg_color = "#e8e8e8"
                text_color = "#333"

            if state == "occupied":
                if line2:
                    content = f'<div class="line1">{side_icon} {line1}</div><div class="line2">{line2}</div><div class="timer">⏰ {timer}</div><div class="expire">📅 {expires.strftime("%H:%M")}</div>'
                else:
                    content = f'<div class="line1">{side_icon} {line1}</div><div class="timer">⏰ {timer}</div><div class="expire">📅 {expires.strftime("%H:%M")}</div>'
            elif state == "expired":
                if line2:
                    content = f'<div class="line1">{side_icon} {line1}</div><div class="line2">{line2}</div>'
                else:
                    content = f'<div class="line1">{side_icon} {line1}</div>'
            else:
                if line2:
                    if is_sp:
                        content = f'<div class="line1">{line1}</div><div class="line2 special-text">{line2}</div>'
                    else:
                        content = f'<div class="line1">{line1}</div><div class="line2">{line2}</div>'
                else:
                    if is_sp:
                        content = f'<div class="line1 special-text">{line1}</div>'
                    else:
                        content = f'<div class="line1">{line1}</div>'

            cells_html.append(f'''
            <div class="city-cell" style="background-color:{bg_color}; color:{text_color};">
                {content}
            </div>
            ''')

    html = f'''
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
        <style>
            .city-grid {{
                display: grid;
                grid-template-columns: repeat(11, 1fr);
                gap: 6px;
                margin-top: 20px;
                margin-bottom: 20px;
            }}
            .city-cell {{
                aspect-ratio: 1 / 0.9;
                border-radius: 8px;
                padding: 8px 4px;
                text-align: center;
                display: flex;
                flex-direction: column;
                justify-content: center;
                font-size: 12px;
                font-family: 'SimSun', '宋体', 'Microsoft YaHei', serif;
                border: 1px solid #ddd;
            }}
            .line1 {{ font-size: 13px; font-weight: bold; }}
            .line2 {{ font-size: 13px; }}
            .timer {{ font-size: 11px; margin-top: 5px; }}
            .expire {{ font-size: 10px; margin-top: 2px; }}
            .special-text {{ color: #ff0000 !important; font-weight: bold !important; }}
        </style>
    </head>
    <body>
        <div class="city-grid">
            {''.join(cells_html)}
        </div>
    </body>
    </html>
    '''
    return html


# ========== 侧边栏 ==========
with st.sidebar:
    st.header("🎮 游戏控制")

    st.caption(f"{storage_mode}")

    st.markdown("### 🔐 管理员登录")

    if st.session_state.authenticated:
        st.success(f"✅ 已登录")
        if st.button("🚪 退出登录", use_container_width=True):
            st.session_state.authenticated = False
            st.session_state.select_mode = False
            st.session_state.single_mode = False
            st.session_state.selected.clear()
            st.session_state.single_selected_cell = None
            st.rerun()
    else:
        st.info("未登录，只能查看")
        password = st.text_input("请输入密码", type="password", key="login_password")
        if st.button("登录", use_container_width=True):
            if check_password(password):
                st.session_state.authenticated = True
                st.rerun()
            else:
                st.error("密码错误！")

    st.divider()

    if st.session_state.authenticated:
        st.markdown("### 📝 管理功能")

        mode_col1, mode_col2 = st.columns(2)
        with mode_col1:
            if st.button("📌 批量选择模式" + (" ✅" if st.session_state.select_mode else ""), use_container_width=True):
                st.session_state.select_mode = True
                st.session_state.single_mode = False
                st.session_state.selected.clear()
                st.session_state.single_selected_cell = None
                st.rerun()
        with mode_col2:
            if st.button("✏️ 单个修改模式" + (" ✅" if st.session_state.single_mode else ""), use_container_width=True):
                st.session_state.single_mode = True
                st.session_state.select_mode = False
                st.session_state.selected.clear()
                st.session_state.single_selected_cell = None
                st.rerun()

        st.divider()

        if st.session_state.select_mode:
            st.markdown(f"**已选择: {len(st.session_state.selected)} 个城池**")

            if st.session_state.selected:
                with st.expander("查看选中的城池", expanded=True):
                    for key in list(st.session_state.selected)[:15]:
                        r, c = map(int, key.split(','))
                        st.caption(f"• {CITIES[r][c]}")
                    if len(st.session_state.selected) > 15:
                        st.caption(f"... 还有 {len(st.session_state.selected) - 15} 个")

            batch_minutes = st.number_input("保护时间(分钟)", min_value=1, max_value=1440, value=180, step=5)

            col1, col2 = st.columns(2)
            with col1:
                if st.button(f"✅ 批量己方 ({batch_minutes}分钟)", use_container_width=True):
                    for key in list(st.session_state.selected):
                        r, c = map(int, key.split(','))
                        name = CITIES[r][c]
                        if name:
                            expires = beijing_now() + timedelta(minutes=batch_minutes)
                            st.session_state.data[key] = {
                                "name": name,
                                "expires": expires.isoformat(),
                                "side": "friendly",
                                "side_icon": "✅"
                            }
                    save_data(st.session_state.data)
                    st.session_state.selected.clear()
                    st.session_state.select_mode = False
                    st.rerun()
            with col2:
                if st.button(f"❌ 批量敌方 ({batch_minutes}分钟)", use_container_width=True):
                    for key in list(st.session_state.selected):
                        r, c = map(int, key.split(','))
                        name = CITIES[r][c]
                        if name:
                            expires = beijing_now() + timedelta(minutes=batch_minutes)
                            st.session_state.data[key] = {
                                "name": name,
                                "expires": expires.isoformat(),
                                "side": "enemy",
                                "side_icon": "❌"
                            }
                    save_data(st.session_state.data)
                    st.session_state.selected.clear()
                    st.session_state.select_mode = False
                    st.rerun()

            if st.button("清空选择", use_container_width=True):
                st.session_state.selected.clear()
                st.rerun()

        elif st.session_state.single_mode:
            st.markdown("**✏️ 单个修改模式**")
            st.caption("点击任意城池选择，然后在下方编辑")

            if st.session_state.single_selected_cell:
                row, col = st.session_state.single_selected_cell
                selected_city_name = CITIES[row][col]
                st.success(f"✅ 当前选中: **{selected_city_name}**")

                key = f"{row},{col}"
                current_data = st.session_state.data.get(key, {})
                current_minutes = 180

                if 'expires' in current_data:
                    try:
                        expires = datetime.fromisoformat(current_data['expires'])
                        remaining = expires - beijing_now()
                        if remaining.total_seconds() > 0:
                            current_minutes = int(remaining.total_seconds() // 60)
                        else:
                            current_minutes = 0
                    except:
                        pass

                st.markdown("---")
                st.markdown("**编辑城池**")

                new_minutes = st.number_input("保护时间(分钟)", min_value=1, max_value=1440,
                                              value=max(1, current_minutes), step=5, key="single_edit_minutes")

                col1, col2 = st.columns(2)
                with col1:
                    if st.button("✅ 标记为己方", use_container_width=True, key="single_friendly"):
                        occupy_cell(row, col, new_minutes, "friendly")
                        st.session_state.single_selected_cell = None
                        st.rerun()
                with col2:
                    if st.button("❌ 标记为敌方", use_container_width=True, key="single_enemy"):
                        occupy_cell(row, col, new_minutes, "enemy")
                        st.session_state.single_selected_cell = None
                        st.rerun()

                if st.button("🗑️ 清除（变为空闲）", use_container_width=True, key="single_clear"):
                    delete_cell(row, col)
                    st.session_state.single_selected_cell = None
                    st.rerun()
            else:
                st.info("👆 点击任意城池进行选择")

            st.markdown("---")
            st.markdown("**或从列表选择**")
            all_cities = []
            city_coords = {}
            for i in range(11):
                for j in range(11):
                    name = CITIES[i][j]
                    if name:
                        all_cities.append(name)
                        city_coords[name] = (i, j)

            selected_city = st.selectbox("选择城池", [""] + all_cities, key="single_select")
            if selected_city:
                coords = city_coords.get(selected_city)
                if coords:
                    st.session_state.single_selected_cell = coords
                    st.rerun()

        st.divider()

    # ========== 分类统计 ==========
    st.markdown("### ⏰ 即将到期（<60分钟）")

    now = beijing_now()
    friendly_soon = []
    enemy_soon = []

    for key, item in st.session_state.data.items():
        try:
            expires = datetime.fromisoformat(item['expires'])
            if expires > now:
                remaining_minutes = get_remaining_minutes(expires)
                if remaining_minutes < 60:
                    city_name = item['name']
                    side = item.get('side', 'friendly')
                    if side == 'friendly':
                        friendly_soon.append((city_name, remaining_minutes, expires))
                    else:
                        enemy_soon.append((city_name, remaining_minutes, expires))
        except:
            pass

    friendly_soon.sort(key=lambda x: x[1])
    enemy_soon.sort(key=lambda x: x[1])

    if friendly_soon:
        st.markdown("**✅ 己方即将到期**")
        for name, minutes, expires in friendly_soon[:10]:
            st.write(f"• {name}: {minutes}分钟")
            st.caption(f"  到期: {expires.strftime('%H:%M')}")
    else:
        st.caption("暂无己方即将到期城池")

    st.markdown("---")

    if enemy_soon:
        st.markdown("**❌ 敌方即将到期**")
        for name, minutes, expires in enemy_soon[:10]:
            st.write(f"• {name}: {minutes}分钟")
            st.caption(f"  到期: {expires.strftime('%H:%M')}")
    else:
        st.caption("暂无敌方即将到期城池")

    st.divider()

    # 统计
    st.markdown("### 📊 统计")
    friendly = 0
    enemy = 0
    for item in st.session_state.data.values():
        if item.get('side') == 'friendly':
            friendly += 1
        else:
            enemy += 1

    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("🏯 己方", friendly)
    with col2:
        st.metric("⚔️ 敌方", enemy)
    with col3:
        st.metric("🆓 空闲", 120 - friendly - enemy)

    if st.button("🗑️ 重置全部", use_container_width=True):
        if st.session_state.authenticated:
            st.session_state.data = {}
            st.session_state.selected.clear()
            st.session_state.single_selected_cell = None
            save_data({})
            st.rerun()

# ========== 主界面 ==========
st.title("🏰 城池占领游戏")
st.caption(f"🕐 北京时间: {beijing_now().strftime('%Y-%m-%d %H:%M:%S')}")

if not st.session_state.authenticated:
    st.info("🔐 只读模式，登录后可修改")

if st.session_state.select_mode or st.session_state.single_mode:
    if st.session_state.select_mode:
        st.warning("🔧 批量选择模式已开启 - 点击格子可多选，选中的格子会有金色边框，然后去左侧边栏批量标记")
    else:
        st.info("✏️ 单个修改模式 - 点击格子选中，然后在左侧边栏编辑")
    render_selection_buttons()
else:
    st.components.v1.html(render_display(), height=950, scrolling=True)
