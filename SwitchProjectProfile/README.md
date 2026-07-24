# SwitchProjectProfile - OpenShot Video Editor Plugin

**SwitchProjectProfile** is a plugin for OpenShot Video Editor that automatically detects when imported media (such as **60 FPS** gameplay, **4K** clips, or alternate resolution videos) does not match the active project profile, and prompts the user to switch the project settings to match the video.

---

## 🌟 Key Features

* **Automatic Mismatch Detection:** Compares the frame rate (FPS), width, and height of imported video clips against the current OpenShot project settings.
* **Smart Prompt Modal:** Displays a clean PyQt popup showing the exact differences (e.g. `1920x1080 @ 60.00 FPS` vs `1280x720 @ 30.00 FPS`) and offers a one-click profile switch.
* **Seamless Project Profile Switching:** Integrates directly with OpenShot's native `actionProfile_trigger` to update project FPS, canvas resolution, timeline scaling, and preview player settings.
* **Session Persistence:** Option to "Always Switch for This Session" to automate profile switching during heavy multi-clip editing sessions.

---

## 📁 Repository Structure

```
C:\projects\OpenShot\SwitchProjectProfile\
├── switch_project_profile.py   # Core plugin engine and PyQt dialog
├── __init__.py                  # Package init
├── install_plugin.ps1           # PowerShell automated installer
└── README.md                    # Documentation
```

---

## 🚀 Installation

### Automated Installation (PowerShell)
Open PowerShell and run:
```powershell
powershell -ExecutionPolicy Bypass -File "C:\projects\OpenShot\SwitchProjectProfile\install_plugin.ps1"
```

### Manual Installation
1. Navigate to your user OpenShot folder:
   `C:\Users\<YourUsername>\.openshot_qt\`
2. Create a folder named `plugins` if it does not exist.
3. Copy `switch_project_profile.py` and `__init__.py` into:
   `C:\Users\<YourUsername>\.openshot_qt\plugins\SwitchProjectProfile\`
4. Restart **OpenShot Video Editor**.

---

## 🔍 How It Works

1. Upon startup, `ProfileChecker` registers as an update listener with OpenShot's `UpdateManager`.
2. When a video file is added to the project, the plugin intercepts the file payload and inspects `file.data['fps']`, `file.data['width']`, and `file.data['height']`.
3. If a frame rate or resolution mismatch is detected, a Qt dialog invites you to switch your project profile to match the imported video.
4. Clicking **Switch Profile** invokes `main_window.actionProfile_trigger(file.profile())`, adjusting your project resolution and frame rate seamlessly.
