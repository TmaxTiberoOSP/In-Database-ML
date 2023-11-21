#!/usr/bin/env python
# -*- coding: utf-8 -*-
# kernel/kernel_message.py

import struct
from enum import Enum, auto

from typing_extensions import Self


class NodeType(Enum):
    Master = "master"
    Provider = "provider"
    Client = "client"

    def type(self, value: str) -> bool:
        return self.value == value


class NodeMessage(Enum):
    # Connection
    DISCONNECT = auto()
    GREETING = auto()
    GREETING_REPLY = auto()

    def type(self, value: int) -> bool:
        return self.value == value

    def pack(self) -> bytes:
        return struct.pack("<H", self.value)

    def unpack(value) -> (int, Self):
        value = struct.unpack("<H", value)[0]
        return value, NodeMessage(value)
