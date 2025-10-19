import curses
from file_manager import FileManager

def main(stdscr):
    if curses.has_colors():
        curses.start_color()
    manager = FileManager(stdscr)
    manager.run()

if __name__ == "__main__":
    curses.wrapper(main)
