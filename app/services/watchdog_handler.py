import time
import threading
from pathlib import Path
from watchdog.events import FileSystemEventHandler
import logging

logger = logging.getLogger(__name__)

class MangaWatchdogHandler(FileSystemEventHandler):
    def __init__(self, cooldown: float = 2.0, task_func=None):
        super().__init__()
        self.cooldown = cooldown
        self._pending = {}
        self._lock = threading.Lock()
        self._timers = {}
        self.task_func = task_func

    def _on_event(self, path: str):
        if not path.lower().endswith(('.cbz', '.cbr')): return
        with self._lock:
            self._pending[path] = time.time() + self.cooldown
        if path not in self._timers:
            t = threading.Timer(self.cooldown, self._execute, args=[path])
            self._timers[path] = t
            t.start()

    def on_created(self, event):
        if not event.is_directory: self._on_event(event.src_path)
    def on_modified(self, event):
        if not event.is_directory: self._on_event(event.src_path)

    def _execute(self, path: str):
        with self._lock:
            self._timers.pop(path, None)
        if not Path(path).exists(): return
        if self.task_func:
            self.task_func.delay(str(path))
            logger.info(f"📥 Archivo detectado y encolado: {path}")