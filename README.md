# Whisper Transcriber

Простой оффлайн-инструмент для macOS, который извлекает аудио из видеофайлов, распознаёт речь с помощью OpenAI Whisper и сохраняет расшифровку в `.txt`. Поддерживает как консольный режим, так и графический интерфейс.

## Возможности
- Принимает `MP4`, `MOV`, `AVI`.
- Извлекает аудио через `ffmpeg` и запускает Whisper локально.
- Сохраняет текстовый файл рядом с исходным видео.
- GUI на `tkinter` с выбором файла, индикатором выполнения и выбором модели.
- Drag & drop путей в терминал, запуск из Finder через `Transcriber.command`.

## Требования
- macOS (проверено на Apple Silicon).
- Python 3.11 (`brew install python@3.11`).
- Установленный `ffmpeg` (`brew install ffmpeg`).
- Tkinter для Python 3.11 (`brew install python-tk@3.11`).
- Библиотеки Python: `openai-whisper`, `ffmpeg-python`, `tqdm`.

## Установка
```bash
# клон репозитория
git clone git@github.com:NataliaAtiukova/transcriber.git
cd transcriber

# виртуальное окружение
/opt/homebrew/bin/python3.11 -m venv .venv
source .venv/bin/activate

# зависимости
pip install openai-whisper ffmpeg-python tqdm

# системные пакеты (если не установлены)
brew install ffmpeg python-tk@3.11
```

## Использование

### GUI
```bash
source .venv/bin/activate
python transcribe.py --gui
```
Или двойной клик по `Transcriber.command` в Finder (запустится окно + терминал).

### CLI
```bash
source .venv/bin/activate
python transcribe.py "/путь/к/видео.mp4"
```
Файл `.txt` появится рядом с видео. Можно перетянуть ролик на терминал, чтобы автоматически подставить путь.

## Дополнительно
- Переменная окружения `WHISPER_MODEL` задаёт модель (по умолчанию `base`, доступны `tiny`, `small`, `medium`, `large`, и т.д.).
- При первом запуске Whisper скачивает веса модели в `~/.cache/whisper`.
- Для запуска без терминала можно создать Automator App с командой:
  ```bash
  cd "/Users/<user>/Downloads/transcriber"
  source .venv/bin/activate
  python transcribe.py --gui
  ```

## Лицензия
Проект доступен для личного использования; при распространении учитывайте лицензии зависимостей (Whisper, FFmpeg, Python).
