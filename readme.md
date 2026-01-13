# 🧪 SampleManager | 科研样品数据管理系统

> **A Lightweight, Visualized Data Management System for Material Scientists.**  
> **专为材料/化学领域科研人员设计的轻量级、可视化实验数据管理工具。**

![Python](https://img.shields.io/badge/Python-3.8%2B-blue) ![Streamlit](https://img.shields.io/badge/Streamlit-App-FF4B4B) ![Status](https://img.shields.io/badge/Status-Stable-green)

---

## 📖 Introduction (简介)

**SampleManager** is a local-first data management tool designed to solve the "Excel Hell" and "File Chaos" problems in scientific research. It helps researchers track sample history, manage process parameters, and link raw data files directly.

**SampleManager** 是一个“本地优先”的数据管理工具，旨在解决科研过程中“Excel表格爆炸”和“数据文件混乱”的痛点。它可以帮助研究人员追踪样品历史、管理工艺参数，并实现原始数据文件的直接关联与调阅。

### 🚀 Key Features (核心功能)

*   **🗂️ Card-View Dashboard (卡片式看板)**: Visualize sample status (Preparing/Testing/Finished) at a glance.
    *   *可视化展示样品状态（制备中/测试中/完成），告别枯燥的表格。*
*   **🚀 Direct File Launch (文件一键直连)**: Click the button in the app to open raw data files (e.g., `.csv`, `.dat`, `.opju`) directly with your local software. No need to download.
    *   *在网页端点击按钮，直接唤醒本地软件打开数据文件（如 Excel, Jade, ZView），无需下载。*
*   **🛠️ Dynamic Templates (动态模版)**: Free to customize experiment templates. You can add/delete parameters for any specific sample without affecting others.
    *   *拒绝死板模版，支持随时为特定样品增删实验参数，实现“千人千面”的管理。*
*   **🐑 One-Click Clone (一键克隆)**: Duplicate an existing sample's parameters to create a new one instantly. Perfect for batch experiments.
    *   *快速复制旧样品参数，仅需修改差异项，极大提升系列样品的录入效率。*
*   **🛡️ Auto Backup (自动备份)**: Data is stored locally in CSV format with automatic daily backups. Safe and private.
    *   *数据本地 CSV 存储，支持每日自动备份，配合网盘（如 OneDrive/Dropbox）可实现云同步。*

---

## 🛠️ Installation (安装指南)

### Prerequisites (前置要求)
*   Python 3.8 or higher installed.
*   Windows OS (Recommended for full file-linking features).

### Steps (步骤)

1. **Clone the repository (克隆仓库)**

   ```bash
   git clone https://github.com/Nan-SHJTUST/SampleManager.git
   cd SampleManager
   ···

2.  **Install dependencies (安装依赖)**
    ```bash
    pip install -r requirements.txt
    ```

3.  **Run the App (运行系统)**
    *   **Method A**: Double-click `run.bat` (Recommended for Windows).
    *   **Method B**: Run command in terminal:
        ```bash
        streamlit run SampleManager.py
        ```

---

## 🧪 Usage (使用说明)

1.  **Create Project**: Create a new project (e.g., `Solid_State_Battery_2026`) in the sidebar.
2.  **New Sample**: Click `+ New Sample`. You can start blank or use a preset template.
3.  **Edit & File Management**:
    *   Enter parameters in the input fields.
    *   Drag & drop experimental files (XRD, SEM, EIS) into the upload area.
    *   Click `🚀 Open` to view files instantly.
4.  **Save**: Click the **Floating Blue Button** at the bottom right to save changes.

---

## ⚙️ Default Templates (预设模版)

The system creates a `presets.json` on the first run. You can modify it in the "Template Manager" sidebar.  
系统首次运行会自动生成预设模版，您可以在侧边栏的“模版管理”中修改。

**Example Structure (English):**

```json
{
    "PLD_Thin_Film_Process": {
        "1.Deposition_Params": ["Laser_Energy(mJ)", "Frequency(Hz)", "Temperature(C)", "Oxygen_Pressure(Pa)", "Time(min)"],
        "2.Post_Annealing": ["Temperature(C)", "Atmosphere", "Duration(h)"],
        "3.Characterization": ["XRD_Range", "Thickness(nm)", "Conductivity(S/cm)"]
    },
    "Ceramic_Sintering_Process": {
        "1.Pressing": ["Pressure(MPa)", "Holding_Time(min)"],
        "2.Sintering": ["Temperature(C)", "Heating_Rate(C/min)", "Dwell_Time(h)"],
        "3.EIS_Test": ["Test_Temp(C)", "Frequency_Range"]
    }
}
```

## Contributing & License
Author: [Catcher@SHJTUST]
License: MIT License
Note: This project was architected by a domain researcher and implemented with the assistance of AI coding tools. It is optimized for real-world laboratory workflows.

注：本项目由一线科研人员设计架构，并由 AI 辅助开发实现，逻辑流针对真实实验室场景进行了深度优化。

