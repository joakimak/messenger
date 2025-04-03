import contextvars
import datetime
import json
import logging


class Logger:
    def __init__(self, name: str):
        _formatter = logging.Formatter("%(message)s")
        _console_handler = logging.StreamHandler()
        _console_handler.setFormatter(_formatter)
        self._logger = logging.getLogger(name)
        self._logger.setLevel(logging.DEBUG)
        self._logger.handlers.clear()
        self._logger.addHandler(_console_handler)
        self._mdc_var = contextvars.ContextVar("mdc", default={})

    def info(self, message: str, **kwargs) -> None:
        self._log("info", message, **kwargs)

    def error(self, message: str, **kwargs) -> None:
        self._log("error", message, **kwargs)

    def debug(self, message: str, **kwargs) -> None:
        self._log("debug", message, **kwargs)

    def warn(self, message: str, **kwargs) -> None:
        self._log("warning", message, **kwargs)

    def add_mdc(self, key: str, value: str) -> None:
        mdc = self._mdc_var.get()
        mdc[key] = value
        self._mdc_var.set(mdc)

    def _log(self, level: str, message: str, **kwargs) -> None:
        log_data = self._mdc_var.get()
        log_data.update(kwargs)
        log_message = {
            "level": level,
            "message": message,
            "data": log_data,
            "timestamp": datetime.datetime.now().isoformat(),
        }

        self._logger.log(getattr(logging, level.upper(), logging.INFO), json.dumps(log_message))


global_logger = Logger(__name__)
