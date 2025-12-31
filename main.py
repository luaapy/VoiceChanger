import sys
import logging
from ui.main_window import MainWindow

def main():
    try:
        app = MainWindow()
        app.mainloop()
    except Exception as e:
        logging.critical(f"Application crashed: {e}")
        # In case GUI fails to start
        print(f"CRITICAL ERROR: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
