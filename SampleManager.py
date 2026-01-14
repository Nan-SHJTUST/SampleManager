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
BASE_DIR = "Sample_System_V2"
PROJECTS_DIR = os.path.join(BASE_DIR, "Projects")
BACKUP_DIR = os.path.join(BASE_DIR, "Backups")
CONFIG_FILE = os.path.join(BASE_DIR, "presets.json")

for path in [BASE_DIR, PROJECTS_DIR, BACKUP_DIR]:
    if not os.path.exists(path):
        os.makedirs(path)

st.set_page_config(page_title="SampleManager V2.0", layout="wide", page_icon="🧪")

# === 🎨 CSS ===
st.markdown(
    """
<style>
    :root { --primary-color: #007bff; }
    
    /* 悬浮保存 */
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
    
    .file-zone {
        border-top: 1px solid #eee; margin-top: 10px; padding-top: 10px;
    }
    
    .new-file-alert {
        color: #856404; background-color: #fff3cd; border: 1px solid #ffeeba;
        padding: 5px 10px; border-radius: 4px; margin-bottom: 5px; font-size: 0.9em;
    }
</style>
""",
    unsafe_allow_html=True,
)

# ================= 1. 核心逻辑 =================

# --- 【新增】备份核心函数 ---
def execute_backup(project_name):
    """执行项目CSV文件的备份"""
    src = get_project_csv(project_name)
    if os.path.exists(src):
        date_str = datetime.now().strftime("%Y-%m-%d")
        # 备份格式：项目名_日期.csv
        dst = os.path.join(BACKUP_DIR, f"{project_name}_{date_str}.csv")
        try:
            # 使用 copy2 保留元数据
            shutil.copy2(src, dst)
        except Exception as e:
            print(f"备份失败: {e}")

def load_presets():
    if not os.path.exists(CONFIG_FILE):
        defaults = {
            "PLD_Thin_Film": {
                "Deposition": ["Laser_Energy", "Oxygen_Pressure"],
                "XRD_Test": ["Scan_Range"],
            },
            "Ceramic_Sintering": {
                "Pressing": ["Pressure"],
                "Sintering": ["Temperature"],
            },
        }
        with open(CONFIG_FILE, "w", encoding="utf-8") as f:
            json.dump(defaults, f, ensure_ascii=False, indent=4)
    try:
        with open(CONFIG_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except:
        return {}


def get_project_csv(project_name):
    return os.path.join(PROJECTS_DIR, f"{project_name}.csv")


def get_project_folder(project_name):
    path = os.path.join(PROJECTS_DIR, project_name + "_Files")
    if not os.path.exists(path):
        os.makedirs(path)
    return path


def get_sample_folder(project_name, sample_id):
    path = os.path.join(get_project_folder(project_name), sample_id)
    if not os.path.exists(path):
        os.makedirs(path)
    return path


def load_project_df(project_name):
    # 【修改】加载项目时自动备份
    execute_backup(project_name)
    
    src = get_project_csv(project_name)
    if os.path.exists(src):
        try:
            with open(src, 'r', encoding='utf-8') as f:
                df = pd.read_csv(f)
            
            if "Content_JSON" not in df.columns: 
                df["Content_JSON"] = "{}"
            df = df.fillna("").astype(str)
            return df
        except Exception as e:
            st.error(f"读取数据失败: {e}")
            return pd.DataFrame(columns=["样品编号", "创建日期", "状态", "备注", "Content_JSON"])
    return pd.DataFrame(columns=["样品编号", "创建日期", "状态", "备注", "Content_JSON"])


def save_project_df(project_name, df):
    # 【修改】保存前备份旧版本，以防写入失败
    execute_backup(project_name)
    path = get_project_csv(project_name)
    df.to_csv(path, index=False)


def open_local_file(filepath):
    if os.path.exists(filepath):
        if os.name == "nt":
            try:
                os.startfile(filepath)
            except Exception as e:
                st.error(f"无法打开: {e}")
    else:
        st.error("文件不存在")


def open_folder(path):
    if os.path.exists(path) and os.name == "nt":
        subprocess.Popen(f'explorer "{path}"')


def sanitize_filename(name):
    return re.sub(r'[\\/*?:"<>|]', "_", name)


def scan_folder_files(folder_path):
    if not os.path.exists(folder_path):
        return {}, []
    all_files = [
        f
        for f in os.listdir(folder_path)
        if os.path.isfile(os.path.join(folder_path, f))
    ]
    linked = {}
    unlinked = []
    pattern = re.compile(r"^\[(.*?)\]--(.*)")
    for f in all_files:
        match = pattern.match(f)
        if match:
            mod_name = match.group(1)
            real_name = match.group(2)
            if mod_name not in linked:
                linked[mod_name] = []
            linked[mod_name].append({"real_name": real_name, "full_name": f})
        else:
            if not f.startswith("~$") and f != "Thumbs.db":
                unlinked.append(f)
    return linked, unlinked


# --- CRUD ---
def create_sample(project_name, df, template_data=None):
    i = 1
    existing = set(df["样品编号"].values)
    while True:
        new_id = f"{project_name}-{i:03d}"
        if new_id not in existing:
            break
        i += 1
    content = {}
    if template_data:
        for mod, fields in template_data.items():
            content[mod] = {f: "" for f in fields}
    new_row = {
        "样品编号": new_id,
        "创建日期": datetime.now().strftime("%Y-%m-%d"),
        "状态": "制备中",
        "备注": "",
        "Content_JSON": json.dumps(content, ensure_ascii=False),
    }
    df = pd.concat([df, pd.DataFrame([new_row])], ignore_index=True)
    save_project_df(project_name, df)
    get_sample_folder(project_name, new_id)
    return new_id


def clone_sample(project_name, df, src_id):
    src = df[df["样品编号"] == src_id]
    if src.empty:
        return
    i = 1
    existing = set(df["样品编号"].values)
    while True:
        new_id = f"{project_name}-{i:03d}"
        if new_id not in existing:
            break
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
    # 【新增】删除关键样品前备份CSV
    execute_backup(project_name)
    df = df[df["样品编号"] != sid]
    save_project_df(project_name, df)
    f = get_sample_folder(project_name, sid)
    if os.path.exists(f):
        # 文件夹重命名备份而非物理删除
        try:
            os.rename(f, f + "_del_" + datetime.now().strftime("%H%M%S"))
        except:
            pass
    return df


def rename_sample(project_name, df, old_id, new_id):
    if new_id in df["样品编号"].values:
        return False, "编号已存在"
    old_f = get_sample_folder(project_name, old_id)
    new_f = os.path.join(PROJECTS_DIR, project_name + "_Files", new_id)
    try:
        if os.path.exists(old_f):
            os.rename(old_f, new_f)
    except:
        return False, "文件夹占用"
    idx = df[df["样品编号"] == old_id].index[0]
    df.at[idx, "样品编号"] = new_id
    save_project_df(project_name, df)
    return True, "成功"


# ================= 2. 主界面 =================

with st.sidebar:
    st.title("🧪 SampleManager V2.0")
    
    projects = sorted([f.replace(".csv", "") for f in os.listdir(PROJECTS_DIR) if f.endswith(".csv")])
    current_project = st.selectbox("选择项目", projects) if projects else None

    st.divider()
    
    with st.expander("📁 项目与文件管理", expanded=True):
        new_p = st.text_input("新建项目名")
        if st.button("➕ 创建项目", use_container_width=True):
            if new_p:
                save_project_df(new_p, pd.DataFrame(columns=["样品编号", "创建日期", "状态", "备注", "Content_JSON"]))
                st.rerun()

        if current_project:
            st.markdown(f"**管理项目: `{current_project}`**")
            
            # 重命名逻辑
            new_p_name = st.text_input("重命名项目:", value=current_project)
            if st.button("📝 执行重命名", use_container_width=True):
                if new_p_name and new_p_name != current_project:
                    # 【新增】结构调整前强制备份
                    execute_backup(current_project)
                    old_csv, new_csv = get_project_csv(current_project), get_project_csv(new_p_name)
                    old_fld, new_fld = get_project_folder(current_project), get_project_folder(new_p_name)
                    if os.path.exists(new_csv): st.error("名称已存在")
                    else:
                        try:
                            gc.collect()
                            if os.path.exists(old_fld): shutil.move(old_fld, new_fld)
                            if os.path.exists(old_csv): shutil.move(old_csv, new_csv)
                            st.rerun()
                        except Exception as e: st.error(f"失败: {e}")

            # 删除项目 (带备份逻辑)
            with st.popover("🔥 永久删除项目", use_container_width=True):
                st.error("警告：将删除CSV记录及物理文件！")
                if st.button("确认删除", type="primary", use_container_width=True):
                    try:
                        # 删除前最后备份一次CSV到Backup文件夹
                        execute_backup(current_project)
                        gc.collect()
                        csv_p = get_project_csv(current_project)
                        fld_p = get_project_folder(current_project)
                        if os.path.exists(csv_p): os.remove(csv_p)
                        if os.path.exists(fld_p): shutil.rmtree(fld_p) 
                        st.rerun()
                    except Exception as e: st.error(f"删除失败: {e}")

    # --- 【新增】侧边栏备份管理 ---
    st.divider()
    if st.button("📂 打开备份文件夹", use_container_width=True):
        open_folder(BACKUP_DIR)

if current_project:
    df = load_project_df(current_project)
    if "edit_id" not in st.session_state:
        st.session_state["edit_id"] = None

    # --- A. 列表 ---
    if st.session_state["edit_id"] is None:
        c1, c2 = st.columns([2, 3])
        with c1:
            presets = load_presets()
            with st.popover("➕ 新建样品", use_container_width=True):
                if st.button("📄 空白样品", use_container_width=True):
                    nid = create_sample(current_project, df, None)
                    st.session_state["edit_id"] = nid
                    st.rerun()
                for t in presets:
                    if st.button(f"📑 {t}", use_container_width=True):
                        nid = create_sample(current_project, df, presets[t])
                        st.session_state["edit_id"] = nid
                        st.rerun()
        with c2:
            search = st.text_input(
                "Search", label_visibility="collapsed", placeholder="搜索..."
            )
        st.divider()
        view_df = df
        if search:
            view_df = df[df.apply(lambda x: str(x.values).find(search) != -1, axis=1)]

        for idx, row in view_df.iloc[::-1].iterrows():
            sid = row["样品编号"]
            with st.container():
                cols = st.columns([0.5, 3, 2, 2])
                cols[0].checkbox("", key=f"c_{sid}", label_visibility="collapsed")
                with cols[1]:
                    if st.button(
                        f"📄 {sid}", key=f"btn_{sid}", use_container_width=True
                    ):
                        st.session_state["edit_id"] = sid
                        st.rerun()
                    st.caption(f"{str(row['备注'])[:20]}")
                with cols[2]:
                    stt = row["状态"]
                    col = (
                        "orange"
                        if stt == "制备中"
                        else "green" if stt == "完成" else "blue"
                    )
                    st.markdown(f":{col}[● {stt}] &nbsp; {row['创建日期']}")
                with cols[3]:
                    b1, b2, b3 = st.columns(3)
                    with b1.popover("✏️"):
                        nn = st.text_input("新ID", value=sid, key=f"rn_{sid}")
                        if st.button("确认", key=f"rnb_{sid}"):
                            ok, msg = rename_sample(current_project, df, sid, nn)
                            if ok:
                                st.rerun()
                    if b2.button("🐑", key=f"cl_{sid}"):
                        clone_sample(current_project, df, sid)
                        st.rerun()
                    if b3.button("🗑️", key=f"dl_{sid}", type="secondary"):
                        delete_sample(current_project, df, sid)
                        st.rerun()
                st.markdown("<hr style='margin:5px 0'>", unsafe_allow_html=True)

    # --- B. 编辑 ---
    else:
        sid = st.session_state["edit_id"]
        try:
            row_idx = df[df["样品编号"] == sid].index[0]
            cur = df.loc[row_idx]
            content_json = json.loads(cur["Content_JSON"])
        except:
            st.session_state["edit_id"] = None
            st.rerun()

        c1, c2, c3 = st.columns([1, 4, 1.5])
        if c1.button("⬅️ 返回列表", use_container_width=True):
            st.session_state["edit_id"] = None
            st.rerun()
        c2.markdown(f"### 🛠️ {sid}")
        folder = get_sample_folder(current_project, sid)
        if c3.button("📂 打开总文件夹", use_container_width=True):
            open_folder(folder)
        st.markdown("---")

        sc1, sc2, sc3 = st.columns(3)
        sts = ["制备中", "待测试", "完成", "报废"]
        n_st = sc1.selectbox(
            "状态", sts, index=sts.index(cur["状态"]) if cur["状态"] in sts else 0
        )
        n_dt = sc2.text_input("日期", value=str(cur["创建日期"]))
        n_nt = sc3.text_input("备注", value=str(cur["备注"]))

        linked_files, unlinked_files = scan_folder_files(folder)

        st.markdown("#### 🧬 实验参数与数据")

        modules_list = list(content_json.keys())
        deleted_modules = []
        if modules_list:
            deleted_modules = st.multiselect(
                "🗑️ 选择要删除的模块", modules_list, placeholder="如不再需要，请勾选..."
            )

        final_content = {}

        for mod_name, params in content_json.items():
            if mod_name in deleted_modules:
                continue

            with st.container():
                mh1, mh2 = st.columns([5, 1])
                mh1.markdown(f"#### 🔹 {mod_name}")
                if mh2.button("📂 整理", key=f"fo_{mod_name}", help="打开文件夹"):
                    open_folder(folder)

                with st.expander("⚙️ 参数管理", expanded=False):
                    mc1, mc2 = st.columns([3, 1])
                    npk = mc1.text_input(
                        "名",
                        placeholder="+参数",
                        key=f"npk_{mod_name}",
                        label_visibility="collapsed",
                    )
                    npv = mc2.text_input(
                        "值",
                        placeholder="值",
                        key=f"npv_{mod_name}",
                        label_visibility="collapsed",
                    )
                    dk = st.multiselect(
                        "删除参数", list(params.keys()), key=f"dk_{mod_name}"
                    )

                curr_params = params.copy()
                if npk:
                    curr_params[npk] = npv

                valid_params = {}
                p_cols = st.columns(3)
                idx = 0
                for k, v in curr_params.items():
                    if k not in dk:
                        with p_cols[idx % 3]:
                            valid_params[k] = st.text_input(
                                k,
                                value=str(v) if v else "",
                                key=f"v_{sid}_{mod_name}_{k}",
                            )
                        idx += 1

                st.markdown('<div class="file-zone">', unsafe_allow_html=True)
                fc1, fc2 = st.columns([3, 2])

                with fc1:
                    my_files = linked_files.get(mod_name, [])
                    count_text = (
                        f"📎 已关联 ({len(my_files)})" if my_files else "📎 无关联文件"
                    )
                    with st.expander(count_text, expanded=False):
                        if my_files:
                            for f_info in my_files:
                                fname = f_info["real_name"]
                                fpath = os.path.join(folder, f_info["full_name"])
                                fr1, fr2 = st.columns([4, 1])
                                fr1.caption(f"📄 {fname}")
                                if fr2.button("🚀", key=f"op_{f_info['full_name']}"):
                                    open_local_file(fpath)
                        else:
                            st.caption("暂无")

                with fc2:
                    if unlinked_files:
                        st.markdown(
                            f"<div class='new-file-alert'>🔍 发现 {len(unlinked_files)} 个新文件!</div>",
                            unsafe_allow_html=True,
                        )
                        to_link = st.multiselect(
                            "认领文件",
                            unlinked_files,
                            key=f"lnk_{mod_name}",
                            label_visibility="collapsed",
                            placeholder="🔍 勾选认领...",
                        )
                    else:
                        to_link = []

                    up = st.file_uploader(
                        "上传",
                        key=f"u_{mod_name}",
                        label_visibility="collapsed",
                        accept_multiple_files=True,
                    )

                final_content[mod_name] = {
                    "params": valid_params,
                    "link_files": to_link,
                    "new_uploads": up,
                }
                st.markdown("---")

        nm = st.text_input("➕ 添加新模块", placeholder="输入名称...")

        st.markdown("<br><br><br>", unsafe_allow_html=True)
        if st.button("💾 保存所有修改 (Save)", type="primary"):
            df.at[row_idx, "状态"] = n_st
            df.at[row_idx, "创建日期"] = n_dt
            df.at[row_idx, "备注"] = n_nt

            clean = {}
            if nm:
                clean[nm] = {}
            for m_name, m_data in final_content.items():
                clean[m_name] = m_data["params"]
                prefix = f"[{sanitize_filename(m_name)}]--"

                for raw_f in m_data["link_files"]:
                    try:
                        os.rename(
                            os.path.join(folder, raw_f),
                            os.path.join(folder, prefix + raw_f),
                        )
                    except:
                        pass

                if m_data["new_uploads"]:
                    for uf in m_data["new_uploads"]:
                        try:
                            with open(
                                os.path.join(
                                    folder, prefix + sanitize_filename(uf.name)
                                ),
                                "wb",
                            ) as f:
                                f.write(uf.getbuffer())
                        except:
                            pass

            df.at[row_idx, "Content_JSON"] = json.dumps(clean, ensure_ascii=False)
            save_project_df(current_project, df)
            st.toast("✅ 已保存并备份！")
            time.sleep(0.5)
            st.rerun()

else:
    st.info("请新建项目")