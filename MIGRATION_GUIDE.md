# MIGRATION_GUIDE.md

Пошаговое руководство: как перейти на Modern UI и как откатиться назад.

## 1. Переход на Modern UI

```bash
cd prizma
pip install -r requirements.txt
python test_modern_ui.py     # проверка окружения
python main_modern.py        # запуск новой версии
```

Прежние настройки из `~/.tools_config.json` подхватятся автоматически.

## 2. Как откатиться

### Вариант A. Просто запускать классику

```bash
python main.py
```

`main.py` не изменялся. Modern UI лежит рядом и никак не мешает.

### Вариант B. Восстановить main.py из резервной копии

```bash
cp main_backup.py main.py
```

### Вариант C. Полностью удалить Modern UI

```bash
rm main_modern.py test_modern_ui.py
rm core/modern_widgets.py core/theme_modern.py
rm README_MODERN.md MODERNIZATION_GUIDE.md MIGRATION_GUIDE.md CHANGELOG.md
```

## 3. Совместное использование

Обе версии могут спокойно сосуществовать:
* один и тот же `~/.tools_config.json`
* одни и те же модули PDF/PSD
* можно запускать одновременно (два независимых окна)

## 4. Частые вопросы

**Q: Классика перестала запускаться после установки Modern UI.**
A: Такого не должно быть. Проверьте: `diff main.py main_backup.py` (должны совпадать).

**Q: В сайдбаре не появляются недавние файлы.**
A: Список обновляется при открытии файла. Откройте любой PDF/PSD.

**Q: Drag & Drop не работает.**
A: Убедитесь, что `tkinterdnd2` установлен: `python -c "import tkinterdnd2"`.
На некоторых Linux DE (Wayland) DnD не поддерживается.

**Q: Хочу переключаться на классику по горячей клавише.**
A: Сделайте два ярлыка: один на `python main.py`, второй на `python main_modern.py`.

## 5. Если что-то сломалось

1. Запустите `python test_modern_ui.py` — сравните вывод с README_MODERN.md.
2. Проверьте, что находитесь в папке `prizma/`.
3. Проверьте версию Python: нужна **3.9+**.
4. Проверьте `~/.tools_config.json` — должен быть валидным JSON.
   Если файл битый — удалите его, он пересоздастся при следующем запуске.
