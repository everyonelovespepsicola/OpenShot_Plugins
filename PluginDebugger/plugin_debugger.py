"""
PluginDebugger - OpenShot Video Editor Plugin

This plugin provides a dedicated real-time debugging GUI and widget inspector
for OpenShot plugins (including SwitchProjectProfile and MatchExportProfile).

Features:
- Live status monitor for loaded OpenShot plugins
- Real-time QWidget inspector for active windows & Export dialog combo boxes
- In-app live diagnostic terminal & log viewer
- Force-trigger buttons to manually execute MatchExportProfile sync

Shortcut: F12 or Ctrl+Shift+D (or Tools -> Plugin Debugger)

Author: Antigravity AI
License: MIT
"""

import os
import sys
import logging

try:
    from PyQt5.QtCore import QObject, QTimer, Qt
    from PyQt5.QtWidgets import (
        QApplication, QDialog, QVBoxLayout, QHBoxLayout, QLabel,
        QPushButton, QTextEdit, QTreeWidget, QTreeWidgetItem, QTabWidget, QWidget, QShortcut
    )
    from PyQt5.QtGui import QKeySequence, QFont
    PYQT_AVAILABLE = True
except ImportError:
    try:
        from PyQt6.QtCore import QObject, QTimer, Qt
        from PyQt6.QtWidgets import (
            QApplication, QDialog, QVBoxLayout, QHBoxLayout, QLabel,
            QPushButton, QTextEdit, QTreeWidget, QTreeWidgetItem, QTabWidget, QWidget, QShortcut
        )
        from PyQt6.QtGui import QKeySequence, QFont
        PYQT_AVAILABLE = True
    except ImportError:
        PYQT_AVAILABLE = False

try:
    from classes.app import get_app
    from classes.logger import log
    OPENSHOT_AVAILABLE = True
except ImportError:
    OPENSHOT_AVAILABLE = False
    log = logging.getLogger("PluginDebugger")


class DebuggerWindow(QDialog if PYQT_AVAILABLE else object):
    """PyQt GUI window for inspecting OpenShot plugins, active widgets, and export dialogs."""

    def __init__(self, parent=None):
        if PYQT_AVAILABLE:
            super().__init__(parent)
            self.setWindowTitle("🛠️ OpenShot Plugin Debugger & Inspector")
            self.resize(750, 520)
            self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout(self)

        # Header
        header = QLabel("<h3>🛠️ OpenShot Plugin Debugger & Inspector</h3>")
        layout.addWidget(header)

        # Tab Widget
        self.tabs = QTabWidget()
        layout.addWidget(self.tabs)

        # Tab 1: Plugin Status
        self.tab_plugins = QWidget()
        t1_layout = QVBoxLayout(self.tab_plugins)
        self.lbl_status = QLabel("Checking loaded plugins...")
        t1_layout.addWidget(self.lbl_status)
        self.txt_plugins_info = QTextEdit()
        self.txt_plugins_info.setReadOnly(True)
        t1_layout.addWidget(self.txt_plugins_info)
        self.tabs.addTab(self.tab_plugins, "🔌 Plugins Status")

        # Tab 2: Widget Inspector
        self.tab_widgets = QWidget()
        t2_layout = QVBoxLayout(self.tab_widgets)
        t2_hdr = QLabel("<b>Active Window & Export Dialog Widgets Tree:</b>")
        t2_layout.addWidget(t2_hdr)
        self.tree_widgets = QTreeWidget()
        self.tree_widgets.setHeaderLabels(["Widget Object Name", "Widget Type", "Selected Value / Items"])
        t2_layout.addWidget(self.tree_widgets)
        btn_refresh_tree = QPushButton("🔄 Refresh Widget Tree")
        btn_refresh_tree.clicked.connect(self.inspect_widgets)
        t2_layout.addWidget(btn_refresh_tree)
        self.tabs.addTab(self.tab_widgets, "🔍 Widget Inspector")

        # Tab 3: Live Terminal Logs
        self.tab_logs = QWidget()
        t3_layout = QVBoxLayout(self.tab_logs)
        self.txt_logs = QTextEdit()
        self.txt_logs.setReadOnly(True)
        self.txt_logs.setFont(QFont("Consolas", 9))
        t3_layout.addWidget(self.txt_logs)
        self.tabs.addTab(self.tab_logs, "📜 Live Diagnostics Log")

        # Bottom Actions Bar
        btn_layout = QHBoxLayout()

        btn_sync_export = QPushButton("⚡ Force MatchExport Sync")
        btn_sync_export.setStyleSheet("font-weight: bold; background-color: #0275d8; color: white; padding: 6px;")
        btn_sync_export.clicked.connect(self.force_match_export_sync)
        btn_layout.addWidget(btn_sync_export)

        btn_refresh_all = QPushButton("🔄 Refresh All")
        btn_refresh_all.clicked.connect(self.refresh_all)
        btn_layout.addWidget(btn_refresh_all)

        btn_close = QPushButton("Close")
        btn_close.clicked.connect(self.close)
        btn_layout.addWidget(btn_close)

        layout.addLayout(btn_layout)

        self.refresh_all()

    def refresh_all(self):
        """Refresh plugin status, widget tree, and logs."""
        self.check_plugin_status()
        self.inspect_widgets()

    def check_plugin_status(self):
        """Check status of loaded OpenShot plugins."""
        if not OPENSHOT_AVAILABLE:
            self.lbl_status.setText("OpenShot environment not loaded.")
            return

        status_lines = []
        status_lines.append("=== OpenShot Plugins Health Check ===")

        # Check SwitchProjectProfile
        try:
            import switch_project_profile
            status_lines.append("✅ [SwitchProjectProfile]: Installed and importable.")
        except ImportError:
            status_lines.append("❌ [SwitchProjectProfile]: Not found in sys.path.")

        # Check MatchExportProfile
        try:
            import match_export_profile
            status_lines.append("✅ [MatchExportProfile]: Installed and importable.")
        except ImportError:
            status_lines.append("❌ [MatchExportProfile]: Not found in sys.path.")

        # App & Project Info
        app = get_app()
        proj = app.project
        status_lines.append("\n=== Current Project Profile ===")
        status_lines.append(f"Name: {proj.get('profile')}")
        status_lines.append(f"Resolution: {proj.get('width')}x{proj.get('height')}")
        status_lines.append(f"FPS: {proj.get('fps')}")

        self.txt_plugins_info.setText("\n".join(status_lines))

    def inspect_widgets(self):
        """Inspect all top-level QDialogs and list key combo boxes."""
        if not PYQT_AVAILABLE:
            return

        self.tree_widgets.clear()
        top_widgets = QApplication.topLevelWidgets()

        for w in top_widgets:
            w_name = w.objectName() or w.__class__.__name__
            w_title = getattr(w, "windowTitle", lambda: "")()
            w_item = QTreeWidgetItem(self.tree_widgets, [w_name, w.__class__.__name__, w_title])

            # Inspect child combo boxes
            try:
                combos = w.findChildren(QObject)
                for child in combos:
                    c_name = child.objectName()
                    if c_name and ("cbo" in c_name.lower() or "combo" in c_name.lower()):
                        cur_text = ""
                        count_info = ""
                        if hasattr(child, "currentText"):
                            cur_text = f"Selected: '{child.currentText()}'"
                        if hasattr(child, "count"):
                            count_info = f" ({child.count()} items)"

                        QTreeWidgetItem(w_item, [c_name, child.__class__.__name__, f"{cur_text}{count_info}"])
            except Exception as ex:
                QTreeWidgetItem(w_item, ["Error inspecting children", str(ex), ""])

        self.tree_widgets.expandAll()

    def force_match_export_sync(self):
        """Manually trigger MatchExportProfile sync on active export dialog."""
        try:
            import match_export_profile
            matcher = match_export_profile.load_plugin()
            matcher.sync_export_dialog()
            self.log_msg("⚡ Force executed MatchExportProfile sync!")
            self.refresh_all()
        except Exception as ex:
            self.log_msg(f"❌ Error triggering MatchExportProfile: {ex}")

    def log_msg(self, msg):
        self.txt_logs.append(msg)


class PluginDebugger(QObject if PYQT_AVAILABLE else object):
    """Main plugin object registered with OpenShot."""

    def __init__(self):
        if PYQT_AVAILABLE:
            super().__init__()
        self.debug_dialog = None

    def initialize(self):
        if not OPENSHOT_AVAILABLE:
            return

        try:
            app = get_app()
            window = getattr(app, "window", None)
            if window and PYQT_AVAILABLE:
                # Add F12 global shortcut
                self.shortcut = QShortcut(QKeySequence(Qt.Key_F12), window)
                self.shortcut.activated.connect(self.show_debugger)

                # Add Ctrl+Shift+D shortcut
                self.shortcut2 = QShortcut(QKeySequence("Ctrl+Shift+D"), window)
                self.shortcut2.activated.connect(self.show_debugger)

                # Add top menu bar item under Plugins / Tools / Help
                menu_bar = window.menuBar()
                if menu_bar:
                    plugins_menu = None
                    for action in menu_bar.actions():
                        if "help" in action.text().lower() or "tool" in action.text().lower() or "plugin" in action.text().lower():
                            plugins_menu = action.menu()
                            break
                    if not plugins_menu:
                        plugins_menu = menu_bar.addMenu("Plugins")

                    dbg_action = plugins_menu.addAction("🛠️ OpenShot Plugin Debugger")
                    dbg_action.setShortcut(QKeySequence("F12"))
                    dbg_action.triggered.connect(self.show_debugger)

                log.info("PluginDebugger initialized. Press F12 or use Plugins menu.")
        except Exception as ex:
            log.warning(f"PluginDebugger init warning: {ex}")

    def show_debugger(self):
        """Display the Plugin Debugger GUI window."""
        if PYQT_AVAILABLE:
            app = get_app()
            win = getattr(app, "window", None)
            self.debug_dialog = DebuggerWindow(win)
            self.debug_dialog.show()


# Global instance
_debugger_instance = None

def load_plugin():
    """Entry point called by OpenShot when loading plugins."""
    global _debugger_instance
    if _debugger_instance is None:
        _debugger_instance = PluginDebugger()
        _debugger_instance.initialize()
    else:
        _debugger_instance.initialize()
    return _debugger_instance

if OPENSHOT_AVAILABLE:
    try:
        load_plugin()
    except Exception as err:
        log.warning(f"Could not auto-start PluginDebugger plugin: {err}")
