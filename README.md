# OpenShot Plugins Collection

A centralized collection of custom plugins for [OpenShot Video Editor](https://www.openshot.org/).

---

## 📦 Included Plugins

### 1. 🎬 [SwitchProjectProfile](./SwitchProjectProfile)
Automatically detects when imported media (such as 60 FPS gameplay, 4K clips, or alternate resolution videos) does not match the active project profile, and prompts the user to switch the project settings to match the video.

* **Key Features:**
  * **Kdenlive-Style Smart Prompting:** Prompts on the **first video imported** into a project session to set your project baseline without annoying repetitive popups for secondary clips.
  * **Automatic Mismatch Detection:** Compares frame rate (FPS), width, and height of imported video clips against active OpenShot project settings.
  * **Timeline Safety Warning:** Automatically warns you if clips already exist on the timeline before changing profiles mid-edit.
  * **Seamless Profile Switch:** Updates canvas resolution, timeline scaling, FPS, and preview player settings instantly via OpenShot's native mechanisms.
  * **Session Persistence:** Option to select "Always Switch for This Session" to streamline multi-clip editing.

### 2. 📤 [MatchExportProfile](./MatchExportProfile)
Hooks into OpenShot's **Export Video** window (`Ctrl+E`). Whenever you open the rendering window, it automatically selects OpenShot's matching official profile format (e.g., `FHD 1080p 60 fps`), container target (`MP4 h.264`), and High Quality preset to match your active Project Profile without requiring manual dropdown adjustments.

> 💡 **Note on How It Works:** Rather than inserting a duplicate custom menu entry into the dropdown, `MatchExportProfile` automatically identifies and **pre-selects the exact official OpenShot profile** (`FHD 1080p 60 fps`, `4K UHD 60 fps`, etc.) corresponding to your project. This guarantees 100% native FFmpeg rendering stability, hardware acceleration (NVENC/VAAPI/CPU), and audio encoder compatibility out-of-the-box.

* **Key Features:**
  * **Auto Profile Selection:** Automatically selects OpenShot's matching official profile format (`1080p 60fps`, `4K 60fps`, etc.) matching your project settings.
  * **Pre-Selected Quality & Target:** Defaults to `MP4 (h.264 / aac)` container and `High Quality` preset automatically.
  * **Native FFmpeg Compatibility:** Utilizes OpenShot's official built-in profile definitions for max rendering stability.

### 3. 🔌 [PluginViewer](./PluginViewer)
Adds a clean **Installed Plug-ins** action under OpenShot's **Help** menu (**Help $\rightarrow$ 🔌 Installed Plug-ins**) to view the status and description of all currently installed custom plugins.

* **Key Features:**
  * **Help Menu Integration:** Access plugin status anytime via OpenShot's native Help menu.
  * **Clean Plugin Summary:** Displays active plugin titles, statuses, and feature summaries in a polished popup.

---

## 📁 Repository Structure

```
OpenShot_Plugins/
├── SwitchProjectProfile/         # Switch Project Profile plugin
│   ├── switch_project_profile.py # Core plugin engine and PyQt dialog
│   ├── __init__.py                # Package init
│   └── install_plugin.ps1         # PowerShell automated installer
├── MatchExportProfile/           # Match Export Profile plugin
│   ├── match_export_profile.py  # Core export auto-selection engine
│   ├── __init__.py                # Package init
│   ├── install_plugin.ps1         # PowerShell automated installer
│   └── README.md                  # Plugin documentation
├── PluginViewer/                 # Installed Plug-ins viewer
│   ├── plugin_viewer.py         # Help menu popout dialog
│   ├── __init__.py                # Package init
│   ├── install_plugin.ps1         # PowerShell automated installer
│   └── README.md                  # Plugin documentation
├── LICENSE                        # MIT License
└── README.md                      # Repository documentation overview
```

---

## 🚀 Installation

### Automated Installation (Windows / PowerShell)

Run the installer scripts for the plugins directly from the repository root:

```powershell
# Install SwitchProjectProfile
powershell -ExecutionPolicy Bypass -File ".\SwitchProjectProfile\install_plugin.ps1"

# Install MatchExportProfile
powershell -ExecutionPolicy Bypass -File ".\MatchExportProfile\install_plugin.ps1"
```

### Manual Installation

1. Open your user OpenShot configuration folder:
   - **Windows:** `C:\Users\<YourUsername>\.openshot_qt\`
   - **Linux / macOS:** `~/.openshot_qt/`
2. Create a folder named `plugins` if it does not already exist.
3. Copy the desired plugin folder (e.g., `SwitchProjectProfile` or `MatchExportProfile`) into `plugins`:
   `C:\Users\<YourUsername>\.openshot_qt\plugins\`
4. Restart **OpenShot Video Editor**.

---

## 🔍 How `SwitchProjectProfile` & `MatchExportProfile` Work Together

1. **Importing Media:** When you add your main video clip to OpenShot, `SwitchProjectProfile` detects any FPS/resolution mismatch and prompts you to switch your project profile to match (e.g. `FHD 1080p 60 fps`).
2. **Exporting Video:** When you press `Ctrl+E` to render your project, `MatchExportProfile` reads the active project profile and automatically pre-selects the matching official profile format (`FHD 1080p 60 fps (1920x1080)`), `MP4 (h.264)`, and `High Quality` preset in the Export window.
3. **One-Click Render:** You can immediately click **Export Video** without having to manually locate or configure profile dropdowns!

---

## 🤝 Adding New Plugins

This repository is designed to host multiple OpenShot plugins. To add a new plugin:

1. Create a dedicated directory for the plugin at the root of this repo (e.g., `MyNewPlugin/`).
2. Place all plugin implementation files inside that folder.
3. (Optional) Include an `install_plugin.ps1` installer inside the plugin directory.
4. Add an entry and description for your new plugin in this `README.md`.

---

## 📄 License

This project is licensed under the [MIT License](./LICENSE).
