from enum import Enum, auto
from functools import partial
from typing import List, Optional, Union

from sanic.models.futures import FutureListener
from sanic.models.handler_types import ListenerType, Sanic


class ListenerEvent(str, Enum):
    def _generate_next_value_(name: str, *args) -> str:  # type: ignore
        return name.lower()

    BEFORE_SERVER_START = "server.init.before"
    AFTER_SERVER_START = "server.init.after"
    BEFORE_SERVER_STOP = "server.shutdown.before"
    AFTER_SERVER_STOP = "server.shutdown.after"
    MAIN_PROCESS_START = auto()
    MAIN_PROCESS_STOP = auto()


class ListenerMixin:
    def __init__(self, *args, **kwargs) -> None:
        self._future_listeners: List[FutureListener] = []

    def _apply_listener(self, listener: FutureListener):
        raise NotImplementedError  # noqa

    def listener(
        self,
        listener_or_event: Union[ListenerType[Sanic], str],
        event_or_none: Optional[str] = None,
        apply: bool = True,
    ) -> ListenerType[Sanic]:
        """
        Create a listener from a decorated function.

        To be used as a decorator:

        .. code-block:: python

            @bp.listener("before_server_start")
            async def before_server_start(app, loop):
                ...

        `See user guide re: listeners
        <https://sanicframework.org/guide/basics/listeners.html#listeners>`__

        :param event: event to listen to
        """

        def register_listener(listener, event):
            nonlocal apply

            future_listener = FutureListener(listener, event)
            self._future_listeners.append(future_listener)
            if apply:
                self._apply_listener(future_listener)
            return listener

        if callable(listener_or_event):
            return register_listener(listener_or_event, event_or_none)
        else:
            return partial(register_listener, event=listener_or_event)

    def main_process_start(self, listener: ListenerType[Sanic]) -> ListenerType[Sanic]:
        return self.listener(listener, "main_process_start")

    def main_process_stop(self, listener: ListenerType[Sanic]) -> ListenerType[Sanic]:
        return self.listener(listener, "main_process_stop")

    def before_server_start(self, listener: ListenerType[Sanic]) -> ListenerType[Sanic]:
        return self.listener(listener, "before_server_start")

    def after_server_start(self, listener: ListenerType[Sanic]) -> ListenerType[Sanic]:
        return self.listener(listener, "after_server_start")

    def before_server_stop(self, listener: ListenerType[Sanic]) -> ListenerType[Sanic]:
        return self.listener(listener, "before_server_stop")

    def after_server_stop(self, listener: ListenerType[Sanic]) -> ListenerType[Sanic]:
        return self.listener(listener, "after_server_stop")
