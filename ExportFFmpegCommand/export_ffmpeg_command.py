"""
ExportFFmpegCommand - OpenShot Video Editor Plugin

Generates and extracts the exact, complete FFmpeg command line string
corresponding to your export dialog settings or active project specifications.
Copies the ready-to-run FFmpeg string straight to your clipboard.

Author: Antigravity AI
License: MIT
"""

import os
import sys
import logging

try:
    from PyQt5.QtCore import QObject, QTimer, Qt
    from PyQt5.QtWidgets import (
        QApplication, QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QTextEdit, QMessageBox
    )
    from PyQt5.QtGui import QFont
    PYQT_AVAILABLE = True
except ImportError:
    try:
        from PyQt6.QtCore import QObject, QTimer, Qt
        from PyQt6.QtWidgets import (
            QApplication, QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QTextEdit, QMessageBox
        )
        from PyQt6.QtGui import QFont
        PYQT_AVAILABLE = True
    except ImportError:
        PYQT_AVAILABLE = False

try:
    from classes.app import get_app
    from classes.logger import log
    OPENSHOT_AVAILABLE = True
except ImportError:
    OPENSHOT_AVAILABLE = False
    log = logging.getLogger("ExportFFmpegCommand")


class FFmpegCommandWindow(QDialog if PYQT_AVAILABLE else object):
    """PyQt window displaying interactive FFmpeg CLI command string generator."""

    def __init__(self, parent=None, clips=None, files_map=None, initial_params=None, builder_func=None):
        if PYQT_AVAILABLE:
            super().__init__(parent)
            self.setWindowTitle("📋 Interactive FFmpeg Command Generator")
            self.resize(780, 440)
            self.clips = clips or []
            self.files_map = files_map or {}
            self.initial_params = initial_params or {}
            self.builder_func = builder_func
            self.setup_ui()

    def setup_ui(self):
        from PyQt5.QtWidgets import QComboBox, QFormLayout, QGroupBox, QCheckBox
        layout = QVBoxLayout(self)

        header = QLabel("<h3>📋 Interactive FFmpeg Command Generator</h3>"
                        "<p>Adjust Target Format, Video Profile, and Quality below to update your standalone FFmpeg command live:</p>")
        layout.addWidget(header)

        # Dropdowns Group Box
        group = QGroupBox("FFmpeg Preset Controls")
        grp_layout = QHBoxLayout(group)

        # 1. Target Format
        v_box_target = QVBoxLayout()
        v_box_target.addWidget(QLabel("Target Format:"))
        self.cbo_target = QComboBox()
        self.cbo_target.addItem("MP4 (h.264 / aac)", {"vcodec": "libx264", "acodec": "aac", "ext": "mp4"})
        self.cbo_target.addItem("MKV (hevc / ac3)", {"vcodec": "libx265", "acodec": "ac3", "ext": "mkv"})
        self.cbo_target.addItem("WEBM (vp9 / opus)", {"vcodec": "libvpx-vp9", "acodec": "libopus", "ext": "webm"})
        self.cbo_target.addItem("AVI (mpeg4 / mp3)", {"vcodec": "mpeg4", "acodec": "libmp3lame", "ext": "avi"})
        self.cbo_target.addItem("MOV (h.264 / pcm)", {"vcodec": "libx264", "acodec": "pcm_s16le", "ext": "mov"})
        self.cbo_target.currentIndexChanged.connect(self.update_command)
        v_box_target.addWidget(self.cbo_target)
        grp_layout.addLayout(v_box_target)

        # 2. Video Profile
        v_box_profile = QVBoxLayout()
        v_box_profile.addWidget(QLabel("Video Profile:"))
        self.cbo_profile = QComboBox()
        self.cbo_profile.addItem("FHD 1080p 60 fps (1920x1080)", {"width": 1920, "height": 1080, "fps": 60.0})
        self.cbo_profile.addItem("FHD 1080p 30 fps (1920x1080)", {"width": 1920, "height": 1080, "fps": 30.0})
        self.cbo_profile.addItem("4K UHD 60 fps (3840x2160)", {"width": 3840, "height": 2160, "fps": 60.0})
        self.cbo_profile.addItem("4K UHD 30 fps (3840x2160)", {"width": 3840, "height": 2160, "fps": 30.0})
        self.cbo_profile.addItem("HD 720p 60 fps (1280x720)", {"width": 1280, "height": 720, "fps": 60.0})
        self.cbo_profile.addItem("HD 720p 30 fps (1280x720)", {"width": 1280, "height": 720, "fps": 30.0})
        self.cbo_profile.currentIndexChanged.connect(self.update_command)
        v_box_profile.addWidget(self.cbo_profile)
        grp_layout.addLayout(v_box_profile)

        # 3. Quality Preset
        v_box_quality = QVBoxLayout()
        v_box_quality.addWidget(QLabel("Quality Preset:"))
        self.cbo_quality = QComboBox()
        self.cbo_quality.addItem("High Quality (15 Mb/s)", "-b:v 15M")
        self.cbo_quality.addItem("Medium Quality (8 Mb/s)", "-b:v 8M")
        self.cbo_quality.addItem("Low Quality (3 Mb/s)", "-b:v 3M")
        self.cbo_quality.addItem("Lossless / Archival (CRF 18)", "-crf 18")
        self.cbo_quality.currentIndexChanged.connect(self.update_command)
        v_box_quality.addWidget(self.cbo_quality)
        grp_layout.addLayout(v_box_quality)

        layout.addWidget(group)

        # Hardware Acceleration Checkbox (Default: Unchecked)
        self.chk_hwaccel = QCheckBox("⚡ Enable Hardware Acceleration (GPU / NVENC)")
        self.chk_hwaccel.setChecked(False)
        self.chk_hwaccel.toggled.connect(self.update_command)
        layout.addWidget(self.chk_hwaccel)

        # Command Text Box
        self.txt_cmd = QTextEdit()
        self.txt_cmd.setFont(QFont("Consolas", 10))
        layout.addWidget(self.txt_cmd)

        # Action Buttons
        btn_layout = QHBoxLayout()

        btn_copy = QPushButton("📋 Copy Command to Clipboard")
        btn_copy.setStyleSheet("font-weight: bold; background-color: #0275d8; color: white; padding: 8px;")
        btn_copy.clicked.connect(self.copy_to_clipboard)
        btn_layout.addWidget(btn_copy)

        btn_close = QPushButton("Close")
        btn_close.clicked.connect(self.close)
        btn_layout.addWidget(btn_close)

        layout.addLayout(btn_layout)

        self.update_command()

    def update_command(self):
        """Regenerate FFmpeg command string based on active dropdown selections."""
        if not self.builder_func:
            return

        target_data = self.cbo_target.currentData() or {}
        profile_data = self.cbo_profile.currentData() or {}
        quality_data = self.cbo_quality.currentData() or "-b:v 15M"

        v_codec = target_data.get("vcodec", "libx264")
        a_codec = target_data.get("acodec", "aac")
        ext = target_data.get("ext", "mp4")

        hw_enabled = self.chk_hwaccel.isChecked() if hasattr(self, "chk_hwaccel") else False
        if hw_enabled:
            if v_codec == "libx265":
                v_codec = "hevc_nvenc"
            else:
                v_codec = "h264_nvenc"

        width = profile_data.get("width", 1920)
        height = profile_data.get("height", 1080)
        fps = profile_data.get("fps", 60.0)

        out_folder = os.path.expanduser(r"~\Desktop")
        out_file = os.path.join(out_folder, f"output.{ext}")

        cmd_str = self.builder_func(
            self.clips, self.files_map, v_codec, quality_data, fps, width, height,
            a_codec, "160k", 48000, 2, out_file, hw_accel=hw_enabled
        )

        self.txt_cmd.setText(cmd_str)

    def copy_to_clipboard(self):
        """Copy generated string to Windows Clipboard."""
        clipboard = QApplication.clipboard()
        clipboard.setText(self.txt_cmd.toPlainText())
        QMessageBox.information(self, "Copied", "FFmpeg command line copied to clipboard!")


class ExportFFmpegCommand(QObject if PYQT_AVAILABLE else object):
    """Main plugin object registered with OpenShot."""

    def __init__(self):
        if PYQT_AVAILABLE:
            super().__init__()

    def initialize(self):
        if not OPENSHOT_AVAILABLE:
            return

        try:
            app = get_app()
            window = getattr(app, "window", None)
            if window and PYQT_AVAILABLE:
                self.add_tools_menu_item(window)
                self.hook_export_dialog(window)
                log.info("ExportFFmpegCommand plugin initialized.")
        except Exception as ex:
            log.warning(f"ExportFFmpegCommand init warning: {ex}")

    def add_tools_menu_item(self, window):
        """Add action to top-level Tools menu (positioned before Help)."""
        try:
            menu_bar = window.menuBar()
            if not menu_bar:
                return

            help_action = None
            tools_menu = None

            for action in menu_bar.actions():
                txt = action.text().lower().strip("& ")
                if txt in ("tools", "tool", "herramientas"):
                    tools_menu = action.menu()
                    break
                elif txt in ("help", "ayuda"):
                    help_action = action

            if not tools_menu:
                from PyQt5.QtWidgets import QMenu
                tools_menu = QMenu("&Tools", window)
                if help_action:
                    menu_bar.insertMenu(help_action, tools_menu)
                else:
                    menu_bar.addMenu(tools_menu)

            # Prevent duplicate actions
            for action in tools_menu.actions():
                if "ffmpeg" in action.text().lower():
                    return

            cmd_action = tools_menu.addAction("📋 Copy FFmpeg Command...")
            cmd_action.triggered.connect(self.generate_and_show_command)
            log.info("ExportFFmpegCommand added '📋 Copy FFmpeg Command...' action to Tools menu.")
        except Exception as ex:
            log.warning(f"ExportFFmpegCommand failed to add menu item: {ex}")

    def hook_export_dialog(self, window):
        """Hook into Export Video dialog trigger to insert a 'Copy FFmpeg Command' button."""
        try:
            if hasattr(window, "actionExportVideo_trigger"):
                if not hasattr(window, "_orig_export_trigger_cmd"):
                    orig_export = window.actionExportVideo_trigger
                    window._orig_export_trigger_cmd = orig_export

                    def wrapped_export_trigger(*args, **kwargs):
                        res = orig_export(*args, **kwargs)
                        if PYQT_AVAILABLE:
                            QTimer.singleShot(250, self.inject_export_dialog_button)
                        return res

                    window.actionExportVideo_trigger = wrapped_export_trigger
                    log.info("ExportFFmpegCommand hooked into actionExportVideo_trigger.")
        except Exception as ex:
            log.warning(f"ExportFFmpegCommand hook error: {ex}")

    def inject_export_dialog_button(self):
        """Inject '📋 Copy FFmpeg Command' button into active Export QDialog."""
        try:
            top_widgets = QApplication.topLevelWidgets()
            export_dialog = None
            for w in top_widgets:
                if isinstance(w, QDialog) or "Export" in w.__class__.__name__:
                    if hasattr(w, "cboSimpleVideoProfile") or hasattr(w, "cboProfile") or hasattr(w, "txtFileName"):
                        export_dialog = w
                        break

            if not export_dialog or hasattr(export_dialog, "_ffmpeg_btn_injected"):
                return

            export_dialog._ffmpeg_btn_injected = True

            # Find action button layout in Export dialog
            btn_box = export_dialog.findChild(QHBoxLayout)
            if not btn_box:
                # Search bottom layouts
                layouts = export_dialog.findChildren(QHBoxLayout)
                if layouts:
                    btn_box = layouts[-1]

            if btn_box:
                btn_copy_cmd = QPushButton("📋 Copy FFmpeg Command")
                btn_copy_cmd.setStyleSheet("font-weight: bold; background-color: #20c997; color: white; padding: 5px 10px;")
                btn_copy_cmd.clicked.connect(lambda: self.generate_from_dialog(export_dialog))
                btn_box.insertWidget(0, btn_copy_cmd)
                log.info("ExportFFmpegCommand injected '📋 Copy FFmpeg Command' button into Export dialog.")

        except Exception as ex:
            log.warning(f"ExportFFmpegCommand button injection error: {ex}")

    def generate_from_dialog(self, dialog):
        """Build FFmpeg CLI string from active Export QDialog fields and timeline clips."""
        try:
            # Read field values
            out_folder = getattr(dialog.txtExportFolder, "text", lambda: os.path.expanduser("~"))()
            out_name = getattr(dialog.txtFileName, "text", lambda: "output")()
            v_format = getattr(dialog.txtVideoFormat, "text", lambda: "mp4")()
            v_codec = getattr(dialog.txtVideoCodec, "text", lambda: "libx264")()
            v_bitrate = getattr(dialog.txtVideoBitRate, "text", lambda: "15 Mb/s")()
            a_codec = getattr(dialog.txtAudioCodec, "text", lambda: "aac")()
            a_bitrate = getattr(dialog.txtAudioBitrate, "text", lambda: "160 kb/s")()
            s_rate = getattr(dialog.txtSampleRate, "value", lambda: 48000)()
            channels = getattr(dialog.txtChannels, "value", lambda: 2)()
            width = getattr(dialog.txtWidth, "value", lambda: 1920)()
            height = getattr(dialog.txtHeight, "value", lambda: 1080)()

            fps_num = getattr(dialog.txtFrameRateNum, "value", lambda: 60)()
            fps_den = getattr(dialog.txtFrameRateDen, "value", lambda: 1)()
            fps_val = float(fps_num) / float(fps_den) if fps_den > 0 else 60.0

            out_file = os.path.join(out_folder, f"{out_name}.{v_format}")

            # Parse video bitrate string
            bitrate_arg = ""
            if "crf" in v_bitrate.lower():
                crf_val = v_bitrate.lower().replace("crf", "").strip()
                bitrate_arg = f"-crf {crf_val}"
            elif "mb/s" in v_bitrate.lower():
                val = v_bitrate.lower().replace("mb/s", "").strip()
                bitrate_arg = f"-b:v {val}M"
            elif "kb/s" in v_bitrate.lower():
                val = v_bitrate.lower().replace("kb/s", "").strip()
                bitrate_arg = f"-b:v {val}k"
            else:
                bitrate_arg = f"-b:v {v_bitrate}"

            a_bitrate_arg = a_bitrate.lower().replace("kb/s", "k").strip()

            # Inspect timeline clips and project files
            app = get_app()
            proj = app.project
            all_files = {str(f.get("id")): f.get("path") for f in (proj.get("files") or [])}
            all_clips = proj.get("clips") or []

            cmd_str = self.build_ffmpeg_cli_string(
                all_clips, all_files, v_codec, bitrate_arg, fps_val, width, height,
                a_codec, a_bitrate_arg, s_rate, channels, out_file
            )

            win = FFmpegCommandWindow(
                dialog, clips=all_clips, files_map=all_files,
                initial_params={"vcodec": v_codec, "vbitrate": bitrate_arg, "fps": fps_val, "width": width, "height": height, "acodec": a_codec, "abitrate": a_bitrate_arg, "srate": s_rate, "channels": channels, "outfile": out_file},
                builder_func=self.build_ffmpeg_cli_string
            )
            win.exec_()
        except Exception as ex:
            log.warning(f"ExportFFmpegCommand error generating from dialog: {ex}")

    def generate_and_show_command(self):
        """Build FFmpeg command string from project settings when invoked from Tools menu."""
        if not OPENSHOT_AVAILABLE:
            return

        try:
            app = get_app()
            window = getattr(app, "window", None)
            proj = app.project

            all_files = {str(f.get("id")): f.get("path") for f in (proj.get("files") or [])}
            all_clips = proj.get("clips") or []

            win = FFmpegCommandWindow(
                window, clips=all_clips, files_map=all_files,
                builder_func=self.build_ffmpeg_cli_string
            )
            win.exec_()

        except Exception as ex:
            log.warning(f"ExportFFmpegCommand menu trigger error: {ex}")

    def build_ffmpeg_cli_string(self, clips, files_map, v_codec, bitrate_arg, fps, width, height, a_codec, a_bitrate, s_rate, channels, out_file, hw_accel=False):
        """Construct full FFmpeg command string for single or multi-clip timelines."""
        hw_prefix = "-hwaccel auto " if hw_accel else ""

        if not clips:
            input_path = list(files_map.values())[0] if files_map else "input_video.mp4"
            return (
                f'ffmpeg -y {hw_prefix}-i "{input_path}" '
                f'-c:v {v_codec} {bitrate_arg} -r {fps:.2f} -s {width}x{height} '
                f'-c:a {a_codec} -b:a {a_bitrate} -ar {s_rate} -ac {channels} '
                f'"{out_file}"'
            )

        # Sort clips chronologically by position
        sorted_clips = sorted(clips, key=lambda c: float(c.get("position", 0)))

        if len(sorted_clips) == 1:
            clip = sorted_clips[0]
            f_path = files_map.get(str(clip.get("file_id")), "input_video.mp4")
            s_time = float(clip.get("start", 0))
            e_time = float(clip.get("end", 0))
            dur = max(0.1, e_time - s_time)

            return (
                f'ffmpeg -y {hw_prefix}-ss {s_time:.2f} -i "{f_path}" -t {dur:.2f} '
                f'-c:v {v_codec} {bitrate_arg} -r {fps:.2f} -s {width}x{height} '
                f'-c:a {a_codec} -b:a {a_bitrate} -ar {s_rate} -ac {channels} '
                f'"{out_file}"'
            )

        # Multi-clip timeline using FFmpeg filter_complex concat
        inputs_args = []
        filter_parts = []
        concat_inputs = []

        for idx, clip in enumerate(sorted_clips):
            f_path = files_map.get(str(clip.get("file_id")), "input_video.mp4")
            inputs_args.append(f'-i "{f_path}"')
            s_time = float(clip.get("start", 0))
            e_time = float(clip.get("end", 0))
            dur = max(0.1, e_time - s_time)

            ext = os.path.splitext(f_path)[1].lower()
            is_image = ext in ('.png', '.jpg', '.jpeg', '.bmp', '.svg', '.gif')

            if is_image:
                # Image asset: loop image and generate silent audio for clip duration
                filter_parts.append(
                    f"[{idx}:v]loop=loop=-1:size=1,trim=start=0:end={dur:.2f},"
                    f"scale={width}:{height}:force_original_aspect_ratio=decrease,"
                    f"pad={width}:{height}:(ow-iw)/2:(oh-ih)/2,setsar=1,setpts=PTS-STARTPTS[v{idx}]"
                )
                filter_parts.append(
                    f"anullsrc=cl=stereo:r={s_rate},atrim=start=0:end={dur:.2f},"
                    f"asetpts=PTS-STARTPTS[a{idx}]"
                )
            else:
                # Normal video asset with audio
                filter_parts.append(
                    f"[{idx}:v]trim=start={s_time:.2f}:end={e_time:.2f},"
                    f"scale={width}:{height}:force_original_aspect_ratio=decrease,"
                    f"pad={width}:{height}:(ow-iw)/2:(oh-ih)/2,setsar=1,setpts=PTS-STARTPTS[v{idx}]"
                )
                filter_parts.append(
                    f"[{idx}:a]atrim=start={s_time:.2f}:end={e_time:.2f},"
                    f"asetpts=PTS-STARTPTS[a{idx}]"
                )

            concat_inputs.append(f"[v{idx}][a{idx}]")

        filter_str = "; ".join(filter_parts) + f"; {''.join(concat_inputs)}concat=n={len(sorted_clips)}:v=1:a=1[outv][outa]"

        return (
            f'ffmpeg -y {hw_prefix}{" ".join(inputs_args)} '
            f'-filter_complex "{filter_str}" -map "[outv]" -map "[outa]" '
            f'-c:v {v_codec} {bitrate_arg} -r {fps:.2f} '
            f'-c:a {a_codec} -b:a {a_bitrate} -ar {s_rate} -ac {channels} '
            f'"{out_file}"'
        )


# Global instance
_cmd_exporter_instance = None

def load_plugin():
    """Entry point called by OpenShot when loading plugins."""
    global _cmd_exporter_instance
    if _cmd_exporter_instance is None:
        _cmd_exporter_instance = ExportFFmpegCommand()
        _cmd_exporter_instance.initialize()
    else:
        _cmd_exporter_instance.initialize()
    return _cmd_exporter_instance

if OPENSHOT_AVAILABLE:
    try:
        load_plugin()
    except Exception as err:
        log.warning(f"Could not auto-start ExportFFmpegCommand plugin: {err}")
