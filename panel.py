import os
import curses
from typing import List

class FilePanel:
    def __init__(self, path: str):
        self.path = path
        self.files: List[str] = []
        self.cursor_pos = 0
        self.scroll_offset = 0
        self.filter = ""
        self.refresh_files()

    def refresh_files(self):
        try:
            files = os.listdir(self.path)
            self.files = sorted(
                files,
                key=lambda x: (not os.path.isdir(os.path.join(self.path, x)), x.lower())
            )
            if self.filter:
                self.files = [f for f in self.files if self.filter.lower() in f.lower()]
        except PermissionError:
            self.files = ["[Permission Denied]"]

    def navigate(self, direction: int):
        if not self.files:
            return
        self.cursor_pos += direction
        if self.cursor_pos < 0:
            self.cursor_pos = len(self.files) - 1
        elif self.cursor_pos >= len(self.files):
            self.cursor_pos = 0

        if self.cursor_pos < self.scroll_offset:
            self.scroll_offset = self.cursor_pos
        elif self.cursor_pos >= self.scroll_offset + curses.LINES - 6:
            self.scroll_offset = self.cursor_pos - (curses.LINES - 6) + 1

    def get_selected(self) -> str:
        if not self.files or self.cursor_pos >= len(self.files):
            return ""
        return self.files[self.cursor_pos]

    def enter_directory(self):
        selected = self.get_selected()
        if selected and os.path.isdir(os.path.join(self.path, selected)):
            self.path = os.path.join(self.path, selected)
            self.cursor_pos = 0
            self.scroll_offset = 0
            self.refresh_files()

    def go_up(self):
        parent = os.path.dirname(self.path)
        if parent != self.path:
            self.path = parent
            self.cursor_pos = 0
            self.scroll_offset = 0
            self.refresh_files()
