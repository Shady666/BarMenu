"""
Модуль для управления окнами и запуска HTML файлов на мониторах.
Требует установки: pip install pywin32
Поддерживает конфигурационный файл monitor_config.json для ручного распределения окон.
"""

import win32gui
import win32con
import time
import ctypes
import subprocess
import os
import sys
import re
import json
from ctypes import wintypes, Structure, c_long, c_ulong

# Определяем структуры
class RECT(Structure):
    _fields_ = [
        ('left', c_long),
        ('top', c_long),
        ('right', c_long),
        ('bottom', c_long)
    ]

class MONITORINFO(Structure):
    _fields_ = [
        ('cbSize', c_ulong),
        ('rcMonitor', RECT),
        ('rcWork', RECT),
        ('dwFlags', c_ulong)
    ]

def get_monitors_info():
    """
    Получение информации о мониторах.
    """
    monitors = []
    
    def callback(hmonitor, hdc, rect, data):
        try:
            info = MONITORINFO()
            info.cbSize = ctypes.sizeof(MONITORINFO)
            
            # Используем GetMonitorInfoA для совместимости
            if ctypes.windll.user32.GetMonitorInfoA(hmonitor, ctypes.byref(info)):
                monitor = {
                    'handle': hmonitor,
                    'left': info.rcMonitor.left,
                    'top': info.rcMonitor.top,
                    'right': info.rcMonitor.right,
                    'bottom': info.rcMonitor.bottom,
                    'width': info.rcMonitor.right - info.rcMonitor.left,
                    'height': info.rcMonitor.bottom - info.rcMonitor.top,
                    'is_primary': bool(info.dwFlags & 1)
                }
                monitors.append(monitor)
        except Exception as e:
            print(f"    Ошибка при получении информации о мониторе: {e}")
        return 1
    
    # Используем правильный тип для callback
    MonitorEnumProc = ctypes.WINFUNCTYPE(
        ctypes.c_int,
        wintypes.HMONITOR,
        wintypes.HDC,
        ctypes.POINTER(RECT),
        wintypes.LPARAM
    )
    
    callback_func = MonitorEnumProc(callback)
    
    ctypes.windll.user32.EnumDisplayMonitors(
        0, 
        0, 
        callback_func, 
        0
    )
    
    if not monitors:
        print("  Не удалось определить мониторы через Windows API")
        print("  Используется конфигурация по умолчанию для 2 мониторов")
        # Конфигурация по умолчанию
        monitors = [
            {
                'left': 0,
                'top': 0,
                'width': 1920,
                'height': 1080,
                'is_primary': True
            },
            {
                'left': 1920,
                'top': 0,
                'width': 1920,
                'height': 1080,
                'is_primary': False
            }
        ]
    
    # Сортируем слева направо
    monitors.sort(key=lambda m: m['left'])
    
    print(f"  Найдено мониторов: {len(monitors)}")
    for i, m in enumerate(monitors):
        status = "ОСНОВНОЙ" if m.get('is_primary', False) else "ДОПОЛНИТЕЛЬНЫЙ"
        print(f"    Монитор {i+1}: {m['width']}x{m['height']} на позиции {m['left']},{m['top']} ({status})")
    
    return monitors

def load_monitor_config():
    """
    Загружает конфигурацию распределения окон из файла.
    Возвращает словарь с конфигурацией или None, если файла нет.
    """
    config_file = "monitor_config.json"
    
    if not os.path.exists(config_file):
        print("  ⓘ Конфигурационный файл не найден, используется автоматическое распределение")
        return None
    
    try:
        with open(config_file, 'r', encoding='utf-8') as f:
            config = json.load(f)
        
        print(f"  ✓ Загружена конфигурация из {config_file}")
        return config
    except json.JSONDecodeError as e:
        print(f"  ✗ Ошибка формата JSON в {config_file}: {e}")
        return None
    except Exception as e:
        print(f"  ✗ Ошибка загрузки конфигурации: {e}")
        return None

def get_monitor_mapping(html_files, all_monitors, config):
    """
    Определяет, на какой монитор разместить каждое окно.
    Возвращает список с номерами мониторов для каждого HTML файла.
    """
    mapping = []
    
    # Если есть конфигурация и в ней указано mapping
    if config and 'mapping' in config:
        print("\n  📋 ИСПОЛЬЗУЕТСЯ КОНФИГУРАЦИОННОЕ РАСПРЕДЕЛЕНИЕ:")
        
        # Создаем словарь для быстрого поиска: имя файла -> номер монитора (0-based)
        config_map = {}
        for item in config['mapping']:
            html_name = item.get('html_file', '')
            monitor_num = item.get('monitor', 1)  # По умолчанию монитор 1
            
            if html_name.endswith('.html'):
                config_map[html_name] = monitor_num - 1  # Конвертируем в 0-based
            else:
                # Если указано без расширения, добавляем .html
                config_map[html_name + '.html'] = monitor_num - 1
        
        # Распределяем файлы согласно конфигурации
        for html_file in html_files:
            filename = html_file['name']
            
            if filename in config_map:
                monitor_idx = config_map[filename]
                
                if 0 <= monitor_idx < len(all_monitors):
                    mapping.append(monitor_idx)
                    print(f"    {filename:20} → Монитор {monitor_idx + 1} (из конфига)")
                else:
                    print(f"    ⚠ {filename:20}: указан монитор {monitor_idx + 1}, но доступно только {len(all_monitors)}")
                    # Используем циклическое распределение
                    mapping.append(len(mapping) % len(all_monitors))
            else:
                # Файла нет в конфиге - используем последовательное распределение
                mapping.append(len(mapping) % len(all_monitors))
                print(f"    {filename:20} → Монитор {mapping[-1] + 1} (авто)")
        
        return mapping
    
    # Если конфига нет или в нем нет mapping
    print("\n  🔄 ИСПОЛЬЗУЕТСЯ АВТОМАТИЧЕСКОЕ РАСПРЕДЕЛЕНИЕ:")
    
    # Проверяем, есть ли стратегия в конфиге
    strategy = 'sequential'
    if config and 'strategy' in config:
        strategy = config['strategy']
    
    if strategy == 'reverse':
        print("  Стратегия: обратный порядок")
        # Обратный порядок: последний файл на первый монитор
        return [min(i, len(all_monitors)-1) for i in range(len(html_files)-1, -1, -1)]
    
    elif strategy == 'primary_first':
        print("  Стратегия: сначала основной монитор")
        # Основной монитор получает больше файлов
        mapping = []
        for i in range(len(html_files)):
            if i < len(all_monitors):
                # Первые файлы на отдельные мониторы
                mapping.append(i)
            else:
                # Остальные файлы на основной монитор
                primary_idx = next((i for i, m in enumerate(all_monitors) if m['is_primary']), 0)
                mapping.append(primary_idx)
        return mapping
    
    else:  # 'sequential' или по умолчанию
        print("  Стратегия: последовательное распределение")
        # Простое циклическое распределение
        return [i % len(all_monitors) for i in range(len(html_files))]

def find_yandex_executable():
    """
    Ищет исполняемый файл Яндекс Браузера на компьютере.
    """
    yandex_paths = [
        r"C:\Users\%USERNAME%\AppData\Local\Yandex\YandexBrowser\Application\browser.exe",
        r"C:\Program Files\Yandex\YandexBrowser\Application\browser.exe",
        r"C:\Program Files (x86)\Yandex\YandexBrowser\Application\browser.exe",
        os.path.expandvars(r"%LOCALAPPDATA%\Yandex\YandexBrowser\Application\browser.exe"),
    ]
    
    for path in yandex_paths:
        expanded_path = os.path.expandvars(path)
        if os.path.exists(expanded_path):
            return expanded_path
    
    try:
        # Пробуем найти через реестр
        import winreg
        try:
            key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, 
                                r"SOFTWARE\Microsoft\Windows\CurrentVersion\App Paths\browser.exe")
            path, _ = winreg.QueryValueEx(key, "")
            winreg.CloseKey(key)
            if os.path.exists(path):
                return path
        except:
            pass
        
        # Пробуем через where
        result = subprocess.run(
            ["where", "browser.exe"],
            capture_output=True,
            text=True,
            shell=True
        )
        if result.returncode == 0:
            paths = result.stdout.strip().split('\n')
            for path in paths:
                if "yandex" in path.lower():
                    return path
    except Exception:
        pass
    
    # Проверяем, есть ли браузер в PATH
    try:
        result = subprocess.run(
            ["browser.exe", "--version"],
            capture_output=True,
            text=True,
            shell=True
        )
        if result.returncode == 0:
            return "browser.exe"
    except:
        pass
    
    return None

def find_html_files():
    """
    Ищет HTML файлы в текущей директории.
    """
    html_files = []
    current_dir = os.path.dirname(os.path.abspath(__file__))
    
    for file in os.listdir(current_dir):
        if file.endswith('.html') and not file.startswith('~'):
            file_path = os.path.join(current_dir, file)
            file_url = "file:///" + file_path.replace('\\', '/')
            html_files.append({
                'name': file,
                'path': file_path,
                'sheet': os.path.splitext(file)[0],
                'url': file_url
            })
    
    return sorted(html_files, key=lambda x: x['name'])

def wait_and_position_window(process_pid, monitor_index, all_monitors, window_title_part):
    """
    Ищет окно по части заголовка (названию HTML файла).
    """
    print(f"    Поиск окна с названием: '{window_title_part}'...")
    
    # Даем больше времени на загрузку окна - HTML должен полностью загрузиться
    time.sleep(7)
    
    # Ищем окно по части заголовка
    target_hwnd = None
    found_windows = []  # Будет хранить (hwnd, title, match_type)
    
    def find_window_by_title(hwnd, ctx):
        nonlocal found_windows
        try:
            if win32gui.IsWindowVisible(hwnd):
                title = win32gui.GetWindowText(hwnd)
                class_name = win32gui.GetClassName(hwnd)
                
                # Ищем окна Яндекс Браузера по ЕГО классу окна
                # Яндекс использует YandexBrowser_WidgetWin_*, а Chrome использует Chrome_WidgetWin_*
                is_yandex_window = 'YandexBrowser_WidgetWin_' in class_name
                is_chrome_window = 'Chrome_WidgetWin_' in class_name
                
                if (is_yandex_window or is_chrome_window) and title:
                    # ВАЖНО: Яндексовые окна с файлами имеют заголовки вида "1: Бар — Яндекс Браузер"
                    
                    # 1. ПРИОРИТЕТ: Точное совпадение с названием файла
                    if window_title_part.lower() in title.lower():
                        found_windows.append((hwnd, title, 'exact_match'))
                        print(f"      Точное совпадение: '{title}'")
                        return True
                    
                    # 2. Проверяем яндексовый формат: "1: Бар — Яндекс Браузер"
                    #    или "2: Кухня — Яндекс Браузер"
                    elif 'яндекс браузер' in title.lower():
                        # Извлекаем название между ":" и "—"
                        match = re.search(r':\s*(.*?)\s*—', title)
                        if match:
                            name_in_title = match.group(1).strip()
                            if window_title_part.lower() == name_in_title.lower():
                                found_windows.append((hwnd, title, 'yandex_format'))
                                print(f"      Яндекс формат: '{title}'")
                    
                    # 3. Проверяем, содержит ли заголовок путь к файлу (file:///)
                    elif 'file:///' in title.lower():
                        if window_title_part.lower() in title.lower():
                            found_windows.append((hwnd, title, 'file_match'))
                            print(f"      Совпадение по файлу: '{title}'")
                    
                    # 4. Запасной вариант: окна Яндекс Браузера с цифрой в начале
                    #    (яндекс нумерует окна: "1: ...", "2: ...")
                    elif is_yandex_window and re.match(r'^\d+:', title):
                        found_windows.append((hwnd, title, 'yandex_numbered'))
                        print(f"      Яндекс нумерованное окно: '{title}'")
                        
        except Exception as e:
            # Для отладки можно включить вывод ошибок
            # print(f"      Ошибка: {e}")
            pass
        return True
    
    # Выполняем поиск окон
    win32gui.EnumWindows(find_window_by_title, None)
    
    print(f"    Найдено кандидатов: {len(found_windows)}")
    
    # ВЫБОР ПРАВИЛЬНОГО ОКНА
    if found_windows:
        # НОВЫЙ ПРИОРИТЕТ: Яндекс-формат самый важный!
        priority_order = {
            'exact_match': 0,      # "Бар" в любом месте заголовка
            'yandex_format': 1,    # "1: Бар — Яндекс Браузер"
            'yandex_numbered': 2,  # "1: ..." (яндекс окно)
            'file_match': 3,       # file:/// в заголовке
            'browser_window': 4    # любое другое окно браузера
        }
        found_windows.sort(key=lambda x: priority_order.get(x[2], 99))
        
        # Берем лучшее совпадение
        target_hwnd, title, match_type = found_windows[0]
        print(f"    Выбрано окно ({match_type}): '{title}'")
        
        # ОБНОВЛЕННАЯ фильтрация подозрительных окон
        # Яндексовые окна НЕ должны фильтроваться!
        is_yandex_window = 'YandexBrowser_WidgetWin_' in win32gui.GetClassName(target_hwnd)
        
        if not is_yandex_window:  # Только НЕ яндексовые окна проверяем
            suspicious_keywords = ['visual studio', 'vscode', 'opera', 'spotify', 'discord', 'battle.net', ' - ', '—']
            for keyword in suspicious_keywords:
                if keyword.lower() in title.lower():
                    print(f"    ⚠  Подозрительное не-яндекс окно: '{keyword}'")
                    # Ищем яндексовое окно вместо этого
                    for hwnd, alt_title, alt_type in found_windows[1:]:
                        if 'YandexBrowser_WidgetWin_' in win32gui.GetClassName(hwnd):
                            target_hwnd, title, match_type = hwnd, alt_title, alt_type
                            print(f"    Взято яндекс окно вместо: '{alt_title[:80]}'")
                            break
                    break
                    
    else:
        print(f"    ✗ Не найдено ни одного подходящего окна с '{window_title_part}'")
        
        # РЕЗЕРВНЫЙ ВАРИАНТ: Получаем окно по PID процесса (если все еще актуально)
        try:
            import win32process
            def find_by_pid(hwnd, ctx):
                nonlocal target_hwnd
                try:
                    _, window_pid = win32process.GetWindowThreadProcessId(hwnd)
                    if window_pid == process_pid:
                        target_hwnd = hwnd
                        return False
                except:
                    pass
                return True
            
            win32gui.EnumWindows(find_by_pid, None)
            
            if target_hwnd:
                title = win32gui.GetWindowText(target_hwnd)
                print(f"    Найдено по PID {process_pid}: '{title}'")
            else:
                print(f"    Не найдено окно по PID {process_pid}")
                return False
                
        except Exception as e:
            print(f"    Ошибка поиска по PID: {e}")
            return False
    
    if not target_hwnd:
        print(f"    ✗ Не удалось найти целевое окно")
        return False
    
    # Проверяем индекс монитора
    if monitor_index >= len(all_monitors):
        print(f"    Ошибка: монитор #{monitor_index} не существует")
        return False
    
    monitor = all_monitors[monitor_index]
    
    # Используем физические координаты
    monitor_left = monitor['left']
    monitor_top = monitor['top']
    monitor_right = monitor['right']
    monitor_bottom = monitor['bottom']
    
    physical_width = monitor_right - monitor_left
    physical_height = monitor_bottom - monitor_top
    
    print(f"    Перемещение на монитор {monitor_index+1}")
    print(f"    Координаты: ({monitor_left}, {monitor_top})")
    print(f"    Разрешение: {physical_width}x{physical_height}")
    
    try:
        # 1. Восстанавливаем окно (если оно свернуто/развернуто)
        win32gui.ShowWindow(target_hwnd, win32con.SW_RESTORE)
        time.sleep(0.5)
        
        # 2. Перемещаем на нужный монитор
        win32gui.SetWindowPos(
            target_hwnd,
            win32con.HWND_TOP,
            monitor_left,
            monitor_top,
            physical_width,
            physical_height,
            win32con.SWP_SHOWWINDOW
        )
        time.sleep(0.5)
        
        # 3. Максимизируем на весь экран
        win32gui.ShowWindow(target_hwnd, win32con.SW_MAXIMIZE)
        time.sleep(1)
        
        # 4. Дополнительная проверка - убеждаемся, что окно действительно на нужном месте
        win32gui.SetWindowPos(
            target_hwnd,
            win32con.HWND_TOP,
            monitor_left,
            monitor_top,
            physical_width,
            physical_height,
            win32con.SWP_SHOWWINDOW
        )
        
        print(f"    ✓ Окно успешно размещено на мониторе {monitor_index+1}")
        return True
        
    except Exception as e:
        print(f"    ✗ Ошибка при перемещении: {e}")
        return False

def main():
    """
    Основная функция запуска HTML файлов на мониторах.
    """
    print("=" * 70)
    print("ЗАПУСК HTML ФАЙЛОВ НА МОНИТОРАХ")
    print("=" * 70)
    
    if sys.platform != "win32":
        print("Ошибка: Эта программа работает только на Windows!")
        return
    
    os.chdir(os.path.dirname(os.path.abspath(__file__)))
    
    print("\n1. ОПРЕДЕЛЕНИЕ МОНИТОРОВ...")
    all_monitors = get_monitors_info()
    
    if not all_monitors:
        print("Ошибка: Не удалось определить мониторы!")
        return
    
    print(f"Найдено мониторов: {len(all_monitors)}")
    
    print("\n2. ПОИСК HTML ФАЙЛОВ...")
    html_files = find_html_files()
    
    if not html_files:
        print("Ошибка: HTML файлы не найдены!")
        print("Сначала запустите Convert.py для создания HTML файлов")
        return
    
    print(f"Найдено HTML файлов: {len(html_files)}")
    for i, file_info in enumerate(html_files):
        print(f"   {i+1}. {file_info['name']}")
    
    print("\n3. КОНФИГУРАЦИЯ РАСПРЕДЕЛЕНИЯ...")
    config = load_monitor_config()
    monitor_mapping = get_monitor_mapping(html_files, all_monitors, config)
    
    # Проверяем, что у нас достаточно мониторов
    max_monitor_needed = max(monitor_mapping) if monitor_mapping else 0
    if max_monitor_needed >= len(all_monitors):
        print(f"\n⚠  Внимание: требуется монитор {max_monitor_needed + 1}, но доступно только {len(all_monitors)}")
        print("   Файлы будут переназначены на доступные мониторы")
        # Переназначаем на доступные мониторы
        for i in range(len(monitor_mapping)):
            if monitor_mapping[i] >= len(all_monitors):
                monitor_mapping[i] = i % len(all_monitors)
    
    print("\n4. ПОИСК YANDEX BROWSER...")
    yandex_path = find_yandex_executable()
    
    if not yandex_path:
        print("Ошибка: Яндекс Браузер не найден!")
        print("Установите Яндекс Браузер или укажите путь к нему в коде")
        return
    
    print(f"Яндекс Браузер найден: {yandex_path}")
    
    print("\n5. ЗАКРЫТИЕ ПРЕДЫДУЩИХ ОКОН...")
    
    try:
        # Закрываем Яндекс Браузер
        subprocess.run(
            ["taskkill", "/F", "/IM", "browser.exe", "/T"],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            shell=True
        )
        time.sleep(2)
        print("Закрыты предыдущие окна Яндекс Браузера")
    except Exception:
        print("Не удалось закрыть предыдущие окна (возможно, они не были открыты)")
    
    print("\n6. ЗАПУСК ФАЙЛОВ НА МОНИТОРАХ...")
    print("=" * 50)
    
    processes = []
    
    # ЗАПУСКАЕМ ВСЕ ОКНА
    for i, html_file in enumerate(html_files):
        monitor_idx = monitor_mapping[i]
        
        print(f"\nЗАПУСК: {html_file['sheet']}")
        print(f"   Файл: {html_file['name']}")
        print(f"   Назначен на монитор: {monitor_idx + 1}")
        
        # АРГУМЕНТЫ Яндекс Браузера для полноэкранного режима
        yandex_args = [
            yandex_path,
            "--new-window",           # Новое окно
            "--start-fullscreen",     # Запуск в полноэкранном режиме
            html_file['url']          # URL файла передается ОТДЕЛЬНЫМ аргументом
        ]
        
        try:
            # Создаем новый процесс Яндекс Браузера
            CREATE_NO_WINDOW = 0x08000000
            proc = subprocess.Popen(
                yandex_args,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                creationflags=CREATE_NO_WINDOW
            )
            
            processes.append(proc)
            print(f"   Яндекс Браузер запущен (PID: {proc.pid})")
            
            # Даем время на загрузку каждого окна
            if i < len(html_files) - 1:
                print(f"   Ожидание загрузки окна...")
                time.sleep(5)
            
        except Exception as e:
            print(f"   Ошибка запуска: {e}")
            processes.append(None)
    
    print("\n7. ПОЗИЦИОНИРОВАНИЕ ОКОН НА МОНИТОРАХ...")
    print("=" * 50)
    
    # Ждем и позиционируем окна
    successful_placements = 0
    
    for i, (html_file, proc) in enumerate(zip(html_files, processes)):
        if proc is None:
            print(f"\nПРОПУСКАЕМ: {html_file['sheet']} (не запущено)")
            continue
        
        monitor_idx = monitor_mapping[i]
        
        print(f"\nПОЗИЦИОНИРОВАНИЕ: {html_file['sheet']}")
        print(f"   PID: {proc.pid}")
        print(f"   Целевой монитор: {monitor_idx + 1}")
        
        # Пытаемся позиционировать окно
        success = wait_and_position_window(proc.pid, monitor_idx, all_monitors, html_file['sheet'])
        
        if success:
            print(f"   ✓ УСПЕШНО размещено на мониторе {monitor_idx + 1}")
            successful_placements += 1
        else:
            print(f"   ✗ НЕ УДАЛОСЬ разместить автоматически")
            print(f"   → Вручную перетащите окно '{html_file['sheet']}' на монитор {monitor_idx + 1}")
    
    print("\n" + "=" * 70)
    print("ОКНА ЗАПУЩЕНЫ!")
    print("=" * 70)
    
    print(f"\nИТОГОВЫЙ ОТЧЕТ:")
    print(f"   • Мониторов: {len(all_monitors)}")
    print(f"   • Запущено файлов: {len(html_files)}")
    print(f"   • Успешно размещено: {successful_placements}")
    
    # Показываем итоговое распределение
    print(f"\nИТОГОВОЕ РАСПРЕДЕЛЕНИЕ:")
    for i, html_file in enumerate(html_files):
        if i < len(monitor_mapping):
            monitor_num = monitor_mapping[i] + 1
            print(f"   • {html_file['name']:20} → Монитор {monitor_num}")
    
    if successful_placements == len(html_files):
        print(f"\n✓ ВСЕ ОКНА УСПЕШНО РАЗМЕЩЕНЫ!")
    else:
        print(f"\n⚠ НЕ ВСЕ ОКНА УДАЛОСЬ РАЗМЕСТИТЬ ({successful_placements}/{len(html_files)})")
    
    print(f"\n" + "=" * 70)
    print("ПРОГРАММА ЗАВЕРШАЕТ РАБОТУ")
    print("=" * 70)
    print("\nОкна остаются открытыми в полноэкранном режиме.")
    print("Для выхода используйте Alt+F4 на каждом окне или Alt+Tab для переключения.")
    
    # Сохраняем использованное распределение в файл для справки
    try:
        used_config = {
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
            "distribution": [
                {"html_file": html_files[i]['name'], "monitor": monitor_mapping[i] + 1}
                for i in range(len(html_files))
            ]
        }
        
        with open("last_distribution.json", "w", encoding="utf-8") as f:
            json.dump(used_config, f, indent=2, ensure_ascii=False)
        
        print(f"\n📄 Использованное распределение сохранено в last_distribution.json")
    except Exception as e:
        print(f"\n⚠ Не удалось сохранить распределение: {e}")
    
    # Программа завершает работу, окна остаются открытыми
    sys.exit(0)

if __name__ == "__main__":
    main()