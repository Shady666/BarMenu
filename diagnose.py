# diagnose.py
import window_manager as wm
import sys

print("🔍 ДИАГНОСТИКА СИСТЕМЫ")
print("=" * 60)

# Получаем информацию о мониторах
monitors = wm.get_monitors_info()
print(f"Найдено мониторов: {len(monitors)}")

for i, monitor in enumerate(monitors):
    primary = " (ОСНОВНОЙ)" if monitor['is_primary'] else ""
    print(f"\nМонитор {i}:")
    print(f"  Координаты: ({monitor['left']}, {monitor['top']}) → ({monitor['right']}, {monitor['bottom']})")
    print(f"  Разрешение: {monitor['width']}x{monitor['height']}")
    print(f"  Статус: {primary}")
    print(f"  Windows Handle: {monitor['handle']}")

# Проверка API Windows
print("\n" + "=" * 60)
print("ПРОВЕРКА WINDOWS API:")

if sys.platform != "win32":
    print("❌ Не Windows система!")
else:
    try:
        import win32gui
        print("✅ win32gui работает")
    except Exception as e:
        print(f"❌ Ошибка win32gui: {e}")

input("\nНажмите Enter для завершения...")