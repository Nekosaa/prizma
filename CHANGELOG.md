# Changelog

Все существенные изменения проекта задокументированы здесь.
Формат — на основе [Keep a Changelog](https://keepachangelog.com/ru/1.1.0/).

## [Unreleased] — Modern UI

### Added

* **`main_modern.py`** — модернизированный entry point с новой раскладкой
  (Sidebar + Top bar + Browser-style tabs + Welcome Screen + улучшенный журнал).
* **`core/modern_widgets.py`** — новые виджеты:
  * `BrowserTabBar` — вкладки в стиле браузера, с кнопкой `×`.
  * `ModernSidebar` — левый сайдбар 240 px с брендом и списком недавних файлов.
  * `WelcomeScreen` — стартовый экран с крупными кнопками «Открыть PDF/PSD».
  * `ModernLogPanel` — журнал событий с цветными уровнями.
* **`core/theme_modern.py`** — новая система тем:
  * Кастомные светлая и тёмная палитры (спокойный синий вместо «AI-фиолетового»).
  * Кастомные ttk-стили для sidebar, tab bar, welcome, log, ghost/accent-кнопок.
* **`test_modern_ui.py`** — скрипт проверки зависимостей и внутренних модулей.
* **Резервная копия** — `main_backup.py` (чистая копия `main.py`).
* **Документация**: README_MODERN.md, MODERNIZATION_GUIDE.md, MIGRATION_GUIDE.md, CHANGELOG.md.
* **Drag & Drop** — опциональная поддержка через `tkinterdnd2`.
* **Множество открытых файлов одновременно** — каждый PDF/PSD в своей вкладке.
* **Хранение недавних файлов** — новый ключ `recent_files` в `~/.tools_config.json`.

### Changed

* **`core/i18n.py`** — добавлены строки для sidebar, welcome screen и top bar
  (`sidebar.*`, `welcome.*`, `topbar.*`). Существующие ключи не тронуты.
* **`core/config.py`** — в `DEFAULTS` добавлен ключ `recent_files: []`.
* **`requirements.txt`** — добавлена зависимость `tkinterdnd2>=0.4.2` (опциональная).

### Preserved (обратная совместимость)

* `main.py` — **не изменён**, работает как раньше.
* `core/theme.py` — используется классической версией.
* `modules/pdf_tools_tab.py` — PDF-функционал сохранён полностью.
* `modules/psd_tools_tab.py` — PSD-функционал сохранён полностью.
* `assets/`, `build_exe.py`, `PrizmaStudio.spec`, `fix_unicode.py`,
  `make_icon.py`, оригинальный `README.md` — без изменений.
* Все существующие ключи `~/.tools_config.json` — прежние.

## [1.0.0] — исходная версия

* Классический интерфейс: `ttk.Notebook` с 4 вкладками.
* PDF: просмотр, редактирование, слияние, вставка текста и изображений.
* PSD: разблокировка слоёв, замена фото в Smart Objects, пакетная обработка.
* Поддержка RU/EN через `core/i18n.py`.
* Светлая/тёмная тема через `sv-ttk`.
* Хранение настроек в `~/.tools_config.json`.
