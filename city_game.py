import streamlit as st
from datetime import datetime, timedelta
import json
import os
import hashlib
import pytz

st.set_page_config(page_title="龙城争霸", layout="wide")

DATA_FILE = "city_data.json"

# ========== 时区设置 ==========
BEIJING_TZ = pytz.timezone('Asia/Shanghai')


def beijing_now():
    """获取当前北京时间（naive datetime，方便存储和比较）"""
    return datetime.now(BEIJING_TZ).replace(tzinfo=None)


# ========== 密码配置 ==========
ADMIN_PASSWORD_HASH = hashlib.md5("admin123".encode()).hexdigest()


def check_password(password):
    return hashlib.md5(password.encode()).hexdigest() == ADMIN_PASSWORD_HASH


# 初始化密码状态
if 'authenticated' not in st.session_state:
    st.session_state.authenticated = False
if 'auth_failed' not in st.session_state:
    st.session_state.auth_failed = False

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


def load_data():
    if os.path.exists(DATA_FILE):
        try:
            with open(DATA_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        except:
            return {}
    return {}


def save_data(data):
    with open(DATA_FILE, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


# 初始化数据
if 'data' not in st.session_state:
    st.session_state.data = load_data()
if 'select_mode' not in st.session_state:
    st.session_state.select_mode = False
if 'selected' not in st.session_state:
    st.session_state.selected = set()
if 'batch_minutes' not in st.session_state:
    st.session_state.batch_minutes = 180


def get_cell_state(row, col):
    """获取城池状态，倒计时结束后只清除时间，保留敌我标记"""
    key = f"{row},{col}"
    if key in st.session_state.data:
        item = st.session_state.data[key]
        try:
            expires = datetime.fromisoformat(item['expires'])
            if beijing_now() >= expires:
                # 倒计时结束：只清除时间，保留 side 和 side_icon
                st.session_state.data[key] = {
                    "name": item['name'],
                    "side": item.get('side', 'friendly'),
                    "side_icon": item.get('side_icon', '✅'),
                    "expired": True
                }
                save_data(st.session_state.data)
                return "occupied_permanent", None, None, item.get('side', 'friendly'), item.get('side_icon', '✅')
            else:
                remaining = expires - beijing_now()
                total_seconds = int(remaining.total_seconds())
                hours = total_seconds // 3600
                mins = (total_seconds % 3600) // 60
                return "occupied", f"{hours}h{mins}m", expires, item.get('side', 'friendly'), item.get('side_icon', '✅')
        except:
            if item.get('expired') or 'side' in item:
                return "occupied_permanent", None, None, item.get('side', 'friendly'), item.get('side_icon', '✅')
            return "free", None, None, None, None
    return "free", None, None, None, None


def occupy_cell(row, col, minutes, side):
    name = CITIES[row][col]
    if not name:
        return
    expires = beijing_now() + timedelta(minutes=float(minutes))
    side_icon = "✅" if side == "friendly" else "❌"
    st.session_state.data[f"{row},{col}"] = {
        "name": name,
        "expires": expires.isoformat(),
        "side": side,
        "side_icon": side_icon
    }
    save_data(st.session_state.data)


def batch_occupy(side, minutes):
    for key in list(st.session_state.selected):
        r, c = map(int, key.split(','))
        name = CITIES[r][c]
        if name:
            expires = beijing_now() + timedelta(minutes=minutes)
            side_icon = "✅" if side == "friendly" else "❌"
            st.session_state.data[key] = {
                "name": name,
                "expires": expires.isoformat(),
                "side": side,
                "side_icon": side_icon
            }
    save_data(st.session_state.data)
    st.session_state.selected.clear()
    st.session_state.select_mode = False


# ========== 侧边栏 ==========
with st.sidebar:
    st.header("🎮 游戏控制")

    # ========== 登录区域 ==========
    st.markdown("### 🔐 管理员登录")

    if st.session_state.authenticated:
        st.success(f"✅ 已登录 (管理员)")
        if st.button("🚪 退出登录", use_container_width=True):
            st.session_state.authenticated = False
            st.session_state.select_mode = False
            st.session_state.selected.clear()
            st.rerun()
    else:
        st.info("未登录，只能查看")
        password = st.text_input("请输入密码", type="password", key="login_password")

        col1, col2 = st.columns(2)
        with col1:
            if st.button("登录", use_container_width=True):
                if check_password(password):
                    st.session_state.authenticated = True
                    st.session_state.auth_failed = False
                    st.rerun()
                else:
                    st.session_state.auth_failed = True
        if st.session_state.auth_failed:
            st.error("密码错误！")

    st.divider()

    # ========== 管理员功能（仅登录后可见） ==========
    if st.session_state.authenticated:
        st.markdown("### 📝 管理功能")

        mode_label = "✏️ 批量选择模式" + (" ✅" if st.session_state.select_mode else "")
        if st.button(mode_label, use_container_width=True):
            st.session_state.select_mode = not st.session_state.select_mode
            if not st.session_state.select_mode:
                st.session_state.selected.clear()
            st.rerun()

        if st.session_state.select_mode:
            st.markdown(f"**已选择: {len(st.session_state.selected)} 个城池**")

            if st.session_state.selected:
                with st.expander("查看选中的城池"):
                    for key in list(st.session_state.selected)[:10]:
                        r, c = map(int, key.split(','))
                        st.caption(f"• {CITIES[r][c]}")
                    if len(st.session_state.selected) > 10:
                        st.caption(f"... 还有 {len(st.session_state.selected) - 10} 个")

            st.markdown("**批量时间设置**")
            batch_minutes = st.number_input("保护时间(分钟)", min_value=1, max_value=1440,
                                            value=st.session_state.batch_minutes, step=5)
            st.session_state.batch_minutes = batch_minutes

            col1, col2 = st.columns(2)
            with col1:
                if st.button(f"✅ 批量己方 ({batch_minutes}分钟)", use_container_width=True):
                    batch_occupy("friendly", batch_minutes)
                    st.rerun()
            with col2:
                if st.button(f"❌ 批量敌方 ({batch_minutes}分钟)", use_container_width=True):
                    batch_occupy("enemy", batch_minutes)
                    st.rerun()

            if st.button("清空选择", use_container_width=True):
                st.session_state.selected.clear()
                st.rerun()

        st.divider()

    # ========== 统计信息（所有人可见） ==========
    st.markdown("### 📊 统计信息")

    now = beijing_now()
    friendly = 0
    enemy = 0
    for item in st.session_state.data.values():
        try:
            if 'side' in item:
                if item.get('side') == 'friendly':
                    friendly += 1
                else:
                    enemy += 1
        except:
            pass

    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("🏯 己方", friendly)
    with col2:
        st.metric("⚔️ 敌方", enemy)
    with col3:
        st.metric("🆓 空闲", 120 - friendly - enemy)

    st.divider()

    st.markdown("### ⏰ 即将到期")
    soon = []
    for key, item in st.session_state.data.items():
        try:
            if 'expires' in item:
                expires = datetime.fromisoformat(item['expires'])
                if expires > now:
                    remaining = expires - now
                    soon.append((item['name'], remaining, item.get('side'), expires))
        except:
            pass
    soon.sort(key=lambda x: x[1])
    for name, remaining, side, expires in soon[:5]:
        total_seconds = int(remaining.total_seconds())
        h = total_seconds // 3600
        m = (total_seconds % 3600) // 60
        icon = "✅" if side == 'friendly' else "❌"
        st.write(f"{icon} {name}: {h}h{m}m")
        st.caption(f"   到期: {expires.strftime('%H:%M')}")

    st.divider()

    # ========== 重置功能 ==========
    if st.button("🗑️ 重置全部", use_container_width=True):
        if st.session_state.authenticated:
            st.session_state.data = {}
            st.session_state.selected.clear()
            if os.path.exists(DATA_FILE):
                os.remove(DATA_FILE)
            st.rerun()
        else:
            st.error("需要管理员权限！")

# ========== 主界面 ==========
st.title("🏰 城池占领游戏")

# 显示当前北京时间
current_time = beijing_now().strftime("%Y-%m-%d %H:%M:%S")
st.caption(f"🕐 当前北京时间: {current_time}")

# 未登录时显示提示
if not st.session_state.authenticated:
    st.info("🔐 当前为只读模式，如需修改城池状态，请在左侧边栏登录")

    with st.expander("📖 查看说明"):
        st.markdown("""
        - ✅ 绿色格子：己方占领
        - ❌ 红色格子：敌方占领
        - 灰色格子：空闲可占领
        - 🔴 红色加粗文字：城、寨、关、镇等特殊地块
        - ⏰ 倒计时结束后，保留敌我标记，不再显示时间
        - 如需修改，请在左侧边栏输入密码登录
        """)

    st.divider()

# 全局样式
st.markdown("""
<style>
.stButton > button {
    width: 100% !important;
    min-height: 95px !important;
    white-space: pre-line !important;
    line-height: 1.3 !important;
    font-size: 11px !important;
    border-radius: 8px !important;
    padding: 6px 3px !important;
    transition: all 0.2s ease !important;
}
.stButton > button:hover {
    transform: scale(1.02) !important;
}
</style>
""", unsafe_allow_html=True)

# 使用 columns 创建网格
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

        # 构建按钮文字
        if state == "occupied":
            if line2:
                display_text = f"{side_icon} {line1}\n{line2}\n\n⏰ {timer}\n📅 {expires.strftime('%H:%M')}"
            else:
                display_text = f"{side_icon} {line1}\n\n⏰ {timer}\n📅 {expires.strftime('%H:%M')}"
        elif state == "occupied_permanent":
            if line2:
                display_text = f"{side_icon} {line1}\n{line2}"
            else:
                display_text = f"{side_icon} {line1}"
        else:
            if line2:
                display_text = f"{line1}\n{line2}"
            else:
                display_text = line1

        # 确定样式
        if is_selected:
            bg_color = "#fff9c4"
            text_color = "#333"
            border = "3px solid #ff9800"
        elif state in ["occupied", "occupied_permanent"]:
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

        with cols[j]:
            # 设置按钮样式
            st.markdown(f"""
            <style>
            div[data-testid="column"]:nth-child({j + 1}) .stButton button {{
                background-color: {bg_color} !important;
                color: {text_color} !important;
                border: {border} !important;
                font-weight: {'bold' if is_sp else 'normal'} !important;
            }}
            </style>
            """, unsafe_allow_html=True)

            button_key = f"cell_{i}_{j}"
            if st.button(display_text, key=button_key, use_container_width=True):
                if st.session_state.authenticated:
                    if st.session_state.select_mode:
                        if key in st.session_state.selected:
                            st.session_state.selected.remove(key)
                        else:
                            st.session_state.selected.add(key)
                        st.rerun()
                    else:
                        st.session_state['pending_row'] = i
                        st.session_state['pending_col'] = j
                        st.rerun()
                else:
                    st.error("请先在左侧边栏登录")
                    st.toast("请先在左侧边栏输入密码登录", icon="🔐")

# 处理占领弹窗（只有登录后才会进入）
if 'pending_row' in st.session_state and st.session_state.authenticated:
    row = st.session_state.pending_row
    col = st.session_state.pending_col
    name = CITIES[row][col]

    with st.popover(f"⚙️ 占领 {name}", use_container_width=True):
        st.markdown(f"**{name}**")
        minutes = st.number_input("保护时间(分钟)", min_value=1, max_value=1440, value=180, step=5,
                                  key="occupy_minutes")
        col1, col2 = st.columns(2)
        with col1:
            if st.button("✅ 己方", use_container_width=True):
                occupy_cell(row, col, minutes, "friendly")
                del st.session_state.pending_row
                del st.session_state.pending_col
                st.rerun()
        with col2:
            if st.button("❌ 敌方", use_container_width=True):
                occupy_cell(row, col, minutes, "enemy")
                del st.session_state.pending_row
                del st.session_state.pending_col
                st.rerun()

# 底部
st.markdown("---")
col1, col2, col3 = st.columns([1, 2, 1])
with col2:
    if st.button("🔄 刷新数据", use_container_width=True):
        st.rerun()
