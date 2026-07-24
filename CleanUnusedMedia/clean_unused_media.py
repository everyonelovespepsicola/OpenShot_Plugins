"""
CleanUnusedMedia - OpenShot Video Editor Plugin

Scans the active project and identifies files in the Project Files bin
that are not currently placed on any timeline track. Offers a 1-click
cleanup to remove unused media and keep the Project Bin clutter-free.

Features:
- Right-click context menu integration in Project Files Bin
- Main Tools menu action
- Reliable File deletion from OpenShot project model

Author: Antigravity AI
License: MIT
"""

import os
import sys
import logging

try:
    from PyQt5.QtCore import QObject, Qt, QItemSelectionModel
    from PyQt5.QtWidgets import (
        QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QListWidget, QListWidgetItem, QMessageBox, QMenu
    )
    PYQT_AVAILABLE = True
except ImportError:
    try:
        from PyQt6.QtCore import QObject, Qt, QItemSelectionModel
        from PyQt6.QtWidgets import (
            QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QListWidget, QListWidgetItem, QMessageBox, QMenu
        )
        PYQT_AVAILABLE = True
    except ImportError:
        PYQT_AVAILABLE = False

try:
    from classes.app import get_app
    from classes.logger import log
    from classes.query import File
    OPENSHOT_AVAILABLE = True
except ImportError:
    OPENSHOT_AVAILABLE = False
    log = logging.getLogger("CleanUnusedMedia")


class CleanUnusedMediaDialog(QDialog if PYQT_AVAILABLE else object):
    """PyQt Dialog for reviewing and removing unused media files from project bin."""

    def __init__(self, parent=None, unused_files=None):
        if PYQT_AVAILABLE:
            super().__init__(parent)
            self.setWindowTitle("🧹 Clean Unused Media")
            self.resize(550, 380)
            self.unused_files = unused_files or []
            self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout(self)

        header = QLabel("<h3>🧹 Clean Unused Media Files</h3>"
                        "<p>The following files in your Project Bin are not used on any timeline track:</p>")
        layout.addWidget(header)

        self.list_widget = QListWidget()
        for f in self.unused_files:
            file_name = f.get("name") or os.path.basename(f.get("path", "Unknown"))
            file_path = f.get("path", "")
            item = QListWidgetItem(f"📄 {file_name} ({file_path})")
            item.setData(Qt.UserRole, f)
            self.list_widget.addItem(item)
        layout.addWidget(self.list_widget)

        # Buttons
        btn_layout = QHBoxLayout()

        btn_clean = QPushButton("🧹 Remove Selected Unused Files")
        btn_clean.setStyleSheet("font-weight: bold; background-color: #d9534f; color: white; padding: 6px;")
        btn_clean.clicked.connect(self.clean_files)
        btn_layout.addWidget(btn_clean)

        btn_cancel = QPushButton("Cancel")
        btn_cancel.clicked.connect(self.reject)
        btn_layout.addWidget(btn_cancel)

        layout.addLayout(btn_layout)

    def clean_files(self):
        """Remove identified unused files from OpenShot project files bin."""
        if not OPENSHOT_AVAILABLE:
            self.reject()
            return

        try:
            app = get_app()
            window = getattr(app, "window", None)

            count = 0
            for i in range(self.list_widget.count()):
                item = self.list_widget.item(i)
                f_data = item.data(Qt.UserRole)
                f_id = f_data.get("id")

                # Method A: Use OpenShot Query File model to delete from project DB
                try:
                    file_obj = File.get(id=f_id)
                    if file_obj:
                        file_obj.delete()
                        count += 1
                        continue
                except Exception as ex_db:
                    log.warning(f"File.get({f_id}).delete() error: {ex_db}")

                # Method B: Direct removal from app.project.get("files")
                all_files = app.project.get("files") or []
                updated_files = [f for f in all_files if str(f.get("id")) != str(f_id)]
                app.project.set("files", updated_files)
                count += 1

            # Save project state & refresh Project Files Bin UI
            try:
                app.project.save()
            except Exception:
                pass

            if window and hasattr(window, "files_model") and hasattr(window.files_model, "update_model"):
                window.files_model.update_model()

            QMessageBox.information(self, "Cleanup Complete", f"Successfully removed {count} unused file(s) from Project Bin!")
            self.accept()
        except Exception as ex:
            log.warning(f"CleanUnusedMedia error removing files: {ex}")
            self.reject()


class CleanUnusedMedia(QObject if PYQT_AVAILABLE else object):
    """Main plugin object registered with OpenShot."""

    def __init__(self):
        if PYQT_AVAILABLE:
            super().__init__()
        self._context_hooked = False

    def initialize(self):
        if not OPENSHOT_AVAILABLE:
            return

        try:
            app = get_app()
            window = getattr(app, "window", None)
            if window and PYQT_AVAILABLE:
                self.add_menu_item(window)
                self.hook_context_menus(window)
                log.info("CleanUnusedMedia plugin initialized.")
        except Exception as ex:
            log.warning(f"CleanUnusedMedia init warning: {ex}")

    def add_menu_item(self, window):
        """Add menu action under Tools menu (placed BEFORE Help menu)."""
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
                tools_menu = QMenu("&Tools", window)
                if help_action:
                    menu_bar.insertMenu(help_action, tools_menu)
                else:
                    menu_bar.addMenu(tools_menu)

            # Prevent duplicate actions
            for action in tools_menu.actions():
                if "clean unused" in action.text().lower():
                    return

            clean_action = tools_menu.addAction("🧹 Clean Unused Media...")
            clean_action.triggered.connect(self.scan_and_prompt_clean)
            log.info("CleanUnusedMedia added '🧹 Clean Unused Media...' action to Tools menu.")
        except Exception as ex:
            log.warning(f"CleanUnusedMedia failed to add menu item: {ex}")

    def hook_context_menus(self, window):
        """Hook into Project Files bin context menus (TreeView and ListView)."""
        if self._context_hooked:
            return

        try:
            # Hook FilesTreeView
            tree_view = getattr(window, "files_treeview", None)
            if tree_view and hasattr(tree_view, "contextMenuEvent"):
                orig_context_tree = tree_view.contextMenuEvent

                def wrapped_context_tree(event):
                    res = orig_context_tree(event)
                    self.append_context_action(tree_view, event)
                    return res

                # Only hook if not already wrapped
                if not hasattr(tree_view, "_cleaner_hooked"):
                    tree_view._cleaner_hooked = True
                    tree_view.contextMenuEvent = wrapped_context_tree

            # Hook FilesListView
            list_view = getattr(window, "files_listview", None)
            if list_view and hasattr(list_view, "contextMenuEvent"):
                orig_context_list = list_view.contextMenuEvent

                def wrapped_context_list(event):
                    res = orig_context_list(event)
                    self.append_context_action(list_view, event)
                    return res

                if not hasattr(list_view, "_cleaner_hooked"):
                    list_view._cleaner_hooked = True
                    list_view.contextMenuEvent = wrapped_context_list

            self._context_hooked = True
            log.info("CleanUnusedMedia hooked into Project Bin context menus.")
        except Exception as ex:
            log.warning(f"CleanUnusedMedia context menu hook warning: {ex}")

    def append_context_action(self, widget, event):
        """Append 'Clean Unused Media...' to the active context menu."""
        try:
            # Find open context menu near cursor
            top_widgets = get_app().window.findChildren(QObject)
            for child in top_widgets:
                if child.__class__.__name__ == "StyledContextMenu" and child.isVisible():
                    # Check if action already added
                    for act in child.actions():
                        if "clean unused" in act.text().lower():
                            return
                    child.addSeparator()
                    action = child.addAction("🧹 Clean Unused Media...")
                    action.triggered.connect(self.scan_and_prompt_clean)
                    break
        except Exception as ex:
            log.warning(f"CleanUnusedMedia error appending context action: {ex}")

    def scan_and_prompt_clean(self):
        """Scan clips vs files and prompt user if unused files exist."""
        if not PYQT_AVAILABLE or not OPENSHOT_AVAILABLE:
            return

        try:
            app = get_app()
            window = getattr(app, "window", None)
            proj = app.project

            all_files = proj.get("files") or []
            all_clips = proj.get("clips") or []

            # Collect all file IDs used on timeline
            used_file_ids = set()
            for clip in all_clips:
                f_id = clip.get("file_id")
                if f_id:
                    used_file_ids.add(str(f_id))

            # Filter unused files
            unused_files = [f for f in all_files if str(f.get("id")) not in used_file_ids]

            if not unused_files:
                QMessageBox.information(
                    window, "Clean Unused Media",
                    "✨ Your Project Bin is clean! All imported files are currently placed on the timeline."
                )
                return

            # Open cleanup dialog
            dlg = CleanUnusedMediaDialog(window, unused_files)
            dlg.exec_()

        except Exception as ex:
            log.warning(f"CleanUnusedMedia error during scan: {ex}")


# Global instance
_cleaner_instance = None

def load_plugin():
    """Entry point called by OpenShot when loading plugins."""
    global _cleaner_instance
    if _cleaner_instance is None:
        _cleaner_instance = CleanUnusedMedia()
        _cleaner_instance.initialize()
    else:
        _cleaner_instance.initialize()
    return _cleaner_instance

if OPENSHOT_AVAILABLE:
    try:
        load_plugin()
    except Exception as err:
        log.warning(f"Could not auto-start CleanUnusedMedia plugin: {err}")
