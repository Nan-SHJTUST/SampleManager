import streamlit as st
import pandas as pd
import os
import json
import subprocess
import shutil
import io
import re
from datetime import datetime
import time

# ================= 0. 全局配置 =================
BASE_DIR = 'Sample_System_V25'
PROJECTS_DIR = os.path.join(BASE_DIR, 'Projects')
BACKUP_DIR = os.path.join(BASE_DIR, 'Backups')
CONFIG_FILE = os.path.join(BASE_DIR, 'presets.json')

for path in [BASE_DIR, PROJECTS_DIR, BACKUP_DIR]:
    if not os.path.exists(path): os.makedirs(path)

st.set_page_config(page_title="实验室 V25", layout="wide", page_icon="🧪")

# === 🎨 CSS 样式 (保持 V24 的蓝色主题与悬浮设计) ===
st.markdown("""
<style>
    :root { --primary-color: #007bff; }
    
    /* 悬浮保存球 */
    section[data-testid="stMain"] button[kind="primary"] {
        position: fixed !important; bottom: 40px !important; right: 40px !important;
        z-index: 999999 !important; width: auto !important; min-width: 150px !important;
        height: 50px !important; border-radius: 25px !important;
        background-color: #007bff !important; color: white !important;
        box-shadow: 0 6px 16px rgba(0, 123, 255, 0.4) !important;
        border: 2px solid white !important; font-size: 1.1em !important; font-weight: bold !important;
    }
    section[data-testid="stMain"] button[kind="primary"]:hover {
        background-color: #0056b3 !important; transform: scale(1.05) !important;
    }

    .block-container { padding-bottom: 150px !important; }

    button[kind="secondary"] {
        background-color: white !important; color: #333 !important; border: 1px solid #d1d5db !important;
    }
    
    .module-tag {
        background:#e3f2fd; color:#1565c0; border:1px solid #90caf9; 
        padding:2px 8px; border-radius:12px; font-size:0.8em; margin-right:5px;
    }
    
    .admin-zone {
        background-color: #f8f9fa; padding: 10px; border-radius: 6px;
        border: 1px dashed #ccc; margin-bottom: 10px;
    }
    
    /* 新增：文件区样式 */
    .file-zone {
        border-top: 1px solid #eee; margin-top: 10px; padding-top: 10px;
    }
</style>
""", unsafe_allow_html=True)

# ================= 1. 核心逻辑 =================

def load_presets():
    if not os.path.exists(CONFIG_FILE):
        defaults = {
            "PLD_Thin_Film": {
                "Deposition": ["Laser_Energy", "Oxygen_Pressure", "Temperature", "Time"], 
                "XRD_Test": ["Scan_Range", "Speed"]
            },
            "Ceramic_Sintering": {
                "Pressing": ["Pressure", "Time"], 
                "Sintering": ["Temperature", "Dwell_Time"], 
                "EIS_Test": ["Temperature"]
            }
        }
        with open(CONFIG_FILE, 'w', encoding='utf-8') as f:
            json.dump(defaults, f, ensure_ascii=False, indent=4)
    try:
        with open(CONFIG_FILE, 'r', encoding='utf-8') as f: return json.load(f)
    except: return {}

def get_project_csv(project_name):
    return os.path.join(PROJECTS_DIR, f"{project_name}.csv")

def get_sample_folder(project_name, sample_id):
    path = os.path.join(PROJECTS_DIR, project_name + "_Files", sample_id)
    if not os.path.exists(path): os.makedirs(path)
    return path

def backup_project(project_name):
    src = get_project_csv(project_name)
    if os.path.exists(src):
        date_str = datetime.now().strftime("%Y-%m-%d")
        dst = os.path.join(BACKUP_DIR, f"{project_name}_{date_str}.csv")
        if not os.path.exists(dst): shutil.copy2(src, dst)

def load_project_df(project_name):
    backup_project(project_name)
    path = get_project_csv(project_name)
    if os.path.exists(path):
        try:
            df = pd.read_csv(path)
            if "Content_JSON" not in df.columns: df["Content_JSON"] = "{}"
            df = df.fillna("")
            for col in df.columns:
                if col != "Content_JSON": df[col] = df[col].astype(str)
            return df
        except: return pd.DataFrame()
    return pd.DataFrame(columns=["样品编号", "创建日期", "状态", "备注", "Content_JSON"])

def save_project_df(project_name, df):
    path = get_project_csv(project_name)
    df.to_csv(path, index=False)

def open_local_file(filepath):
    if os.path.exists(filepath):
        if os.name == 'nt':
            try: os.startfile(filepath)
            except Exception as e: st.error(f"Error: {e}")
    else: st.error("文件不存在")

def open_folder(path):
    if os.path.exists(path) and os.name == 'nt':
        subprocess.Popen(f'explorer "{path}"')

def sanitize_filename(name):
    return re.sub(r'[\\/*?:"<>|]', "_", name)

# --- 业务操作 ---
def create_sample(project_name, df, template_data=None):
    i = 1
    existing = set(df["样品编号"].values)
    while True:
        new_id = f"{project_name}-{i:03d}"
        if new_id not in existing: break
        i += 1
    content = {}
    if template_data:
        for mod, fields in template_data.items(): content[mod] = {f: "" for f in fields}
    new_row = {
        "样品编号": new_id, "创建日期": datetime.now().strftime("%Y-%m-%d"),
        "状态": "制备中", "备注": "",
        "Content_JSON": json.dumps(content, ensure_ascii=False)
    }
    df = pd.concat([df, pd.DataFrame([new_row])], ignore_index=True)
    save_project_df(project_name, df)
    get_sample_folder(project_name, new_id)
    return new_id

def clone_sample(project_name, df, src_id):
    src = df[df["样品编号"] == src_id]
    if src.empty: return
    i = 1
    existing = set(df["样品编号"].values)
    while True:
        new_id = f"{project_name}-{i:03d}"
        if new_id not in existing: break
        i += 1
    row = src.iloc[0].copy()
    row["样品编号"] = new_id
    row["创建日期"] = datetime.now().strftime("%Y-%m-%d")
    row["状态"] = "制备中"
    row["备注"] = f"克隆自 {src_id}"
    df = pd.concat([df, pd.DataFrame([row])], ignore_index=True)
    save_project_df(project_name, df)
    get_sample_folder(project_name, new_id)
    return new_id

def delete_sample(project_name, df, sid):
    df = df[df["样品编号"] != sid]
    save_project_df(project_name, df)
    f = get_sample_folder(project_name, sid)
    if os.path.exists(f): os.rename(f, f + "_del_" + datetime.now().strftime("%H%M%S"))
    return df

def rename_sample(project_name, df, old_id, new_id):
    if new_id in df["样品编号"].values: return False, "编号已存在"
    old_f = get_sample_folder(project_name, old_id)
    new_f = os.path.join(PROJECTS_DIR, project_name + "_Files", new_id)
    try:
        if os.path.exists(old_f): os.rename(old_f, new_f)
    except: return False, "文件夹占用"
    idx = df[df["样品编号"]==old_id].index[0]
    df.at[idx, "样品编号"] = new_id
    save_project_df(project_name, df)
    return True, "成功"

# ================= 2. 主界面 =================

with st.sidebar:
    st.title("🧪 实验室 V25")
    projects = [f.replace('.csv', '') for f in os.listdir(PROJECTS_DIR) if f.endswith('.csv')]
    if projects:
        current_project = st.selectbox("当前项目", projects)
    else:
        current_project = None
        st.warning("请新建项目")
        
    with st.expander("🛠️ 项目管理"):
        np = st.text_input("新建项目名")
        if st.button("创建", key="cp", use_container_width=True):
            if np and np not in projects:
                save_project_df(np, pd.DataFrame(columns=["样品编号", "创建日期", "状态", "备注", "Content_JSON"]))
                st.rerun()

if current_project:
    df = load_project_df(current_project)
    if 'edit_id' not in st.session_state: st.session_state['edit_id'] = None

    # --- A. 列表模式 ---
    if st.session_state['edit_id'] is None:
        c1, c2 = st.columns([2, 3])
        with c1:
            presets = load_presets()
            with st.popover("➕ 新建样品", use_container_width=True):
                if st.button("📄 空白样品", use_container_width=True):
                    nid = create_sample(current_project, df, None)
                    st.session_state['edit_id'] = nid
                    st.rerun()
                for t in presets:
                    if st.button(f"📑 {t}", use_container_width=True):
                        nid = create_sample(current_project, df, presets[t])
                        st.session_state['edit_id'] = nid
                        st.rerun()
        with c2: search = st.text_input("Search", label_visibility="collapsed", placeholder="搜索...")
        
        st.divider()
        view_df = df
        if search: view_df = df[df.apply(lambda x: str(x.values).find(search)!=-1, axis=1)]

        for idx, row in view_df.iloc[::-1].iterrows():
            sid = row['样品编号']
            with st.container():
                cols = st.columns([0.5, 3, 2, 2])
                cols[0].checkbox("", key=f"c_{sid}", label_visibility="collapsed")
                with cols[1]:
                    if st.button(f"📄 {sid}", key=f"btn_{sid}", use_container_width=True):
                        st.session_state['edit_id'] = sid
                        st.rerun()
                    st.caption(f"{str(row['备注'])[:20]}")
                with cols[2]:
                    stt = row['状态']
                    color = "orange" if stt=="制备中" else "green" if stt=="完成" else "blue"
                    st.markdown(f":{color}[● {stt}] &nbsp; {row['创建日期']}")
                with cols[3]:
                    b1, b2, b3 = st.columns(3)
                    with b1.popover("✏️"):
                        nn = st.text_input("新ID", value=sid, key=f"rn_{sid}")
                        if st.button("确认", key=f"rnb_{sid}"):
                            ok, msg = rename_sample(current_project, df, sid, nn)
                            if ok: st.rerun()
                    if b2.button("🐑", key=f"cl_{sid}"): 
                        clone_sample(current_project, df, sid); st.rerun()
                    if b3.button("🗑️", key=f"dl_{sid}", type="secondary"): 
                        delete_sample(current_project, df, sid); st.rerun()
                st.markdown("<hr style='margin:5px 0'>", unsafe_allow_html=True)

    # --- B. 编辑模式 ---
    else:
        sid = st.session_state['edit_id']
        try:
            row_idx = df[df["样品编号"]==sid].index[0]
            cur = df.loc[row_idx]
            content_json = json.loads(cur['Content_JSON'])
        except: st.session_state['edit_id']=None; st.rerun()

        c1, c2, c3 = st.columns([1, 4, 1.5])
        if c1.button("⬅️ 返回列表", use_container_width=True): st.session_state['edit_id']=None; st.rerun()
        c2.markdown(f"### 🛠️ {sid}")
        folder = get_sample_folder(current_project, sid)
        # 顶部的总文件夹按钮保留
        if c3.button("📂 打开文件夹", use_container_width=True): open_folder(folder)
        st.markdown("---")

        sc1, sc2, sc3 = st.columns(3)
        sts = ["制备中", "待测试", "完成", "报废"]
        idx_s = sts.index(cur["状态"]) if cur["状态"] in sts else 0
        n_st = sc1.selectbox("状态", sts, index=idx_s)
        n_dt = sc2.text_input("日期", value=str(cur["创建日期"]))
        n_nt = sc3.text_input("备注", value=str(cur["备注"]))

        st.markdown("#### 🧬 实验参数与数据")
        
        final_content = {}
        deleted_modules = []
        
        for mod_name, params in content_json.items():
            with st.container():
                # 模块标题行
                mc1, mc2 = st.columns([5, 1])
                mc1.markdown(f"#### 🔹 {mod_name}")
                # 模块级的“打开文件夹”按钮，方便直接定位
                if mc2.button("📂 文件夹", key=f"open_mod_{mod_name}", help="打开此样品的文件夹"):
                    open_folder(folder)

                # 管理区
                with st.expander("⚙️ 管理模块 (增删参数)"):
                    ac1, ac2 = st.columns([4, 1])
                    with ac1:
                        aac1, aac2, aac3 = st.columns([2, 2, 3])
                        nk = aac1.text_input("名", placeholder="+参数", key=f"npk_{mod_name}", label_visibility="collapsed")
                        nv = aac2.text_input("值", placeholder="值", key=f"npv_{mod_name}", label_visibility="collapsed")
                        dk = aac3.multiselect("删参数", list(params.keys()), key=f"dk_{mod_name}", label_visibility="collapsed")
                    with ac2:
                        if st.checkbox("删模块", key=f"dm_{mod_name}"): deleted_modules.append(mod_name)

                # 参数区
                curr_params = params.copy()
                if nk: curr_params[nk] = nv
                valid_params = {}
                if curr_params:
                    p_cols = st.columns(3)
                    idx = 0
                    for k, v in curr_params.items():
                        if k not in dk:
                            with p_cols[idx % 3]:
                                valid_params[k] = st.text_input(k, value=str(v), key=f"v_{sid}_{mod_name}_{k}")
                            idx += 1

                # --- 文件展示区 (核心改进) ---
                st.markdown('<div class="file-zone">', unsafe_allow_html=True)
                
                prefix = f"[{mod_name}]--"
                file_count = 0
                if os.path.exists(folder):
                    # 统计该模块下的文件
                    fs = [f for f in os.listdir(folder) if f.startswith(prefix)]
                    file_count = len(fs)
                
                fc1, fc2 = st.columns([3, 1])
                
                with fc1:
                    # 默认折叠，只显示数量，解决 EIS 几十个文件刷屏的问题
                    with st.expander(f"📎 关联文件 (共 {file_count} 个)"):
                        if file_count > 0:
                            for f in fs:
                                clean_name = f.replace(prefix, "")
                                f_path = os.path.join(folder, f)
                                
                                # 单行显示：文件名 + 🚀打开按钮
                                fr1, fr2 = st.columns([4, 1])
                                fr1.caption(clean_name)
                                if fr2.button("🚀", key=f"op_{f}", help="打开文件"):
                                    open_local_file(f_path)
                        else:
                            st.caption("暂无文件，请上传或直接拖入文件夹")

                with fc2:
                    up = st.file_uploader("添加", key=f"u_{mod_name}", label_visibility="collapsed")
                    if up:
                        safe_name = sanitize_filename(up.name)
                        with open(os.path.join(folder, prefix+safe_name), "wb") as f: f.write(up.getbuffer())
                        st.toast("已上传")
                        st.rerun()
                
                st.markdown('</div>', unsafe_allow_html=True)

                if mod_name not in deleted_modules: final_content[mod_name] = valid_params
                st.markdown("---")

        nm = st.text_input("➕ 添加新模块", placeholder="输入名称...")
        if nm and nm not in final_content: final_content[nm] = {}

        st.markdown("<br><br><br>", unsafe_allow_html=True)
        if st.button("💾 保存所有修改 (Save)", type="primary"):
            df.at[row_idx, "状态"] = n_st
            df.at[row_idx, "创建日期"] = n_dt
            df.at[row_idx, "备注"] = n_nt
            df.at[row_idx, "Content_JSON"] = json.dumps(final_content, ensure_ascii=False)
            save_project_df(current_project, df)
            st.toast("✅ 已保存！")
            time.sleep(0.5)
            st.rerun()

else: st.info("请新建项目")