from typing import Any, Callable

from PySide6.QtCore import QThread, Signal


class AsyncCallThread(QThread):
    succeeded = Signal(object)
    failed = Signal(object)

    def __init__(self, fn: Callable[..., Any], /, *args, parent=None, **kwargs):
        super().__init__(parent)
        self._fn = fn
        self._args = args
        self._kwargs = kwargs

    def run(self):
        try:
            result = self._fn(*self._args, **self._kwargs)
        except Exception as exc:
            self.failed.emit(exc)
            return
        self.succeeded.emit(result)
