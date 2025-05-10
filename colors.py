import curses
import configparser
from typing import Dict, Tuple

class ColorScheme:
    def __init__(self):
        self.config = configparser.ConfigParser()
        self.config.read('colors.settings')
        self.color_defs: Dict[str, Tuple[int, int, int]] = {}
        self.init_color_pairs()

    def _hex_to_curses(self, hex_color: str) -> Tuple[int, int, int]:
        """Convert hex color to curses RGB format (0-1000 scale)"""
        hex_color = hex_color.lstrip('#')
        r = int(hex_color[0:2], 16) * 1000 // 255
        g = int(hex_color[2:4], 16) * 1000 // 255
        b = int(hex_color[4:6], 16) * 1000 // 255
        return (r, g, b)

    def init_color_pairs(self):
        """Initialize all colors and color pairs from config"""
        # First initialize all color definitions
        color_id = 100  # Starting ID for custom colors
        self.color_ids: Dict[str, int] = {}
        
        for color_name, hex_value in self.config['Colors'].items():
            rgb = self._hex_to_curses(hex_value)
            curses.init_color(color_id, *rgb)
            self.color_ids[color_name] = color_id
            color_id += 1

        # Then initialize all color pairs
        for pair_num, colors in self.config['ColorPairs'].items():
            fg_name, bg_name = map(str.strip, colors.split(','))
            curses.init_pair(
                int(pair_num),
                self.color_ids[fg_name],
                self.color_ids[bg_name]
            )

    def get(self, pair_num: int) -> int:
        """Get color pair with attributes"""
        return curses.color_pair(pair_num)
