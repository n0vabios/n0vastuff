import pystray
from PIL import Image
import threading
import os

class TrayIcon:
    def __init__(self, show_window_callback):
        self.show_window_callback = show_window_callback
        self.icon = None
        
    def create_icon(self):
        # Create a simple icon (you can replace with your own .ico file)
        image = Image.new('RGB', (64, 64), color='purple')
        
        menu = pystray.Menu(
            pystray.MenuItem("Show", self.show_window),
            pystray.MenuItem("Exit", self.exit_app)
        )
        
        self.icon = pystray.Icon(
            "n0va_selfbot",
            image,
            "n0va selfbot",
            menu
        )
        
    def show_window(self):
        if self.show_window_callback:
            self.show_window_callback()
            
    def exit_app(self):
        if self.icon:
            self.icon.stop()
        os._exit(0)
        
    def run(self):
        self.create_icon()
        self.icon.run() 