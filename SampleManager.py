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
import gc

# ================= 0. 全局配置 =================
BASE_DIR = "Sample_System_V3.0"
PROJECTS_DIR = os.path.normpath(os.path.join(BASE_DIR, "Projects"))
BACKUP_DIR = os.path.normpath(os.path.join(BASE_DIR, "Backups"))
CONFIG_FILE = os.path.normpath(os.path.join(BASE_DIR, "presets.json"))

for path in [BASE_DIR, PROJECTS_DIR, BACKUP_DIR]:
    if not os.path.exists(path):
        os.makedirs(path)

st.set_page_config(page_title="SampleManager V3.0", layout="wide", page_icon="🧪")

# === 🎨 CSS ===
st.markdown(
    """
<style>
    :root { --primary-color: #007bff; }
    section[data-testid="stMain"] button[kind="primary"]{
        position: fixed !important; bottom: 40px !important; right: 40px !important;
        z-index: 999999 !important; width: auto !important; min-width: 150px !important;
        height: 50px !important; border-radius: 25px !important;
        background-color: #007bff !important; color: white !important;
        box-shadow: 0 6px 16px rgba(0, 123, 255, 0.4) !important;
        border: 2px solid white !important; font-size: 1.1em !important; font-weight: bold !important;
    }
    .block-container { padding-bottom: 150px !important; }
    .module-tag {
        display: inline-block;
        background: #e3f2fd; color: #1565c0; border: 1px solid #90caf9; 
        padding: 1px 8px; border-radius: 10px; font-size: 0.75em; 
        margin-right: 4px; margin-bottom: 2px; font-weight: 500;
    }
    .file-zone { border-top: 1px solid #eee; margin-top: 10px; padding-top: 10px; }
    div[data-testid="stHorizontalBlock"] > div { padding: 0px 5px !important; }
</style>
""",
    unsafe_allow_html=True,
)

# ================= 1. 核心工具逻辑 =================

def execute_backup(project_name):
    src = get_project_csv(project_name)
    if os.path.exists(src):
        date_str = datetime.now().strftime("%Y-%m-%d")
        dst = os.path.join(BACKUP_DIR, f"{project_name}_{date_str}.csv")
        try: shutil.copy2(src, dst)
        except: pass

def load_presets():
    if not os.path.exists(CONFIG_FILE):
        defaults = {
            "PLD_Thin_Film": {"Deposition": ["Laser_Energy", "Oxygen_Pressure"], "XRD_Test": ["Scan_Range"]},
            "Ceramic_Sintering": {"Pressing": ["Pressure"], "Sintering": ["Temperature"]}
        }
        with open(CONFIG_FILE, "w", encoding="utf-8") as f:
            json.dump(defaults, f, ensure_ascii=False, indent=4)
    try:
        with open(CONFIG_FILE, "r", encoding="utf-8") as f: return json.load(f)
    except: return {}

def save_presets(presets):
    with open(CONFIG_FILE, "w", encoding="utf-8") as f:
        json.dump(presets, f, ensure_ascii=False, indent=4)

def get_project_csv(name): return os.path.join(PROJECTS_DIR, f"{name}.csv")
def get_project_folder(name): return os.path.join(PROJECTS_DIR, f"{name}_Files")
def get_sample_folder(proj, sid):
    p = os.path.join(get_project_folder(proj), sid)
    if not os.path.exists(p): os.makedirs(p)
    return p

def load_project_df(project_name):
    execute_backup(project_name)
    src = get_project_csv(project_name)
    if os.path.exists(src):
        try:
            with open(src, 'r', encoding='utf-8') as f:
                df = pd.read_csv(f)
            if "Content_JSON" not in df.columns: df["Content_JSON"] = "{}"
            return df.fillna("").astype(str)
        except: return pd.DataFrame(columns=["样品编号", "创建日期", "状态", "备注", "Content_JSON"])
    return pd.DataFrame(columns=["样品编号", "创建日期", "状态", "备注", "Content_JSON"])

def save_project_df(project_name, df):
    execute_backup(project_name)
    df.to_csv(get_project_csv(project_name), index=False, encoding='utf-8')

def sanitize_filename(name): return re.sub(r'[\\/*?:"<>|]', "_", name)

def open_folder(path):
    if os.path.exists(path) and os.name == "nt":
        subprocess.Popen(f'explorer "{path}"')
        
def get_module_folder(project_name, sample_id, mod_name):
    sample_f = get_sample_folder(project_name, sample_id)
    mod_f = os.path.join(sample_f, sanitize_filename(mod_name))
    if not os.path.exists(mod_f): os.makedirs(mod_f)
    return mod_f

def rename_sample_logic(project_name, df, old_sid, new_sid):
    if not new_sid: return False, "编号不能为空"
    if new_sid in df["样品编号"].values: return False, "新编号已存在"
    old_folder = get_sample_folder(project_name, old_sid)
    new_folder = os.path.join(get_project_folder(project_name), new_sid)
    try:
        gc.collect(); time.sleep(0.1)
        if os.path.exists(old_folder): shutil.move(old_folder, new_folder)
        df.loc[df["样品编号"] == old_sid, "样品编号"] = new_sid
        save_project_df(project_name, df)
        return True, "成功"
    except Exception as e: return False, f"重命名失败: {e}"

# ================= 2. 侧边栏 =================

with st.sidebar:
    st.title("🧪 SampleManager V3.0")
    all_p = [f.replace(".csv", "") for f in os.listdir(PROJECTS_DIR) if f.endswith(".csv")]
    current_project = st.selectbox("选择项目", sorted(all_p)) if all_p else None

    st.divider()
    with st.expander("📁 项目与备份管理", expanded=False):
        new_p = st.text_input("新建项目名")
        if st.button("➕ 创建项目", use_container_width=True):
            if new_p:
                save_project_df(new_p, pd.DataFrame(columns=["样品编号", "创建日期", "状态", "备注", "Content_JSON"]))
                st.rerun()
        
        if current_project:
            st.markdown(f"**操作项目: `{current_project}`**")
            new_p_name = st.text_input("重命名为:", value=current_project)
            if st.button("📝 确认项目更名", use_container_width=True):
                try:
                    gc.collect(); time.sleep(0.2)
                    shutil.move(get_project_csv(current_project), get_project_csv(new_p_name))
                    if os.path.exists(get_project_folder(current_project)):
                        shutil.move(get_project_folder(current_project), get_project_folder(new_p_name))
                    st.rerun()
                except Exception as e: st.error(f"失败: {e}")
            
            # --- 【恢复】项目物理删除确认 ---
            with st.popover("🗑️ 物理删除该项目", use_container_width=True):
                st.error("警告：此操作不可逆！将删除CSV及物理文件。")
                if st.button("🔥 确认永久删除项目", type="primary", use_container_width=True):
                    try:
                        gc.collect()
                        time.sleep(0.1)
                        if os.path.exists(get_project_csv(current_project)):
                            os.remove(get_project_csv(current_project))
                        if os.path.exists(get_project_folder(current_project)):
                            shutil.rmtree(get_project_folder(current_project))
                        st.rerun()
                    except Exception as e: st.error(f"删除失败: {e}")

    with st.expander("📑 模板预设管理", expanded=False):
        presets = load_presets()
        target_pre = st.selectbox("选择/删除模板", ["--请选择--"] + list(presets.keys()))
        if target_pre != "--请选择--":
            if st.button(f"🗑️ 删除模板 {target_pre}", use_container_width=True):
                del presets[target_pre]; save_presets(presets); st.rerun()
        st.divider()
        n_pre_name = st.text_input("新建模板名")
        n_pre_mods = st.text_area("包含模块 (逗号分隔)")
        if st.button("➕ 保存模板", use_container_width=True):
            if n_pre_name:
                mod_list = [m.strip() for m in n_pre_mods.split(",") if m.strip()]
                presets[n_pre_name] = {m: [] for m in mod_list}
                save_presets(presets); st.rerun()

    if st.button("📂 备份文件夹", use_container_width=True):
        if os.name == 'nt': subprocess.Popen(f'explorer "{BACKUP_DIR}"')

# ================= 3. 主界面 =================

if current_project:
    df = load_project_df(current_project)
    if "edit_id" not in st.session_state: st.session_state["edit_id"] = None

    if st.session_state["edit_id"] is None:
        # --- A. 列表模式 ---
        c1, c2, c3 = st.columns([2, 3, 2])
        with c1:
            presets = load_presets()
            with st.popover("➕ 新建样品", use_container_width=True):
                def get_new_id(p_name, curr_df):
                    i, exist = 1, set(curr_df["样品编号"].values)
                    while f"{p_name}-{i:03d}" in exist: i += 1
                    return f"{p_name}-{i:03d}"
                if st.button("📄 空白样品", use_container_width=True):
                    nid = get_new_id(current_project, df)
                    new_row = {"样品编号": nid, "创建日期": datetime.now().strftime("%Y-%m-%d"), "状态": "制备中", "备注": "", "Content_JSON": "{}"}
                    df = pd.concat([df, pd.DataFrame([new_row])], ignore_index=True)
                    save_project_df(current_project, df); st.session_state["edit_id"] = nid; st.rerun()
                for t in presets:
                    if st.button(f"📑 {t}", use_container_width=True):
                        nid = get_new_id(current_project, df)
                        content = {m: ({f: "" for f in fields} if isinstance(fields, list) else {}) for m, fields in presets[t].items()}
                        df = pd.concat([df, pd.DataFrame([{"样品编号": nid, "创建日期": datetime.now().strftime("%Y-%m-%d"), "状态": "制备中", "备注": "", "Content_JSON": json.dumps(content, ensure_ascii=False)}])], ignore_index=True)
                        save_project_df(current_project, df); st.session_state["edit_id"] = nid; st.rerun()

        with c2: search = st.text_input("🔍 搜索...", label_visibility="collapsed", placeholder="输入编号或备注...")
        
        with c3: 
            sort_opt = st.selectbox("排序方式", ["日期 (新→旧)", "日期 (旧→新)", "编号 (A-Z)", "编号 (Z-A)", "状态"], label_visibility="collapsed")

        st.divider()
        v_df = df if not search else df[df.apply(lambda x: search.lower() in str(x.values).lower(), axis=1)]
        
        if sort_opt == "日期 (新→旧)": v_df = v_df.sort_values(by="创建日期", ascending=False)
        elif sort_opt == "日期 (旧→新)": v_df = v_df.sort_values(by="创建日期", ascending=True)
        elif sort_opt == "编号 (A-Z)": v_df = v_df.sort_values(by="样品编号", ascending=True)
        elif sort_opt == "编号 (Z-A)": v_df = v_df.sort_values(by="样品编号", ascending=False)
        elif sort_opt == "状态": v_df = v_df.sort_values(by="状态")

        for idx, row in v_df.iterrows():
            sid = row["样品编号"]
            with st.container():
                cols = st.columns([2.5, 4, 2.5])
                with cols[0]:
                    if st.button(f"📄 {sid}", key=f"btn_{sid}", use_container_width=True):
                        st.session_state["edit_id"] = sid; st.rerun()
                    stt = row["状态"]
                    color = "orange" if stt == "制备中" else "green" if stt == "完成" else "red"
                    st.markdown(f":{color}[● {stt}] &nbsp; `{row['创建日期']}`")
                with cols[1]:
                    try:
                        modules = json.loads(row["Content_JSON"]).keys()
                        if modules:
                            tags_html = "".join([f'<span class="module-tag">{m}</span>' for m in modules])
                            st.markdown(tags_html, unsafe_allow_html=True)
                    except: pass
                    st.caption(f"备注: {row['备注']}")
                with cols[2]:
                    b1, b2, b3 = st.columns([1, 1, 1])
                    with b1.popover("✏️"):
                        ren_sid = st.text_input("新编号:", value=sid, key=f"ren_l_{sid}")
                        if st.button("确认", key=f"rb_l_{sid}"):
                            ok, msg = rename_sample_logic(current_project, df, sid, ren_sid)
                            if ok: st.rerun()
                            else: st.error(msg)
                    if b2.button("🐑", key=f"cl_{sid}", help="克隆"):
                        new_r = row.copy(); new_r["样品编号"] = get_new_id(current_project, df)
                        df = pd.concat([df, pd.DataFrame([new_r])], ignore_index=True); save_project_df(current_project, df); st.rerun()
                    with b3.popover("🗑️"):
                        st.warning(f"删除 {sid}？")
                        if st.button("确认删除", key=f"conf_del_{sid}", type="primary", use_container_width=True):
                            df = df[df["样品编号"] != sid]; save_project_df(current_project, df)
                            sf = get_sample_folder(current_project, sid)
                            if os.path.exists(sf): shutil.rmtree(sf)
                            st.rerun()
                st.markdown("<hr style='margin:5px 0; opacity:0.1'>", unsafe_allow_html=True)

    else:
        # --- B. 编辑模式 ---
        sid = st.session_state["edit_id"]
        try:
            row_idx = df[df["样品编号"] == sid].index[0]
            cur = df.loc[row_idx]; content_json = json.loads(cur["Content_JSON"])
        except: st.session_state["edit_id"] = None; st.rerun()

        c1, c2, c3 = st.columns([1, 4, 1.5])
        if c1.button("⬅️ 返回", use_container_width=True): st.session_state["edit_id"] = None; st.rerun()
        with c2:
            edit_h = st.columns([3, 1])
            edit_h[0].subheader(f"🛠️ {sid}")
            with edit_h[1].popover("✏️ 重命名"):
                side_ren = st.text_input("新编号:", value=sid, key="side_ren")
                if st.button("确认更名", key="side_ren_btn"):
                    ok, msg = rename_sample_logic(current_project, df, sid, side_ren)
                    if ok: st.session_state["edit_id"] = side_ren; st.rerun()
                    else: st.error(msg)

        fpath = get_sample_folder(current_project, sid)
        if c3.button("📂 总目录", use_container_width=True): open_folder(fpath)

        sc1, sc2, sc3 = st.columns(3)
        n_st = sc1.selectbox("状态", ["制备中", "待测试", "完成", "报废"], index=0)
        n_dt = sc2.text_input("日期", value=cur["创建日期"])
        n_nt = sc3.text_input("备注", value=cur["备注"])

        del_mods = st.multiselect("🔥 选择删除模块", list(content_json.keys()))
        mod_keys = [k for k in content_json.keys() if k not in del_mods]
        
        final_json = {}

        for idx, mod in enumerate(mod_keys):
            params = content_json[mod]
            mod_sub_fpath = get_module_folder(current_project, sid, mod)
            
            with st.container(border=True):
                mh0, mh1, mh2, mh3, mh4 = st.columns([0.5, 3, 1, 2, 2])
                mh0.markdown(f"#### 🧩")
                new_mod_name = mh1.text_input("模块名", value=mod, key=f"mn_{sid}_{mod}", label_visibility="collapsed")
                
                with mh3:
                    bc1, bc2 = st.columns([1, 1])
                    if bc1.button("⬆️", key=f"up_{sid}_{mod}", disabled=(idx == 0)):
                        new_order = mod_keys.copy()
                        new_order[idx], new_order[idx-1] = new_order[idx-1], new_order[idx]
                        reordered_json = {k: content_json[k] for k in new_order}
                        df.at[row_idx, "Content_JSON"] = json.dumps(reordered_json, ensure_ascii=False)
                        save_project_df(current_project, df); st.rerun()
                    if bc2.button("⬇️", key=f"dn_{sid}_{mod}", disabled=(idx == len(mod_keys)-1)):
                        new_order = mod_keys.copy()
                        new_order[idx], new_order[idx+1] = new_order[idx+1], new_order[idx]
                        reordered_json = {k: content_json[k] for k in new_order}
                        df.at[row_idx, "Content_JSON"] = json.dumps(reordered_json, ensure_ascii=False)
                        save_project_df(current_project, df); st.rerun()
               
                if mh4.button("📂 整理", key=f"fold_{sid}_{mod}"): open_folder(mod_sub_fpath)

                updated_p_list = []
                with st.expander("⚙️ 参数列表", expanded=False):
                    for i, (pk, pv) in enumerate(params.items()):
                        pc1, pc2, pc3 = st.columns([2, 3, 1.2])
                        # 核心修改：Key 包含原始 pk 以防错位
                        r_pk = pc1.text_input("名", value=pk, key=f"pk_{sid}_{mod}_{pk}_{i}", label_visibility="collapsed")
                        r_pv = pc2.text_input("值", value=str(pv), key=f"pv_{sid}_{mod}_{pk}_{i}", label_visibility="collapsed")
                        
                        with pc3.popover("🗑️"):
                            st.error("物理删除？")
                            if st.button("确认", key=f"btn_p_del_{sid}_{mod}_{pk}_{i}"):
                                if mod in content_json and pk in content_json[mod]:
                                    del content_json[mod][pk]
                                df.at[row_idx, "Content_JSON"] = json.dumps(content_json, ensure_ascii=False)
                                save_project_df(current_project, df); st.rerun()
                        updated_p_list.append((r_pk, r_pv))
                    
                    st.divider()
                    nc1, nc2 = st.columns([2, 3])
                    add_k = nc1.text_input("新参数", key=f"nk_{sid}_{mod}", label_visibility="collapsed", placeholder="+新名")
                    add_v = nc2.text_input("值", key=f"nv_{sid}_{mod}", label_visibility="collapsed", placeholder="值")
                    if add_k: updated_p_list.append((add_k, add_v))

                final_json[new_mod_name] = {"p_list": updated_p_list, "old_name": mod}
                st.divider()

        nm = st.text_input("➕ 添加新模块")
        if st.button("💾 保存所有修改 (SAVE)", type="primary"):
            for m in del_mods:
                td = os.path.join(fpath, sanitize_filename(m))
                if os.path.exists(td): shutil.rmtree(td)

            df.at[row_idx, "状态"], df.at[row_idx, "创建日期"], df.at[row_idx, "备注"] = n_st, n_dt, n_nt
            
            new_cont_serialized = {}
            for m_new, data in final_json.items():
                m_old = data["old_name"]
                curr_m_dir = get_module_folder(current_project, sid, m_old)
                if m_new != m_old:
                    gc.collect(); time.sleep(0.1)
                    new_m_path = os.path.join(fpath, sanitize_filename(m_new))
                    if os.path.exists(curr_m_dir): shutil.move(curr_m_dir, new_m_path)
                    curr_m_dir = new_m_path
                
                new_cont_serialized[m_new] = {pair[0]: pair[1] for pair in data["p_list"] if pair[0]}
            
            if nm: new_cont_serialized[nm] = {}
            df.at[row_idx, "Content_JSON"] = json.dumps(new_cont_serialized, ensure_ascii=False)
            save_project_df(current_project, df); st.toast("✅ 已保存"); time.sleep(0.5); st.rerun()
else: st.info("👋 请选择项目")