# Prizma Studio — Modern UI

Модернизированная версия Prizma Studio с новым интерфейсом:
Sidebar + Browser-style Tabs + Welcome Screen + улучшенный журнал.

Классический интерфейс (`main.py`) **сохранён без изменений** — можно
переключаться между версиями в любой момент.

---

## Что нового

| Элемент | Классика (`main.py`) | Modern (`main_modern.py`) |
|---|---|---|
| Навигация | `ttk.Notebook` с 4 вкладками | Sidebar 240 px + Top bar + Tabs |
| Файлы | 1 PDF + 1 PSD одновременно | Много вкладок как в браузере |
| Стартовый экран | Пустая вкладка «PDF Tools» | Welcome Screen с кнопками |
| Недавние файлы | Нет | В сайдбаре, до 8 штук |
| Журнал | ` • ! × ✓ ` | `ℹ ✓ ⚠ ✕` + цветные уровни |
| Drag & Drop | Нет | Есть (если установлен `tkinterdnd2`) |
| Тема | sv-ttk light/dark | sv-ttk + кастомная палитра |

---

## Установка

```bash
git clone https://github.com/Nekosaa/prizma.git
cd prizma
pip install -r requirements.txt
python test_modern_ui.py
```

## Запуск

```bash
python main_modern.py       # Modern UI (новый интерфейс)
python main.py              # Classic UI (без изменений)
```

Все настройки лежат в `~/.tools_config.json` и общие для обеих версий.

---

## Схема окна

```
┌──────────┬───────────────────────────────────────────┐
│          │  [📄 PDF] [🎨 PSD]        [⚙] [ℹ] [RU▾]   │  ← Top bar
│  ◆ Prizma├───────────────────────────────────────────┤
│  Studio  │  [📄 doc.pdf ×] [🎨 tpl.psd ×]             │  ← Tab bar
│          ├───────────────────────────────────────────┤
│  Недавние│                                            │
│  • a.pdf │            Active content                  │
│  • b.psd │      (PDF viewer / PSD tools / …)          │
│          ├───────────────────────────────────────────┤
│ [Очист.] │  📋 Журнал                        [Очист.] │
├──────────┴───────────────────────────────────────────┤
│ Готово                                               │  ← Status bar
└──────────────────────────────────────────────────────┘
```

---

## Обратная совместимость

* `main.py` и все существующие модули PDF/PSD **не изменялись**
* `core/config.py` дополнен ключом `recent_files` (список)
* `core/i18n.py` дополнен строками для sidebar/welcome
* Файл `main_backup.py` — чистая копия оригинального `main.py`

---

## Известные ограничения

* PSD-функции работают только на Windows (нужен Photoshop и `pywin32`)
* Drag & Drop работает, только если установлен `tkinterdnd2`

Автор: **MurKasKaa** · Модернизация UI: без изменений бизнес-логики.
