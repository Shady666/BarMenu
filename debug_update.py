"""
Диагностика обновления окон.
"""

import win32gui
import win32con
import time

def debug_windows():
    """Показывает все окна и их состояние."""
    print("=" * 80)
    print("🔍 ДИАГНОСТИКА ОКОН ДЛЯ ОБНОВЛЕНИЯ")
    print("=" * 80)
    
    windows = []
    
    def enum_windows(hwnd, ctx):
        try:
            title = win32gui.GetWindowText(hwnd)
            class_name = win32gui.GetClassName(hwnd)
            
            if title and ('YandexBrowser' in class_name or 'Chrome' in class_name):
                # Проверяем видимость и состояние
                is_visible = win32gui.IsWindowVisible(hwnd)
                placement = win32gui.GetWindowPlacement(hwnd)
                state = placement[1]
                
                state_text = {
                    win32con.SW_SHOWMINIMIZED: "СВЕРНУТО",
                    win32con.SW_SHOWMAXIMIZED: "РАЗВЕРНУТО",
                    win32con.SW_SHOWNORMAL: "НОРМАЛЬНОЕ"
                }.get(state, f"ДРУГОЕ ({state})")
                
                windows.append({
                    'hwnd': hwnd,
                    'title': title,
                    'class': class_name,
                    'visible': is_visible,
                    'state': state,
                    'state_text': state_text
                })
        except:
            pass
        return True
    
    win32gui.EnumWindows(enum_windows, None)
    
    print(f"\n📊 Найдено окон Яндекс/Chrome: {len(windows)}")
    print("-" * 80)
    
    for i, win in enumerate(windows):
        title_short = win['title'][:80] + ("..." if len(win['title']) > 80 else "")
        print(f"{i+1:2}. [{win['class']:25}] [{win['state_text']:12}]")
        print(f"     '{title_short}'")
        print(f"     HWND: {win['hwnd']}, Видимо: {win['visible']}")
        print()
    
    # Тестируем отправку сообщений
    if windows:
        print("\n" + "=" * 80)
        print("🧪 ТЕСТИРОВАНИЕ ОТПРАВКИ СООБЩЕНИЙ")
        print("=" * 80)
        
        test_hwnd = windows[0]['hwnd']
        test_title = windows[0]['title']
        
        print(f"Тестируем окно: '{test_title[:60]}'")
        print(f"HWND: {test_hwnd}")
        
        # Тест 1: Проверяем, что окно принимает сообщения
        print("\n1. Тест приема сообщений...")
        try:
            # Отправляем простейшее сообщение
            result = win32gui.SendMessage(test_hwnd, win32con.WM_USER, 0, 0)
            print(f"   ✅ Окно приняло сообщение, результат: {result}")
        except Exception as e:
            print(f"   ❌ Ошибка: {e}")
        
        # Тест 2: Пробуем активировать
        print("\n2. Тест активации окна...")
        try:
            old_hwnd = win32gui.GetForegroundWindow()
            win32gui.SetForegroundWindow(test_hwnd)
            time.sleep(0.5)
            new_hwnd = win32gui.GetForegroundWindow()
            print(f"   ✅ Активация: {old_hwnd} -> {new_hwnd}")
            if new_hwnd != test_hwnd:
                print(f"   ⚠ Окно не стало активным! Текущее активное: {new_hwnd}")
        except Exception as e:
            print(f"   ❌ Ошибка активации: {e}")
        
        # Тест 3: Отправляем F5
        print("\n3. Тест отправки F5...")
        try:
            print(f"   Отправляем WM_KEYDOWN VK_F5...")
            win32gui.SendMessage(test_hwnd, win32con.WM_KEYDOWN, win32con.VK_F5, 0x00000001)
            time.sleep(0.05)
            print(f"   Отправляем WM_KEYUP VK_F5...")
            win32gui.SendMessage(test_hwnd, win32con.WM_KEYUP, win32con.VK_F5, 0xC0000001)
            print(f"   ✅ F5 отправлен")
        except Exception as e:
            print(f"   ❌ Ошибка F5: {e}")
        
        # Тест 4: Отправляем сообщение об обновлении напрямую
        print("\n4. Тест прямого сообщения об обновлении...")
        try:
            # WM_COMMAND с ID обновления
            # 57600 = 0xE100 = ID файлового меню "Обновить"
            result = win32gui.SendMessage(test_hwnd, win32con.WM_COMMAND, 57600, 0)
            print(f"   ✅ WM_COMMAND 57600 отправлен, результат: {result}")
        except Exception as e:
            print(f"   ❌ Ошибка WM_COMMAND: {e}")
        
        # Тест 5: PostMessage вместо SendMessage
        print("\n5. Тест PostMessage (асинхронно)...")
        try:
            win32gui.PostMessage(test_hwnd, win32con.WM_KEYDOWN, win32con.VK_F5, 0)
            win32gui.PostMessage(test_hwnd, win32con.WM_KEYUP, win32con.VK_F5, 0)
            print(f"   ✅ PostMessage F5 отправлен (асинхронно)")
        except Exception as e:
            print(f"   ❌ Ошибка PostMessage: {e}")
    
    print("\n" + "=" * 80)
    print("📋 ВЫВОДЫ:")
    print("=" * 80)
    
    if not windows:
        print("❌ Окна не найдены!")
        print("   Запустите сначала window_manager.py")
    else:
        print(f"✅ Найдено {len(windows)} окон")
        print("   Если тесты проходят, но обновление не работает,")
        print("   возможно браузер игнорирует F5 в полноэкранном режиме")
    
    input("\nНажмите Enter для выхода...")

if __name__ == "__main__":
    debug_windows()