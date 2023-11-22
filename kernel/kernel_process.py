#!/usr/bin/env python
# -*- coding: utf-8 -*-
# kernel/kernel_process.py

import asyncio
import os
import signal
from multiprocessing import Process

from ipykernel.kernelapp import IPKernelApp
from setproctitle import setproctitle

from kernel.kernel_message import KernelMessage, NodeType
from kernel.kernel_node import Flow, KernelNode


class KernelProcessServer(KernelNode):
    _provider_id: bytes

    def __init__(
        self,
        provider_address: str,
        provider_id: bytes,
        root_path: str,
    ) -> None:
        super().__init__(NodeType.Kernel, root_path=root_path)
        self.connect(provider_address, to_master=True)

        self._provider_id = provider_id

    def send_to_provider(self, *args, **kwargs) -> None:
        self.send(*args, id=self._provider_id, **kwargs)


class KernelProcess(Process):
    id: bytes

    kernel_id: str  # uuid4
    _provider_path: str
    _provider_port: int
    _provider_id: bytes
    _req_flow: Flow

    def __init__(
        self,
        kernel_id: str,
        provider_path: str,
        provider_port: int,
        provider_id: bytes,
        flow: Flow,
    ) -> None:
        super(KernelProcess, self).__init__()

        self.kernel_id = kernel_id
        self._provider_path = provider_path
        self._provider_id = provider_id
        self._provider_port = provider_port
        self._req_flow = flow

    def run(self) -> None:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

        os.setpgrp()
        setproctitle(f"python kernel {self.kernel_id}")

        server = KernelProcessServer(
            f"tcp://127.0.0.1:{self._provider_port}",
            self._provider_id,
            f"{self._provider_path}/{self.kernel_id}",
        )

        IPKernelApp.no_stdout = True
        IPKernelApp.no_stderr = True

        app = IPKernelApp.instance()
        app.user_ns = {
            "kernel_id": self.kernel_id,
            "_ROOT_PATH": server.root_path,
            "_SERVER": server,
        }

        app.initialize()
        app.cleanup_connection_file()

        loop.call_later(
            0.5,
            lambda: server.send_to_provider(
                KernelMessage.READY_KERNEL,
                json_body={
                    "kernel_id": self.kernel_id,
                    "connection": {
                        "session_key": app.session.key.decode(),
                        "ip": app.ip,
                        "hb": app.hb_port,
                        "iopub": app.iopub_port,
                        "shell": app.shell_port,
                        "process_key": server._identity.decode(),
                        "process": server._port,
                    },
                },
                flow=self._req_flow,
            ),
        )

        def signal_handler(*_):
            app.kernel.do_shutdown(False)

        signal.signal(signal.SIGTERM, signal_handler)
        app.start()

    def stop(self) -> None:
        print(f"stop {self.kernel_id}")
        if self.is_alive():
            try:
                os.kill(self.pid, signal.SIGTERM)
            except:
                pass
