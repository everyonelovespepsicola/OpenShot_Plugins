"""
MatchExportProfile - OpenShot Video Editor Plugin

This plugin hooks into OpenShot's Export Video dialog. When the user opens the
Export Video window (Ctrl+E or Export button), this plugin automatically syncs
the export target settings (Video Profile, Resolution, Frame Rate, and High Quality)
to match the active project profile's exact specifications.

Author: Antigravity AI
License: MIT
"""

import os
import logging

# PyQt imports with fallback support for PyQt5 and PyQt6
try:
    from PyQt5.QtCore import QObject, QTimer, Qt
    from PyQt5.QtWidgets import QApplication, QDialog, QComboBox
    PYQT_AVAILABLE = True
except ImportError:
    try:
        from PyQt6.QtCore import QObject, QTimer, Qt
        from PyQt6.QtWidgets import QApplication, QDialog, QComboBox
        PYQT_AVAILABLE = True
    except ImportError:
        PYQT_AVAILABLE = False

# OpenShot module imports
try:
    from classes.app import get_app
    from classes.logger import log
    OPENSHOT_AVAILABLE = True
except ImportError:
    OPENSHOT_AVAILABLE = False
    log = logging.getLogger("MatchExportProfile")


class ExportProfileMatcher(QObject if PYQT_AVAILABLE else object):
    """
    Hooks into OpenShot's Export Video trigger to ensure export presets
    and output settings match the active Project Profile.
    """

    def __init__(self):
        if PYQT_AVAILABLE:
            super().__init__()
        self.is_active = False

    def initialize(self):
        """Register the plugin with OpenShot's main window."""
        if not OPENSHOT_AVAILABLE:
            log.warning("OpenShot environment not detected. MatchExportProfile plugin disabled.")
            return

        try:
            app = get_app()
            window = getattr(app, "window", None)
            if window:
                self.hook_export_action(window)
                self.is_active = True
                log.info("MatchExportProfile plugin successfully initialized and hooked.")
            else:
                # Retry hook when window is fully rendered
                if PYQT_AVAILABLE:
                    QTimer.singleShot(1000, self.initialize)
        except Exception as ex:
            log.warning(f"MatchExportProfile initialization error: {ex}")

    def hook_export_action(self, window):
        """Hook into MainWindow.actionExportVideo_trigger to detect when Export window opens."""
        try:
            if hasattr(window, "actionExportVideo_trigger"):
                if not hasattr(window, "_orig_actionExportVideo_trigger"):
                    orig_export = window.actionExportVideo_trigger
                    window._orig_actionExportVideo_trigger = orig_export

                    def wrapped_export_trigger(*args, **kwargs):
                        res = orig_export(*args, **kwargs)
                        if PYQT_AVAILABLE:
                            # Schedule pulses to guarantee pinning after OpenShot finishes internal preset loading
                            QTimer.singleShot(150, self.sync_export_dialog)
                            QTimer.singleShot(400, self.sync_export_dialog)
                            QTimer.singleShot(800, self.sync_export_dialog)
                        return res

                    window.actionExportVideo_trigger = wrapped_export_trigger
                    log.info("MatchExportProfile hooked into actionExportVideo_trigger.")
        except Exception as ex:
            log.warning(f"MatchExportProfile failed to hook actionExportVideo_trigger: {ex}")

    def sync_export_dialog(self):
        """Locate open Export QDialog and align its presets with active Project Profile."""
        if not PYQT_AVAILABLE or not OPENSHOT_AVAILABLE:
            return

        try:
            app = get_app()
            proj = app.project

            proj_profile_name = str(proj.get("profile") or "").lower()
            proj_width = int(proj.get("width") or 0)
            proj_height = int(proj.get("height") or 0)
            proj_fps_data = proj.get("fps") or {}
            proj_fps_num = float(proj_fps_data.get("num", 30))
            proj_fps_den = float(proj_fps_data.get("den", 1))
            proj_fps = proj_fps_num / proj_fps_den if proj_fps_den > 0 else 30.0

            log.info(f"MatchExportProfile reading active profile: '{proj_profile_name}' "
                     f"({proj_width}x{proj_height} @ {proj_fps:.2f} FPS)")

            # Find active Export dialog among top level widgets
            export_dialog = self.find_export_dialog()
            if not export_dialog:
                log.info("MatchExportProfile: Export dialog not found among active windows.")
                return

            self.apply_profile_to_dialog(export_dialog, proj_profile_name, proj_width, proj_height, proj_fps)

        except Exception as ex:
            log.warning(f"MatchExportProfile error during sync_export_dialog: {ex}")

    def find_export_dialog(self):
        """Find the open Export dialog instance in QApplication."""
        try:
            top_widgets = QApplication.topLevelWidgets()
            for widget in top_widgets:
                if isinstance(widget, QDialog) or "Export" in widget.__class__.__name__:
                    title = widget.windowTitle().lower()
                    class_name = widget.__class__.__name__.lower()
                    if "export" in title or "export" in class_name or hasattr(widget, "cboSimpleVideoProfile") or hasattr(widget, "cboProfile") or hasattr(widget, "comboTarget"):
                        return widget
        except Exception as ex:
            log.warning(f"MatchExportProfile error searching topLevelWidgets: {ex}")
        return None

    def apply_profile_to_dialog(self, dialog, proj_profile_name, p_w, p_h, p_fps):
        """Set Export dialog combo boxes to match project profile parameters and pin to TOP (Index 0)."""
        try:
            # 1. Match Video Profile Combo Box (cboSimpleVideoProfile and cboProfile)
            profile_combos = []
            for attr in ["cboSimpleVideoProfile", "cboProfile", "comboVideoProfile", "comboProfile"]:
                cb = getattr(dialog, attr, None)
                if cb and isinstance(cb, QComboBox) and cb not in profile_combos:
                    profile_combos.append(cb)

            for combo_profile in profile_combos:
                target_idx = -1
                best_match_idx = -1

                for idx in range(combo_profile.count()):
                    item_text = combo_profile.itemText(idx).lower()
                    item_data = str(combo_profile.itemData(idx) or "").lower()

                    # Direct profile name match
                    if proj_profile_name and (proj_profile_name in item_text or proj_profile_name in item_data):
                        target_idx = idx
                        break

                    # Resolution & FPS text match (e.g. "1920x1080" and "60")
                    res_str = f"{p_w}x{p_h}"
                    fps_str = f"{int(p_fps)}"
                    if res_str in item_text and fps_str in item_text:
                        best_match_idx = idx

                selected_idx = target_idx if target_idx != -1 else best_match_idx
                target_pos = 1 if combo_profile.count() > 1 else 0

                if selected_idx != -1:
                    orig_text = combo_profile.itemText(selected_idx)
                    orig_data = combo_profile.itemData(selected_idx)
                    if not orig_text.startswith("⭐"):
                        combo_profile.removeItem(selected_idx)
                        pinned_label = f"⭐ [PROJECT MATCH] {orig_text}"
                        combo_profile.insertItem(target_pos, pinned_label, orig_data)
                    combo_profile.setCurrentIndex(target_pos)
                    log.info(f"MatchExportProfile pinned profile to Index {target_pos}: '{combo_profile.itemText(target_pos)}'")
                else:
                    pinned_label = f"⭐ [PROJECT MATCH] {proj_profile_name.upper()} ({p_w}x{p_h} @ {p_fps:.2f} FPS)"
                    if not combo_profile.itemText(target_pos).startswith("⭐"):
                        combo_profile.insertItem(target_pos, pinned_label)
                    combo_profile.setCurrentIndex(target_pos)
                    log.info(f"MatchExportProfile created & pinned profile entry at Index {target_pos}: '{pinned_label}'")

            # 2. Match Target / Format (cboSimpleTarget and comboTarget)
            target_combos = []
            for attr in ["cboSimpleTarget", "comboTarget", "comboSimpleTarget"]:
                cb = getattr(dialog, attr, None)
                if cb and isinstance(cb, QComboBox) and cb not in target_combos:
                    target_combos.append(cb)

            for combo_target in target_combos:
                # Hook index changed to re-apply pinning if OpenShot rebuilds list on target selection
                if not hasattr(combo_target, "_hooked_matcher"):
                    combo_target._hooked_matcher = True
                    combo_target.currentIndexChanged.connect(lambda idx: QTimer.singleShot(150, self.sync_export_dialog))

                target_match_idx = -1
                for idx in range(combo_target.count()):
                    text = combo_target.itemText(idx).lower()
                    if "mp4" in text or "h.264" in text or "h264" in text:
                        target_match_idx = idx
                        break

                target_pos = 1 if combo_target.count() > 1 else 0

                if target_match_idx != -1:
                    orig_text = combo_target.itemText(target_match_idx)
                    orig_data = combo_target.itemData(target_match_idx)
                    if not orig_text.startswith("⭐"):
                        combo_target.removeItem(target_match_idx)
                        pinned_target = f"⭐ {orig_text}"
                        combo_target.insertItem(target_pos, pinned_target, orig_data)
                    combo_target.setCurrentIndex(target_pos)
                    log.info(f"MatchExportProfile pinned target format to Index {target_pos}: '{combo_target.itemText(target_pos)}'")

            # 3. Match High Quality preset (cboSimpleQuality and comboQuality)
            quality_combos = []
            for attr in ["cboSimpleQuality", "comboQuality", "comboSimpleQuality"]:
                cb = getattr(dialog, attr, None)
                if cb and isinstance(cb, QComboBox) and cb not in quality_combos:
                    quality_combos.append(cb)

            for combo_quality in quality_combos:
                for idx in range(combo_quality.count()):
                    text = combo_quality.itemText(idx).lower()
                    if "high" in text:
                        combo_quality.setCurrentIndex(idx)
                        log.info("MatchExportProfile set Quality to High.")
                        break

        except Exception as ex:
            log.warning(f"MatchExportProfile error applying settings to Export dialog: {ex}")


# Global instance
_export_matcher_instance = None

def load_plugin():
    """Entry point called by OpenShot when loading plugins."""
    global _export_matcher_instance
    if _export_matcher_instance is None:
        _export_matcher_instance = ExportProfileMatcher()
        _export_matcher_instance.initialize()
    else:
        _export_matcher_instance.initialize()
    return _export_matcher_instance

# Auto-initialize if imported in OpenShot runtime
if OPENSHOT_AVAILABLE:
    try:
        load_plugin()
    except Exception as err:
        log.warning(f"Could not auto-start MatchExportProfile plugin: {err}")
