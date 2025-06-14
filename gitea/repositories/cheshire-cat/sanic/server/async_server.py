from __future__ import annotations

import asyncio

from sanic.exceptions import SanicException


class AsyncioServer:
    """
    Wraps an asyncio server with functionality that might be useful to
    a user who needs to manage the server lifecycle manually.
    """

    __slots__ = ("app", "connections", "loop", "serve_coro", "server", "init")

    def __init__(
        self,
        app,
        loop,
        serve_coro,
        connections,
    ):
        # Note, Sanic already called "before_server_start" events
        # before this helper was even created. So we don't need it here.
        self.app = app
        self.connections = connections
        self.loop = loop
        self.serve_coro = serve_coro
        self.server = None
        self.init = False

    def startup(self):
        """
        Trigger "before_server_start" events
        """
        self.init = True
        return self.app._startup()

    def before_start(self):
        """
        Trigger "before_server_start" events
        """
        return self._server_event("init", "before")

    def after_start(self):
        """
        Trigger "after_server_start" events
        """
        return self._server_event("init", "after")

    def before_stop(self):
        """
        Trigger "before_server_stop" events
        """
        return self._server_event("shutdown", "before")

    def after_stop(self):
        """
        Trigger "after_server_stop" events
        """
        return self._server_event("shutdown", "after")

    def is_serving(self) -> bool:
        if self.server:
            return self.server.is_serving()
        return False

    def wait_closed(self):
        if self.server:
            return self.server.wait_closed()

    def close(self):
        if self.server:
            self.server.close()
            coro = self.wait_closed()
            task = asyncio.ensure_future(coro, loop=self.loop)
            return task

    def start_serving(self):
        if self.server:
            try:
                return self.server.start_serving()
            except AttributeError:
                raise NotImplementedError(
                    "server.start_serving not available in this version "
                    "of asyncio or uvloop."
                )

    def serve_forever(self):
        if self.server:
            try:
                return self.server.serve_forever()
            except AttributeError:
                raise NotImplementedError(
                    "server.serve_forever not available in this version "
                    "of asyncio or uvloop."
                )

    def _server_event(self, concern: str, action: str):
        if not self.init:
            raise SanicException(
                "Cannot dispatch server event without " "first running server.startup()"
            )
        return self.app._server_event(concern, action, loop=self.loop)

    def __await__(self):
        """
        Starts the asyncio server, returns AsyncServerCoro
        """
        task = asyncio.ensure_future(self.serve_coro)
        while not task.done():
            yield
        self.server = task.result()
        return self
