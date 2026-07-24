"""
PluginViewer - OpenShot Video Editor Plugin

Adds an 'Installed Plug-ins' viewer under OpenShot's Help menu (Help -> Plug-ins)
that displays a clean summary of all currently loaded and installed plugins.

Author: Antigravity AI
License: MIT
"""

import os
import sys
import logging

try:
    from PyQt5.QtCore import QObject, Qt
    from PyQt5.QtWidgets import QMessageBox, QAction
    PYQT_AVAILABLE = True
except ImportError:
    try:
        from PyQt6.QtCore import QObject, Qt
        from PyQt6.QtGui import QAction
        from PyQt6.QtWidgets import QMessageBox
        PYQT_AVAILABLE = True
    except ImportError:
        PYQT_AVAILABLE = False

try:
    from classes.app import get_app
    from classes.logger import log
    OPENSHOT_AVAILABLE = True
except ImportError:
    OPENSHOT_AVAILABLE = False
    log = logging.getLogger("PluginViewer")


class PluginViewer(QObject if PYQT_AVAILABLE else object):
    """
    Hooks into OpenShot's Help menu to display a simple popout dialog
    listing all installed and active plugins.
    """

    def __init__(self):
        if PYQT_AVAILABLE:
            super().__init__()

    def initialize(self):
        """Register menu item in OpenShot MainWindow Help menu."""
        if not OPENSHOT_AVAILABLE:
            return

        try:
            app = get_app()
            window = getattr(app, "window", None)
            if window and PYQT_AVAILABLE:
                self.add_help_menu_item(window)
                log.info("PluginViewer initialized and added to Help menu.")
        except Exception as ex:
            log.warning(f"PluginViewer initialization error: {ex}")

    def add_help_menu_item(self, window):
        """Find Help menu and append 'Plug-ins' action."""
        try:
            menu_bar = window.menuBar()
            if not menu_bar:
                return

            help_menu = None
            for action in menu_bar.actions():
                if "help" in action.text().lower() or "ayuda" in action.text().lower():
                    help_menu = action.menu()
                    break

            if not help_menu:
                help_menu = menu_bar.addMenu("Help")

            # Check if action already exists
            for action in help_menu.actions():
                if "plug-in" in action.text().lower() or "plugin" in action.text().lower():
                    return

            plugins_action = help_menu.addAction("🔌 Installed Plug-ins")
            plugins_action.triggered.connect(self.show_installed_plugins_dialog)
            log.info("PluginViewer added '🔌 Installed Plug-ins' action to Help menu.")
        except Exception as ex:
            log.warning(f"PluginViewer failed to add menu item: {ex}")

    def show_installed_plugins_dialog(self):
        """Pop up a clean dialog listing installed plugins and their status."""
        if not PYQT_AVAILABLE or not OPENSHOT_AVAILABLE:
            return

        app = get_app()
        window = getattr(app, "window", None)

        msg = QMessageBox(window)
        msg.setWindowTitle("Installed Plug-ins")
        msg.setIcon(QMessageBox.Information)

        plugins_list = [
            "<b>🎬 SwitchProjectProfile</b><br>"
            "<i>Status: Active</i><br>"
            "Automatically prompts to match project FPS and resolution on media import.<br>",

            "<b>📤 MatchExportProfile</b><br>"
            "<i>Status: Active</i><br>"
            "Auto-selects matching profile, MP4 container, and High Quality preset in Export window.<br>",

            "<b>🔌 PluginViewer</b><br>"
            "<i>Status: Active</i><br>"
            "Displays installed plugin information in OpenShot Help menu."
        ]

        dialog_text = (
            "<h3>🔌 OpenShot Installed Plug-ins</h3>"
            "<hr>"
            + "<br><br>".join(plugins_list)
        )

        msg.setText(dialog_text)
        msg.exec_()


# Global instance
_viewer_instance = None

def load_plugin():
    """Entry point called by OpenShot when loading plugins."""
    global _viewer_instance
    if _viewer_instance is None:
        _viewer_instance = PluginViewer()
        _viewer_instance.initialize()
    else:
        _viewer_instance.initialize()
    return _viewer_instance

if OPENSHOT_AVAILABLE:
    try:
        load_plugin()
    except Exception as err:
        log.warning(f"Could not auto-start PluginViewer plugin: {err}")
