"""
Модуль для обновления HTML страниц в Яндекс Браузере.
Активирует окна перед отправкой Ctrl+F5.
"""

import win32gui
import win32con
import time
import sys
import ctypes

def activate_and_refresh(hwnd, title):
    """
    Активирует окно и отправляет Ctrl+F5.
    Возвращает True если успешно.
    """
    try:
        print(f"\n  🔄 Окно: '{title[:50]}'")
        print(f"     HWND: {hwnd}")
        
        # 1. Восстанавливаем окно (на случай если свернуто)
        win32gui.ShowWindow(hwnd, win32con.SW_RESTORE)
        time.sleep(0.2)
        
        # 2. Пробуем несколько методов активации
        print(f"    1. Активация окна...")
        
        # Метод 1: SetForegroundWindow
        win32gui.SetForegroundWindow(hwnd)
        time.sleep(0.3)
        
        # Проверяем, стало ли окно активным
        active_hwnd = win32gui.GetForegroundWindow()
        
        if active_hwnd == hwnd:
            print(f"       ✅ Окно активировано (HWND: {hwnd})")
        else:
            print(f"       ⚠ Активно другое окно (HWND: {active_hwnd})")
            print(f"       Пробуем альтернативные методы...")
            
            # Метод 2: ShowWindow с SW_SHOW
            win32gui.ShowWindow(hwnd, win32con.SW_SHOW)
            time.sleep(0.2)
            
            # Метод 3: SetWindowPos
            win32gui.SetWindowPos(hwnd, win32con.HWND_TOPMOST, 0, 0, 0, 0,
                                 win32con.SWP_NOMOVE | win32con.SWP_NOSIZE)
            win32gui.SetWindowPos(hwnd, win32con.HWND_NOTOPMOST, 0, 0, 0, 0,
                                 win32con.SWP_NOMOVE | win32con.SWP_NOSIZE)
            
            # Снова проверяем
            active_hwnd = win32gui.GetForegroundWindow()
            if active_hwnd == hwnd:
                print(f"       ✅ Окно активировано альтернативным методом")
            else:
                print(f"       ❌ Не удалось активировать окно")
                print(f"       Пробуем отправить Ctrl+F5 без активации...")
        
        # 3. Отправляем Ctrl+F5
        print(f"    2. Отправка Ctrl+F5...")
        
        # Небольшая пауза для гарантии, что окно готово
        time.sleep(0.5)
        
        # KEYDOWN для Ctrl
        ctypes.windll.user32.keybd_event(win32con.VK_CONTROL, 0, 0, 0)
        time.sleep(0.1)
        
        # KEYDOWN для F5
        ctypes.windll.user32.keybd_event(win32con.VK_F5, 0, 0, 0)
        time.sleep(0.1)
        
        # KEYUP для F5
        ctypes.windll.user32.keybd_event(win32con.VK_F5, 0, 2, 0)
        time.sleep(0.1)
        
        # KEYUP для Ctrl
        ctypes.windll.user32.keybd_event(win32con.VK_CONTROL, 0, 2, 0)
        
        print(f"       ✅ Ctrl+F5 отправлен")
        
        # 4. Дополнительно: Shift+F5 (на всякий случай)
        time.sleep(0.2)
        print(f"    3. Отправка Shift+F5...")
        
        ctypes.windll.user32.keybd_event(win32con.VK_SHIFT, 0, 0, 0)
        ctypes.windll.user32.keybd_event(win32con.VK_F5, 0, 0, 0)
        time.sleep(0.1)
        ctypes.windll.user32.keybd_event(win32con.VK_F5, 0, 2, 0)
        ctypes.windll.user32.keybd_event(win32con.VK_SHIFT, 0, 2, 0)
        
        print(f"       ✅ Shift+F5 отправлен")
        
        # 5. WM_COMMAND как запасной вариант
        time.sleep(0.2)
        print(f"    4. Прямая команда обновления...")
        
        try:
            # ID команды "Обновить" в Яндекс Браузере
            result = win32gui.SendMessage(hwnd, win32con.WM_COMMAND, 57600, 0)
            print(f"       ✅ Команда 0xE100 отправлена")
        except:
            try:
                # Альтернативный ID
                result = win32gui.SendMessage(hwnd, win32con.WM_COMMAND, 0xE120, 0)
                print(f"       ✅ Команда 0xE120 отправлена")
            except:
                print(f"       ⚠ Не удалось отправить команду")
        
        return True
        
    except Exception as e:
        print(f"       ❌ Ошибка: {e}")
        return False

def main():
    """
    Основная функция обновления.
    """
    print("=" * 70)
    print("🚀 ОБНОВЛЕНИЕ HTML СТРАНИЦ В ЯНДЕКС БРАУЗЕРЕ")
    print("=" * 70)
    print("Активирует окна и отправляет Ctrl+F5")
    print("=" * 70)
    
    if sys.platform != "win32":
        print("❌ Только для Windows!")
        return
    
    # Находим окна Яндекс Браузера
    print("\n🔍 Поиск окон Яндекс Браузера...")
    
    yandex_windows = []
    
    def find_yandex_windows(hwnd, ctx):
        try:
            title = win32gui.GetWindowText(hwnd)
            class_name = win32gui.GetClassName(hwnd)
            
            # Ищем окна Яндекс
            if 'YandexBrowser_WidgetWin_' in class_name and title:
                if ('яндекс браузер' in title.lower() or 
                    len(title.strip()) > 5):
                    yandex_windows.append({
                        'hwnd': hwnd,
                        'title': title,
                        'class': class_name
                    })
        except:
            pass
        return True
    
    win32gui.EnumWindows(find_yandex_windows, None)
    
    if not yandex_windows:
        print("❌ Окна Яндекс Браузера не найдены!")
        print("   Запустите сначала: python window_manager.py")
        time.sleep(2)
        return
    
    print(f"✅ Найдено {len(yandex_windows)} окон")
    
    # Показываем найденные окна
    print("\n📋 НАЙДЕННЫЕ ОКНА:")
    for i, win in enumerate(yandex_windows):
        print(f"  {i+1}. '{win['title'][:60]}'")
        print(f"      Класс: {win['class']}, HWND: {win['hwnd']}")
    
    # Обновляем каждое окно
    print("\n⚡ НАЧИНАЕМ ОБНОВЛЕНИЕ...")
    print("=" * 50)
    
    success_count = 0
    
    for i, win in enumerate(yandex_windows):
        print(f"\n📝 Окно {i+1} из {len(yandex_windows)}:")
        
        if activate_and_refresh(win['hwnd'], win['title']):
            success_count += 1
            print(f"\n   ✅ УСПЕХ - окно должно обновиться")
        else:
            print(f"\n   ❌ НЕ УДАЛОСЬ")
        
        # Пауза между окнами
        if i < len(yandex_windows) - 1:
            time.sleep(2)
    
    # Итоги
    print("\n" + "=" * 70)
    print("📊 РЕЗУЛЬТАТЫ")
    print("=" * 70)
    print(f"   Всего окон: {len(yandex_windows)}")
    print(f"   Успешно обработано: {success_count}")
    
    if success_count > 0:
        print(f"\n✅ {success_count} окон получили команды обновления")
        print("   Если страницы не обновились, попробуйте:")
        print("   1. Вручную нажать Ctrl+F5 в каждом окне")
        print("   2. Убедиться, что HTML файлы были пересозданы")
        print("   3. Проверить, что окна не блокируют клавиши")
    else:
        print(f"\n❌ Ни одно окно не обновлено")
    
    print("\n" + "=" * 70)
    print("💡 Рекомендация: После запуска update.py,")
    print("   быстро переключитесь на окно браузера")
    print("   (Alt+Tab) и нажмите Ctrl+F5 вручную")
    print("=" * 70)
    
    time.sleep(3)

if __name__ == "__main__":
    main()