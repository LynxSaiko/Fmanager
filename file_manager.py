import os
import curses
import subprocess
import shutil
from curses import textpad
from pathlib import Path
from panel import FilePanel
from colors import ColorScheme
from archive_extractor import ArchiveExtractor

class FileManager:
    def __init__(self, stdscr):
        self.stdscr = stdscr
        self.color_scheme = ColorScheme()
        self.left_panel = FilePanel(str(Path.home()))
        self.right_panel = FilePanel("/")
        self.active_panel = "left"
        self.search_mode = False
        self.search_query = ""
        self.message = ""
        self.message_timer = 0
        self.clipboard_path = ""
        self.clipboard_mode = ""  # "copy" or "cut"


        self.init_ui()

    def init_ui(self):
        self.stdscr.keypad(True)
        curses.curs_set(0)
        curses.use_default_colors()
        self.stdscr.clear()
        self.stdscr.refresh()

    @property
    def current_panel(self):
        return self.left_panel if self.active_panel == "left" else self.right_panel

    @property
    def inactive_panel(self):
        return self.right_panel if self.active_panel == "left" else self.left_panel

    def draw(self):
        self.stdscr.erase()
        height, width = self.stdscr.getmaxyx()

        if height < 10 or width < 40:
            self.stdscr.addstr(
                0, 0, "Terminal terlalu kecil. Perbesar dan jalankan ulang."
            )
            self.stdscr.refresh()
            curses.napms(2000)
            return

        self.draw_header(width)
        panel_width = max((width - 4) // 2, 10)
        base_panel_height = max(height - 4, 5)
        panel_height = base_panel_height - (2 if self.search_mode else 0)

        self.draw_panel(
            self.left_panel,
            2,
            1,
            panel_height,
            panel_width,
            self.active_panel == "left",
        )
        self.draw_panel(
            self.right_panel,
            2,
            panel_width + 2,
            panel_height,
            panel_width,
            self.active_panel == "right",
        )

        if self.message and self.message_timer > 0:
            self.stdscr.addstr(
                height - 1,
                0,
                self.message.ljust(width - 1),
                curses.color_pair(8 if "Error" in self.message else 9),
            )
            self.message_timer -= 1
        self.stdscr.refresh()

    def draw_header(self, width):
        header = "[ Hack The Planet ]"
        self.stdscr.addstr(
            0, 0, header.ljust(width), curses.color_pair(10) | curses.A_BOLD
        )

    def draw_panel(self, panel, y, x, height, width, active):
        if active and self.search_mode:
            path_line = panel.path
            if len(path_line) > width - 4:
                path_line = "..." + path_line[-(width - 7) :]
            self.stdscr.addstr(
                y, x + 2, path_line.ljust(width - 3), curses.color_pair(3)
            )

            search_line = f"[ /: {self.search_query}"
            self.stdscr.addstr(
                y + 1,
                x + 2,
                search_line.ljust(width - 3),
                curses.color_pair(11) | curses.A_BOLD,
            )
            panel_y = y + 2
        else:
            panel_y = y

        border_color = curses.color_pair(2) if active else curses.color_pair(3)
        self.stdscr.attron(border_color)
        try:
            textpad.rectangle(self.stdscr, panel_y, x, panel_y + height, x + width)
        except curses.error:
            pass

        full_path = panel.path
        if len(full_path) > width - 4:
            full_path = "..." + full_path[-(width - 7) :]
        self.stdscr.addstr(panel_y, x + 2, f" {full_path} ")
        self.stdscr.attroff(border_color)

        visible_items = min(len(panel.files), height - 2)
        for i in range(visible_items):
            idx = i + panel.scroll_offset
            if idx >= len(panel.files):
                break
            item = panel.files[idx]
            is_selected = i == panel.cursor_pos - panel.scroll_offset
            full_path = os.path.join(panel.path, item)
            is_dir = os.path.isdir(full_path)
            if is_dir:
                size_str = "<DIR>"
            else:
                try:
                    size_str = f"{os.path.getsize(full_path)} B"
                except (PermissionError, FileNotFoundError, OSError):
                    size_str = "N/A"
            display_name = (
                item if len(item) <= width - 20 else item[: width - 23] + "..."
            )
            line = f"{display_name:<{width - 15}} {size_str:>10}"
            color = curses.color_pair(
                7
                if is_selected and is_dir
                else 5 if is_selected else 6 if is_dir else 1
            )
            try:
                self.stdscr.addstr(panel_y + 1 + i, x + 2, line, color)
            except curses.error:
                pass

    def handle_input(self):

        key = self.stdscr.getch()
        # Convert to lowercase untuk handle case-insensitive
        if isinstance(key, int) and 97 <= key <= 122:  # a-z

            key = key - 32 if curses.keyname(key) == b"R" else key  # Handle Shift
        if self.search_mode:
            self.handle_search_input(key)
            return True

        actions = {
            curses.KEY_UP: lambda: self.current_panel.navigate(-1),
            curses.KEY_DOWN: lambda: self.current_panel.navigate(1),
            curses.KEY_LEFT: self.current_panel.go_up,
            curses.KEY_RIGHT: self.current_panel.enter_directory,
            curses.KEY_F6: self.copy_file,
            curses.KEY_F7: self.cut_file,
            curses.KEY_F8: self.paste_file,
            curses.KEY_F11: self.view_mounts,
           
            10: self.execute_or_enter,
            9: self.toggle_panel,
            ord("/"): self.start_search,
            ord("r"): self.rename_file,
            ord("R"): self.rename_file,  # Support untuk Shift+R
            ord('z'): self.extract_zip,      # z for zip
            ord('g'): self.extract_tar_gz,   # g for gz
            ord('x'): self.extract_tar_xz,   # x for xz
            curses.KEY_F5: self.delete_file,
            curses.KEY_F10: self.exit_program,
        }

        action = actions.get(key)
        if action:
            result = action()
            return result if isinstance(result, bool) else True

        return True

    def execute_or_enter(self):

        selected = self.current_panel.get_selected()
        if not selected:
            return

        full_path = os.path.join(self.current_panel.path, selected)

        # Make file executable if needed
        if not os.path.isdir(full_path) and not os.access(full_path, os.X_OK):
            os.chmod(full_path, os.stat(full_path).st_mode | 0o111)

        if os.path.isdir(full_path):
            self.current_panel.enter_directory()
        else:
            try:
                ext = os.path.splitext(full_path)[1].lower()

                if ext == ".py":
                    # Execute Python files with terminal staying open
                    subprocess.Popen(
                        [
                            "urxvt",
                            "-e",
                            "bash",
                            "-c",
                            f'python3 "{full_path}"; exec bash',
                        ],
                        start_new_session=True,
                    )
                elif ext == ".sh":
                    # Execute shell scripts with terminal staying open
                    subprocess.Popen(
                        ["urxvt", "-e", "bash", "-c", f'bash "{full_path}"; exec bash'],
                        start_new_session=True,
                    )
                elif ext in [".txt", ".md"]:
                    subprocess.Popen(["xdg-open", full_path])
                elif ext in [".jpg", ".png", ".jpeg", ".webp", ".gif", ".pdf"]:
                    subprocess.Popen(["xdg-open", full_path])
                else:
                    # For other executables
                    subprocess.Popen(
                        ["urxvt", "-e", "bash", "-c", f'"{full_path}"; exec bash'],
                        start_new_session=True,
                    )

            except Exception as e:
                self.show_message(f"Error executing file: {str(e)}", 5)

    def toggle_panel(self):
        self.active_panel = "right" if self.active_panel == "left" else "left"

    def start_search(self):
        self.search_mode = True
        self.search_query = ""

    def exit_program(self):
        return False

    def handle_search_input(self, key):
        if key == 27:
            self.search_mode = False
            self.current_panel.filter = ""
            self.current_panel.refresh_files()
        elif key in [curses.KEY_BACKSPACE, 127]:
            self.search_query = self.search_query[:-1]
            self.current_panel.filter = self.search_query
            self.current_panel.refresh_files()
        elif key in [curses.KEY_ENTER, 10]:
            self.search_mode = False
        elif 32 <= key <= 126:
            self.search_query += chr(key)
            self.current_panel.filter = self.search_query
            self.current_panel.refresh_files()

    def show_message(self, message: str, duration: int = 3):
        self.message = message
        self.message_timer = duration

    def rename_file(self):
        selected = self.current_panel.get_selected()
        if not selected or selected == "[Permission Denied]":
            self.show_message("Invalid selection", 2)
            return

        old_path = os.path.join(self.current_panel.path, selected)
        height, width = self.stdscr.getmaxyx()

        # Setup popup window
        popup_h = 5
        popup_w = min(50, width - 10)
        popup_y = max(1, height // 2 - popup_h // 2)
        popup_x = max(1, width // 2 - popup_w // 2)

        popup = curses.newwin(popup_h, popup_w, popup_y, popup_x)
        popup.border()
        popup.addstr(0, 2, " Rename File ")
        popup.addstr(1, 2, f"Original: {selected[:popup_w-12]}")
        popup.addstr(2, 2, "New name: ")
        popup.addstr(3, 2, "Enter:Confirm  ESC:Cancel")
        popup.refresh()

        # Setup input box - KEY CHANGE: Disable echo()
        input_width = min(40, popup_w - 12)
        input_win = curses.newwin(1, input_width, popup_y + 2, popup_x + 11)
        input_win.addstr(0, 0, selected[:input_width])

        curses.curs_set(1)  # Enable cursor
        curses.noecho()  # KEY FIX: Disable echo to prevent double chars

        try:
            box = textpad.Textbox(input_win)
            new_name = box.edit(self.validate_rename_input).strip()

            if new_name and new_name != selected:
                new_path = os.path.join(self.current_panel.path, new_name)
                try:
                    os.rename(old_path, new_path)
                    self.show_message(f"Renamed to '{new_name[:20]}'", 3)
                    self.current_panel.refresh_files()
                except OSError as e:
                    self.show_message(f"Error: {e.strerror}", 5)
        finally:
            curses.curs_set(0)
            self.stdscr.touchwin()
            self.stdscr.refresh()

    def validate_rename_input(self, key):
        """Validator that prevents double characters"""
        # Control keys
        if key == 27:
            return 7  # ESC
        if key in (10, 13):
            return 7  # Enter
        if key in (curses.KEY_BACKSPACE, 127, 8):
            return curses.KEY_BACKSPACE

        # Printable characters (no echo so no doubling)
        if 32 <= key <= 126:
            char = chr(key)
            if char.isalnum() or char in (" ", ".", "-", "_"):
                return key
        return 0

    def delete_file(self):
        selected = self.current_panel.get_selected()
        if not selected:
            self.show_message("No file selected", 2)
            return

        path = os.path.join(self.current_panel.path, selected)
        height, width = self.stdscr.getmaxyx()

        # Create confirmation popup
        popup_h = 5
        popup_w = 50
        popup = curses.newwin(
            popup_h, popup_w, height // 2 - popup_h // 2, width // 2 - popup_w // 2
        )
        popup.border()
        popup.addstr(0, 2, " Confirm Delete ")
        popup.addstr(1, 2, f"Delete '{selected[:30]}'?")
        popup.addstr(2, 2, "This action cannot be undone!")
        popup.addstr(3, 2, "Press Y to confirm, any key to cancel")
        popup.refresh()

        # Get confirmation
        key = self.stdscr.getch()

        if key in [ord("y"), ord("Y")]:
            try:
                if os.path.isdir(path):
                    shutil.rmtree(path)
                else:
                    os.remove(path)
                self.show_message(f"Deleted '{selected}'", 3)
                self.current_panel.refresh_files()
            except Exception as e:
                self.show_message(f"Error deleting: {str(e)}", 5)

    def copy_file(self):
        """Copy selected file to clipboard"""
        selected = self.current_panel.get_selected()
        if not selected or selected == "[Permission Denied]":
            self.show_message("No file selected", 2)
            return
        
        self.clipboard_path = os.path.join(self.current_panel.path, selected)
        self.clipboard_mode = "copy"
        self.show_message(f"Copied: {selected}", 3)

    def cut_file(self):
        """Cut selected file to clipboard"""
        selected = self.current_panel.get_selected()
        if not selected or selected == "[Permission Denied]":
            self.show_message("No file selected", 2)
            return
        
        self.clipboard_path = os.path.join(self.current_panel.path, selected)
        self.clipboard_mode = "cut"
        self.show_message(f"Cut: {selected}", 3)

    def paste_file(self):
        """Paste file from clipboard"""
        if not self.clipboard_path:
            self.show_message("Clipboard empty", 2)
            return
        
        dest_dir = self.current_panel.path
        filename = os.path.basename(self.clipboard_path)
        dest_path = os.path.join(dest_dir, filename)
        
        try:
            if self.clipboard_mode == "copy":
                if os.path.isdir(self.clipboard_path):
                    shutil.copytree(self.clipboard_path, dest_path)
                else:
                    shutil.copy2(self.clipboard_path, dest_path)
                self.show_message(f"Copied to: {filename}", 3)
            elif self.clipboard_mode == "cut":
                shutil.move(self.clipboard_path, dest_path)
                self.show_message(f"Moved to: {filename}", 3)
                self.clipboard_path = ""  # Clear clipboard after move
            
            self.current_panel.refresh_files()
        except Exception as e:
            self.show_message(f"Paste error: {str(e)}", 5)
    
    def view_mounts(self):
        paths = []
        for base in ["/mnt", "/media"]:
            if os.path.exists(base):
                for entry in os.listdir(base):
                    full = os.path.join(base, entry)
                    if os.path.ismount(full):
                        paths.append(full)

        height, width = self.stdscr.getmaxyx()
        popup_h = min(20, height - 4)
        popup_w = min(70, width - 4)
        popup_y = max(1, (height - popup_h) // 2)
        popup_x = max(1, (width - popup_w) // 2)

        popup = curses.newwin(popup_h, popup_w, popup_y, popup_x)
        popup.border()
        popup.addstr(0, 2, " Mounted in /mnt and /media ")

        if not paths:
            popup.addstr(2, 2, "No mounts found in /mnt or /media.")
        else:
            for i, path in enumerate(paths[:popup_h - 3]):
                popup.addstr(i + 1, 2, path[:popup_w - 4])

        popup.addstr(popup_h - 2, 2, "Press any key to close")
        popup.refresh()
        self.stdscr.getch()
        self.stdscr.touchwin()
        self.stdscr.refresh()

    def extract_zip(self):
        selected = self.current_panel.get_selected()
        if not selected or not selected.endswith('.zip'):
            self.show_message("Select a .zip file first", 2)
            return
        
        success, message = ArchiveExtractor.extract_zip(
            self.stdscr, 
            self.current_panel.path, 
            selected
        )
        self.show_message(message, 3)
        if success:
            self.current_panel.refresh_files()

    def extract_tar_gz(self):
        selected = self.current_panel.get_selected()
        if not selected or not (selected.endswith('.tar.gz') or selected.endswith('.tgz')):
            self.show_message("Select a .tar.gz or .tgz file first", 2)
            return
        
        success, message = ArchiveExtractor.extract_tar_gz(
            self.stdscr,
            self.current_panel.path,
            selected
        )
        self.show_message(message, 3)
        if success:
            self.current_panel.refresh_files()

    def extract_tar_xz(self):
        selected = self.current_panel.get_selected()
        if not selected or not selected.endswith('.tar.xz'):
            self.show_message("Select a .tar.xz file first", 2)
            return
        
        success, message = ArchiveExtractor.extract_tar_xz(
            self.stdscr,
            self.current_panel.path,
            selected
        )
        self.show_message(message, 3)
        if success:
            self.current_panel.refresh_files()

    def run(self):
        """Main application loop"""
        running = True
        while running:
            self.draw()
            running = self.handle_input()