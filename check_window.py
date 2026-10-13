import win32gui
import time

time.sleep(5)  # Дайте время браузеру открыться

def list_windows():
    windows = []
    
    def enum_handler(hwnd, ctx):
        if win32gui.IsWindowVisible(hwnd):
            title = win32gui.GetWindowText(hwnd)
            class_name = win32gui.GetClassName(hwnd)
            if title:
                windows.append((hwnd, title, class_name))
        return True
    
    win32gui.EnumWindows(enum_handler, None)
    
    print("\nВСЕ ОКНА С ЗАГОЛОВКАМИ:")
    print("=" * 100)
    for hwnd, title, class_name in sorted(windows, key=lambda x: len(x[1]), reverse=True):
        if 'Chrome' in class_name:
            print(f"[BROWSER] {class_name:25} | {title}")
        else:
            print(f"[OTHER]   {class_name:25} | {title}")

list_windows()