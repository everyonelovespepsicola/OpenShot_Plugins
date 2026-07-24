# MatchExportProfile - OpenShot Video Editor Plugin

**MatchExportProfile** is an OpenShot Video Editor plugin that automatically syncs and pre-selects the Export Video dialog (`Ctrl+E`) settings to match your active Project Profile parameters.

---

## 🌟 How It Works

Rather than adding a duplicate custom menu entry, **MatchExportProfile** automatically identifies and pre-selects OpenShot's **matching official built-in profile** (e.g. `FHD 1080p 60 fps (1920x1080)`), container format (`MP4 h.264`), and `High Quality` preset.

Using OpenShot's official built-in profile definitions guarantees:
* **100% FFmpeg Transcoding Stability**
* **Hardware Acceleration Compatibility (NVENC / VAAPI / CPU)**
* **Zero manual dropdown configuration required prior to rendering**

---

## 🚀 Installation (PowerShell)

```powershell
powershell -ExecutionPolicy Bypass -File "C:\projects\OpenShot_Plugins\MatchExportProfile\install_plugin.ps1"
```
