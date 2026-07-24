"""
SwitchProjectProfile - OpenShot Video Editor Plugin

This plugin detects when media files (such as 60 FPS or 4K videos) are imported
or added to OpenShot. If the media resolution or frame rate (FPS) does not match
the active project profile, the plugin prompts the user with a dialog asking if
they would like to switch the project profile to match the imported video.

Author: Antigravity AI
License: GPLv3
"""

import os
import json
import logging

try:
    from PyQt5.QtCore import QObject, QTimer, Qt
    from PyQt5.QtWidgets import QMessageBox
    PYQT_AVAILABLE = True
except ImportError:
    PYQT_AVAILABLE = False

# OpenShot module imports
try:
    from classes.app import get_app
    from classes.logger import log
    from classes.query import File
    OPENSHOT_AVAILABLE = True
except ImportError:
    OPENSHOT_AVAILABLE = False
    log = logging.getLogger("SwitchProjectProfile")


class ProfileChecker(QObject if PYQT_AVAILABLE else object):
    """
    Listens for project file additions and checks if the project profile
    matches the imported video's resolution and frame rate.
    """

    def __init__(self):
        if PYQT_AVAILABLE:
            super().__init__()
        self.processed_files = set()
        self.auto_switch = False
        self.prompt_user = True
        self.is_active = False

    def initialize(self):
        """Register the plugin with OpenShot update listeners and models."""
        if not OPENSHOT_AVAILABLE:
            log.warning("OpenShot environment not detected. ProfileChecker plugin disabled.")
            return

        app = get_app()
        if hasattr(app, "updates"):
            app.updates.add_listener(self)
            self.is_active = True
            log.info("SwitchProjectProfile plugin registered with UpdateManager.")

        # Also hook into FilesModel.add_files if main window exists
        self.hook_files_model()

    def hook_files_model(self):
        """Hook into FilesModel.add_files as a secondary trigger."""
        try:
            app = get_app()
            window = getattr(app, "window", None)
            if window and hasattr(window, "files_model"):
                files_model = window.files_model
                if not hasattr(files_model, "_orig_add_files"):
                    orig_add_files = files_model.add_files
                    files_model._orig_add_files = orig_add_files

                    def wrapped_add_files(files, *args, **kwargs):
                        res = orig_add_files(files, *args, **kwargs)
                        if PYQT_AVAILABLE:
                            QTimer.singleShot(200, self.check_all_recent_files)
                        return res

                    files_model.add_files = wrapped_add_files
                    log.info("SwitchProjectProfile hooked into FilesModel.add_files.")
        except Exception as ex:
            log.warning(f"SwitchProjectProfile could not hook FilesModel: {ex}")

    def changed(self, action):
        """
        Invoked by OpenShot's UpdateManager whenever project data changes.
        """
        if not self.is_active or not action:
            return

        try:
            key = getattr(action, "key", [])
            if key and len(key) >= 1 and str(key[0]).lower() == "files":
                action_type = getattr(action, "type", "")
                if action_type in ("insert", "update"):
                    # Extract file values (handles action.values or action.value)
                    file_data = getattr(action, "values", None) or getattr(action, "value", None)
                    if isinstance(file_data, dict):
                        self.process_file_data(file_data)
                    elif isinstance(file_data, list):
                        for item in file_data:
                            if isinstance(item, dict):
                                self.process_file_data(item)
                    else:
                        # Fallback: check recent files in project
                        if PYQT_AVAILABLE:
                            QTimer.singleShot(200, self.check_all_recent_files)
        except Exception as ex:
            log.warning(f"SwitchProjectProfile error in changed(): {ex}")

    def check_all_recent_files(self):
        """Inspect all files in the project to check for profile mismatches."""
        try:
            files = File.filter()
            for file_obj in files:
                if file_obj and hasattr(file_obj, "data"):
                    self.process_file_data(file_obj.data, file_obj=file_obj)
        except Exception as ex:
            log.warning(f"SwitchProjectProfile error during check_all_recent_files: {ex}")

    def process_file_data(self, file_data, file_obj=None):
        """Process a single file's data dictionary."""
        file_id = file_data.get("id")
        if file_id and file_id in self.processed_files:
            return
        if file_id:
            self.processed_files.add(file_id)

        if PYQT_AVAILABLE:
            QTimer.singleShot(50, lambda: self.check_file_profile(file_data, file_obj))

    def check_file_profile(self, file_data, file_obj=None):
        """
        Compare video file metadata with current project profile and prompt user if mismatched.
        """
        try:
            app = get_app()
            proj = app.project

            # Only process video files
            media_type = file_data.get("media_type")
            has_video = file_data.get("has_video", False)
            if media_type != "video" and not has_video:
                return

            file_width = int(file_data.get("width", 0))
            file_height = int(file_data.get("height", 0))

            file_fps_data = file_data.get("fps", {})
            file_fps_num = float(file_fps_data.get("num", 30))
            file_fps_den = float(file_fps_data.get("den", 1))
            file_fps = file_fps_num / file_fps_den if file_fps_den > 0 else 30.0

            # Current project settings
            proj_width = int(proj.get("width") or 0)
            proj_height = int(proj.get("height") or 0)
            proj_fps_data = proj.get("fps") or {}
            proj_fps_num = float(proj_fps_data.get("num", 30))
            proj_fps_den = float(proj_fps_data.get("den", 1))
            proj_fps = proj_fps_num / proj_fps_den if proj_fps_den > 0 else 30.0

            # Determine if there is a mismatch
            width_mismatch = (file_width > 0 and proj_width > 0 and file_width != proj_width)
            height_mismatch = (file_height > 0 and proj_height > 0 and file_height != proj_height)
            fps_mismatch = abs(file_fps - proj_fps) > 0.05

            log.info(f"SwitchProjectProfile evaluating file: '{file_data.get('name')}' "
                     f"({file_width}x{file_height}@{file_fps:.2f}fps) vs Project "
                     f"({proj_width}x{proj_height}@{proj_fps:.2f}fps) -> mismatch={width_mismatch or height_mismatch or fps_mismatch}")

            if not (width_mismatch or height_mismatch or fps_mismatch):
                # File matches current project profile
                return

            # Lookup file object to retrieve file profile
            if not file_obj:
                file_id = file_data.get("id")
                file_obj = File.get(id=file_id) if file_id else None

            if not file_obj:
                return

            file_profile = file_obj.profile()
            file_name = file_data.get("name") or os.path.basename(file_data.get("path", "video"))

            # Auto-switch if enabled for session
            if self.auto_switch:
                log.info(f"Auto-switching project profile for '{file_name}' to {file_profile.info.description}")
                main_win = getattr(app, "window", None)
                if hasattr(main_win, "actionProfile_trigger"):
                    main_win.actionProfile_trigger(file_profile)
                return

            # Prompt user
            if self.prompt_user and PYQT_AVAILABLE:
                self.show_switch_dialog(file_name, file_width, file_height, file_fps,
                                         proj_width, proj_height, proj_fps, file_profile)

        except Exception as ex:
            log.warning(f"SwitchProjectProfile error during file check: {ex}")

    def show_switch_dialog(self, file_name, f_w, f_h, f_fps, p_w, p_h, p_fps, file_profile):
        """
        Display a PyQt dialog asking the user if they want to switch project profile.
        """
        app = get_app()
        main_win = getattr(app, "window", None)

        dialog = QMessageBox(main_win)
        dialog.setWindowTitle("Match Project Profile?")
        dialog.setIcon(QMessageBox.Question)

        current_info = f"{p_w}x{p_h} @ {p_fps:.2f} FPS"
        video_info = f"{f_w}x{f_h} @ {f_fps:.2f} FPS"

        description_text = file_profile.info.description if hasattr(file_profile, "info") else "Matching Profile"

        text = (
            f"<b>Imported Video Mismatch Detected</b><br><br>"
            f"The file <b>'{file_name}'</b> (<i>{video_info}</i>) does not match "
            f"your current project profile (<i>{current_info}</i>).<br><br>"
            f"Would you like to switch your project profile to <b>{description_text}</b>?"
        )
        dialog.setText(text)

        switch_btn = dialog.addButton(f"Switch Profile ({description_text})", QMessageBox.AcceptRole)
        always_btn = dialog.addButton("Always Switch for This Session", QMessageBox.AcceptRole)
        keep_btn = dialog.addButton("Keep Current Profile", QMessageBox.RejectRole)

        dialog.setDefaultButton(switch_btn)
        dialog.exec_()

        clicked = dialog.clickedButton()
        if clicked in (switch_btn, always_btn):
            if clicked == always_btn:
                self.prompt_user = False
                self.auto_switch = True

            log.info(f"Switching project profile to match {file_name}: {description_text}")
            if hasattr(main_win, "actionProfile_trigger"):
                main_win.actionProfile_trigger(file_profile)


# Global instance
_checker_instance = None

def load_plugin():
    """Entry point called by OpenShot when loading plugins."""
    global _checker_instance
    if _checker_instance is None:
        _checker_instance = ProfileChecker()
        _checker_instance.initialize()
    else:
        _checker_instance.initialize()
    return _checker_instance

# Auto-initialize if imported in OpenShot runtime
if OPENSHOT_AVAILABLE:
    try:
        load_plugin()
    except Exception as err:
        log.warning(f"Could not auto-start SwitchProjectProfile plugin: {err}")
