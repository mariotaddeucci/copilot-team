import importlib
import logging
from typing import Any, Callable

from copilot import CopilotClient
from injector import Binder, Inject, Injector, Module, singleton

from copilot_team.core.interfaces import BaseTaskStoreBackend
from copilot_team.core.services import TaskService
from copilot_team.core.settings import Settings


def create_logger(settings: Inject[Settings]) -> logging.Logger:
    logger = logging.getLogger(settings.app_name)
    logger.setLevel(settings.logger.level)

    stdout_handler = logging.StreamHandler()
    stdout_handler.setLevel(logging.DEBUG)
    stdout_handler.addFilter(lambda record: record.levelno < logging.WARNING)
    formatter = logging.Formatter(settings.logger.format)
    stdout_handler.setFormatter(formatter)

    stderr_handler = logging.StreamHandler()
    stderr_handler.setLevel(logging.WARNING)
    stderr_handler.setFormatter(formatter)

    logger.addHandler(stdout_handler)
    logger.addHandler(stderr_handler)
    return logger


def create_factory(
    implementation_name: str,
    desired_type: type,
) -> Callable[..., Any]:
    def factory(settings: Inject[Settings], injector: Inject[Injector]) -> Any:
        impl_path = getattr(settings.core.implementations, implementation_name)
        module_path, cls_name = impl_path.rsplit(".", 1)
        module = importlib.import_module(module_path)
        impl_class = getattr(module, cls_name)
        if not issubclass(impl_class, desired_type):
            raise ValueError(
                f"{impl_path} is not a subclass of {desired_type.__name__}"
            )
        return injector.create_object(impl_class)

    return factory


class Dependencies(Module):
    def configure(self, binder: Binder):
        binder.bind(Settings, scope=singleton)
        binder.bind(logging.Logger, to=create_logger, scope=singleton)
        binder.bind(
            CopilotClient,
            to=lambda: CopilotClient({"auto_restart": True, "auto_start": True}),
            scope=singleton,
        )
        binder.bind(
            BaseTaskStoreBackend,
            to=create_factory("task_store", BaseTaskStoreBackend),
            scope=singleton,
        )
        binder.bind(TaskService, scope=singleton)


def create_injector(*, modules: list[Module] | None = None) -> Injector:
    injector = Injector(modules=[Dependencies()])
    injector.binder.bind(Injector, to=injector)
    if modules:
        injector = Injector(modules=modules, parent=injector)

    return injector
