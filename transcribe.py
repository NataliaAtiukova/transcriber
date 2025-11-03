#!/usr/bin/env python3
import os
import sys
import tempfile

import ffmpeg
import whisper
from tqdm import tqdm

SUPPORTED_EXTS = {".mp4", ".mov", ".avi"}


def normalize_path(path):
    return path.strip().strip('"').strip("'")


def extract_audio(video_path, audio_path):
    (
        ffmpeg.input(video_path)
        .output(audio_path, format="wav", acodec="pcm_s16le", ac=1, ar="16000")
        .overwrite_output()
        .run(quiet=True)
    )


def load_model(model_name):
    return whisper.load_model(model_name)


def transcribe_audio(model, audio_path):
    return model.transcribe(audio_path, verbose=False, fp16=False)


def transcribe_video(video_path, model_name=None, status_cb=None):
    status_cb = status_cb or (lambda message: None)
    if not video_path:
        raise ValueError("Путь к файлу не указан.")

    video_path = normalize_path(video_path)
    if not os.path.isfile(video_path):
        raise FileNotFoundError(f"Файл не найден: {video_path}")

    ext = os.path.splitext(video_path)[1].lower()
    if ext not in SUPPORTED_EXTS:
        raise ValueError(
            f"Поддерживаемые форматы: {', '.join(sorted(SUPPORTED_EXTS))}"
        )

    output_dir = os.path.dirname(video_path) or "."
    base_name = os.path.splitext(os.path.basename(video_path))[0]
    txt_path = os.path.join(output_dir, f"{base_name}.txt")

    audio_tmp = tempfile.NamedTemporaryFile(suffix=".wav", delete=False)
    audio_path = audio_tmp.name
    audio_tmp.close()

    try:
        status_cb("Извлечение аудио...")
        extract_audio(video_path, audio_path)

        status_cb("Распознавание...")
        model_name = model_name or os.environ.get("WHISPER_MODEL", "base")
        model = load_model(model_name)
        result = transcribe_audio(model, audio_path)

        text = result.get("text", "").strip()
        if not text and result.get("segments"):
            text = "\n".join(s["text"].strip() for s in result["segments"]).strip()

        with open(txt_path, "w", encoding="utf-8") as handle:
            handle.write(text)

        status_cb("Готово!")
        status_cb(f"Сохранено в {txt_path}")
        return txt_path
    except ffmpeg.Error as exc:
        raise RuntimeError(f"Ошибка ffmpeg: {exc}") from exc
    finally:
        if os.path.exists(audio_path):
            os.remove(audio_path)


def run_cli(video_path):
    printer = tqdm.write
    try:
        txt_path = transcribe_video(video_path, status_cb=printer)
        printer(f"Файл результата: {txt_path}")
    except Exception as exc:
        print(exc)
        sys.exit(1)


def launch_gui():
    import queue
    import threading
    import tkinter as tk
    from tkinter import filedialog, messagebox, ttk

    root = tk.Tk()
    root.title("Whisper Transcriber")
    root.geometry("520x220")
    root.resizable(False, False)

    path_var = tk.StringVar()
    status_var = tk.StringVar(value="Выберите видеофайл.")
    model_var = tk.StringVar(value=os.environ.get("WHISPER_MODEL", "base"))
    msg_queue = queue.Queue()

    def post_status(message):
        msg_queue.put(("status", message))

    def choose_file():
        initial = os.path.expanduser("~/Downloads")
        file_path = filedialog.askopenfilename(
            title="Выберите видеофайл",
            initialdir=initial if os.path.isdir(initial) else None,
            filetypes=(
                ("Видео", "*.mp4 *.mov *.avi"),
                ("Все файлы", "*.*"),
            ),
        )
        if file_path:
            path_var.set(file_path)
            status_var.set("Готово к запуску.")

    def worker(video_path, model_name):
        try:
            txt_path = transcribe_video(
                video_path, model_name=model_name, status_cb=post_status
            )
            msg_queue.put(("done", txt_path))
        except Exception as exc:
            msg_queue.put(("error", str(exc)))

    def start_transcription():
        video_path = path_var.get().strip()
        if not video_path:
            messagebox.showwarning("Файл не выбран", "Выберите видеофайл.")
            return
        start_btn.config(state="disabled")
        browse_btn.config(state="disabled")
        progress.start(10)
        status_var.set("Запуск...")
        thread = threading.Thread(
            target=worker, args=(video_path, model_var.get()), daemon=True
        )
        thread.start()

    def process_queue():
        try:
            while True:
                kind, payload = msg_queue.get_nowait()
                if kind == "status":
                    status_var.set(payload)
                elif kind == "done":
                    progress.stop()
                    start_btn.config(state="normal")
                    browse_btn.config(state="normal")
                    status_var.set(f"Готово! См. {payload}")
                    messagebox.showinfo("Готово", f"Транскрипт сохранен:\n{payload}")
                elif kind == "error":
                    progress.stop()
                    start_btn.config(state="normal")
                    browse_btn.config(state="normal")
                    status_var.set("Ошибка.")
                    messagebox.showerror("Ошибка", payload)
        except queue.Empty:
            pass
        finally:
            root.after(100, process_queue)

    frame = ttk.Frame(root, padding=20)
    frame.pack(fill="both", expand=True)

    ttk.Label(frame, text="Видео:").grid(row=0, column=0, sticky="w")
    entry = ttk.Entry(frame, textvariable=path_var, width=50)
    entry.grid(row=0, column=1, sticky="ew", padx=(10, 10))

    browse_btn = ttk.Button(frame, text="Выбрать…", command=choose_file)
    browse_btn.grid(row=0, column=2, sticky="ew")

    ttk.Label(frame, text="Модель Whisper:").grid(
        row=1, column=0, sticky="w", pady=(15, 0)
    )
    model_entry = ttk.Entry(frame, textvariable=model_var, width=20)
    model_entry.grid(row=1, column=1, sticky="w", padx=(10, 10), pady=(15, 0))

    start_btn = ttk.Button(frame, text="Старт", command=start_transcription)
    start_btn.grid(row=1, column=2, sticky="ew", pady=(15, 0))

    progress = ttk.Progressbar(frame, mode="indeterminate")
    progress.grid(row=2, column=0, columnspan=3, sticky="ew", pady=(20, 10))

    status_label = ttk.Label(frame, textvariable=status_var, wraplength=440)
    status_label.grid(row=3, column=0, columnspan=3, sticky="w")

    frame.columnconfigure(1, weight=1)
    root.after(100, process_queue)
    root.mainloop()


def main():
    raw_args = sys.argv[1:]
    use_gui = "--gui" in raw_args or not raw_args
    args = [arg for arg in raw_args if arg != "--gui"]

    if use_gui:
        launch_gui()
        return

    if not args:
        print("Использование: python transcribe.py <путь_к_видео>")
        print("Для GUI используйте ключ --gui")
        sys.exit(1)

    run_cli(args[0])


if __name__ == "__main__":
    main()
