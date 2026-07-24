# OpenShot Plugins Collection

A centralized collection of custom plugins for [OpenShot Video Editor](https://www.openshot.org/).

---

## 📦 Included Plugins

### 1. 🎬 [SwitchProjectProfile](./SwitchProjectProfile)
Automatically detects when imported media (such as 60 FPS gameplay, 4K clips, or alternate resolution videos) does not match the active project profile, and prompts the user to switch the project settings to match the video.

* **Key Features:**
  * **Automatic Mismatch Detection:** Compares frame rate (FPS), width, and height of imported video clips against active OpenShot project settings.
  * **Smart PyQt Modal:** Displays a clean dialog showing exact profile differences (e.g., `1920x1080 @ 60.00 FPS` vs `1280x720 @ 30.00 FPS`) and provides a one-click profile switch.
  * **Seamless Profile Switch:** Updates canvas resolution, timeline scaling, FPS, and preview player settings instantly via OpenShot's native mechanisms.
  * **Session Persistence:** Option to select "Always Switch for This Session" to streamline multi-clip editing.

---

## 📁 Repository Structure

```
OpenShot_Plugins/
├── SwitchProjectProfile/         # Switch Project Profile plugin
│   ├── switch_project_profile.py # Core plugin engine and PyQt dialog
│   ├── __init__.py                # Package init
│   └── install_plugin.ps1         # PowerShell automated installer
└── README.md                      # Repository documentation overview
```

---

## 🚀 Installation

### Automated Installation (Windows / PowerShell)

Run the installer script for a plugin directly from the repository root:

```powershell
powershell -ExecutionPolicy Bypass -File ".\SwitchProjectProfile\install_plugin.ps1"
```

### Manual Installation

1. Open your user OpenShot configuration folder:
   - **Windows:** `C:\Users\<YourUsername>\.openshot_qt\`
   - **Linux / macOS:** `~/.openshot_qt/`
2. Create a folder named `plugins` if it does not already exist.
3. Copy the desired plugin folder (e.g., `SwitchProjectProfile`) into `plugins`:
   `C:\Users\<YourUsername>\.openshot_qt\plugins\SwitchProjectProfile\`
4. Restart **OpenShot Video Editor**.

---

## 🔍 How `SwitchProjectProfile` Works

1. Upon startup, `ProfileChecker` registers as an update listener with OpenShot's `UpdateManager`.
2. When a video file is added to the project, the plugin intercepts the file payload and inspects `file.data['fps']`, `file.data['width']`, and `file.data['height']`.
3. If a frame rate or resolution mismatch is detected, a Qt dialog invites you to switch your project profile to match the imported video.
4. Clicking **Switch Profile** invokes `main_window.actionProfile_trigger(file.profile())`, adjusting your project resolution and frame rate seamlessly.

---

## 🤝 Adding New Plugins

This repository is designed to host multiple OpenShot plugins. To add a new plugin:

1. Create a dedicated directory for the plugin at the root of this repo (e.g., `MyNewPlugin/`).
2. Place all plugin implementation files inside that folder.
3. (Optional) Include an `install_plugin.ps1` installer inside the plugin directory.
4. Add an entry and description for your new plugin in this `README.md`.
