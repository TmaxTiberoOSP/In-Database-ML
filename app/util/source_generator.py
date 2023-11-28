#!/usr/bin/env python
# -*- coding: utf-8 -*-
# app/util/source_generator.py


from app.model.model import Component, Model


def get_model_source(model: Model):
    def class_init_source(c: Component):
        source = f"        "
        if c.code:
            pass
        elif c.is_container():
            pass
        else:
            return source + f"self.{c.name} = nn.{c.type}({c.params})"

    def class_forward_source(c: Component):
        def replace(str: str):
            return str.replace("{OUTPUT}", "input")

        source = f"        input = "
        if c.code:
            return (
                source
                + f"{replace(c.code)}({replace(c.params) if c.params else 'input'})"
            )

        else:
            return source + f"self.{c.name}(input)"

    source = "##################\n"
    source += "# Network Source #\n"
    source += "##################\n\n"

    source += "import torch\n"
    source += "import torch.nn as nn\n"
    source += "\n"

    source += f"class {model.get_source_classname()}(nn.Module):\n"
    source += "    def __init__(self):\n"
    source += "        super(Network, self).__init__()\n\n"
    source += (
        "\n".join(filter(None, [class_init_source(c) for c in model.layers])) + "\n\n"
    )

    source += f"    def forward(self, input):\n"
    source += "\n".join(class_forward_source(c) for c in model.layers) + "\n"
    source += "\n        return input\n"

    return source
