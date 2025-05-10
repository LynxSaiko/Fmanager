import os
import zipfile
import tarfile
import curses
from curses import textpad

class ArchiveExtractor:
    @staticmethod
    def extract_zip(stdscr, path, filename):
        """Handle ZIP file extraction"""
        file_path = os.path.join(path, filename)
        extract_dir = os.path.join(path, os.path.splitext(filename)[0])
        
        # Create confirmation popup
        height, width = stdscr.getmaxyx()
        popup_h = 5
        popup_w = 60
        popup = curses.newwin(popup_h, popup_w, height//2 - popup_h//2, width//2 - popup_w//2)
        popup.border()
        popup.addstr(0, 2, " Extract ZIP Archive ")
        popup.addstr(1, 2, f"File: {filename[:popup_w-10]}")
        popup.addstr(2, 2, f"To: {os.path.basename(extract_dir)[:popup_w-10]}")
        popup.addstr(3, 2, "Press Y to confirm, any key to cancel")
        popup.refresh()

        key = stdscr.getch()
        if key in [ord('y'), ord('Y')]:
            try:
                os.makedirs(extract_dir, exist_ok=True)
                with zipfile.ZipFile(file_path, 'r') as archive:
                    archive.extractall(extract_dir)
                return True, f"Extracted to {os.path.basename(extract_dir)}"
            except Exception as e:
                return False, f"Extraction failed: {str(e)}"
        return False, "Cancelled"

    @staticmethod
    def extract_tar_gz(stdscr, path, filename):
        """Handle TAR.GZ file extraction"""
        return ArchiveExtractor._extract_tar(stdscr, path, filename, 'gz')

    @staticmethod
    def extract_tar_xz(stdscr, path, filename):
        """Handle TAR.XZ file extraction"""
        return ArchiveExtractor._extract_tar(stdscr, path, filename, 'xz')

    @staticmethod
    def _extract_tar(stdscr, path, filename, mode):
        """Internal method for tar extraction"""
        file_path = os.path.join(path, filename)
        extract_dir = os.path.join(path, os.path.splitext(filename)[0].replace('.tar',''))
        ext_type = 'GZ' if mode == 'gz' else 'XZ'

        height, width = stdscr.getmaxyx()
        popup_h = 5
        popup_w = 60
        popup = curses.newwin(popup_h, popup_w, height//2 - popup_h//2, width//2 - popup_w//2)
        popup.border()
        popup.addstr(0, 2, f" Extract TAR.{ext_type} Archive ")
        popup.addstr(1, 2, f"File: {filename[:popup_w-10]}")
        popup.addstr(2, 2, f"To: {os.path.basename(extract_dir)[:popup_w-10]}")
        popup.addstr(3, 2, "Press Y to confirm, any key to cancel")
        popup.refresh()

        key = stdscr.getch()
        if key in [ord('y'), ord('Y')]:
            try:
                os.makedirs(extract_dir, exist_ok=True)
                with tarfile.open(file_path, f'r:{mode}') as archive:
                    archive.extractall(extract_dir)
                return True, f"Extracted to {os.path.basename(extract_dir)}"
            except Exception as e:
                return False, f"Extraction failed: {str(e)}"
        return False, "Cancelled"