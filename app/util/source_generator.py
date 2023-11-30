#!/usr/bin/env python
# -*- coding: utf-8 -*-
# app/util/source_generator.py


from pathlib import Path

from app.model.model import Component, Model

dataloader_source_origin: str = ""
with open(f"{Path(__file__).parent.absolute()}/jdbc_dataloader.source", "r") as file:
    dataloader_source_origin = file.read()

train_source_origin: str = ""
with open(f"{Path(__file__).parent.absolute()}/train.source", "r") as file:
    train_source_origin = file.read()


def get_dataloader_source(
    dataset_table: str,
    dataset_label: str,
    dataset_data: str,
    testset_table: str,
    testset_label: str,
    testset_data: str,
) -> str:
    replaces = [
        ["{DATASET_TABLE_NAME}", dataset_table],
        ["{DATASET_LABEL_COLUMN_NAME}", dataset_label],
        ["{DATASET_DATA_COLUMN_NAME}", dataset_data],
        ["{TESTSET_TABLE_NAME}", testset_table],
        ["{TESTSET_LABEL_COLUMN_NAME}", testset_label],
        ["{TESTSET_DATA_COLUMN_NAME}", testset_data],
    ]

    source = dataloader_source_origin
    for old, new in replaces:
        source = source.replace(old, new)

    return source


def get_network_source(model: Model) -> str:
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

    source = "#####################\n"
    source += "#  Network Source   #\n"
    source += "#####################\n\n"

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


def get_train_source(
    model: Model, train_id: int, num_epochs: int, mini_batches: int
) -> str:
    model_name = model.get_source_name()
    replaces = [
        ["{MODEL_CLASS}", model.get_source_classname()],
        ["{MODEL_NAME}", model_name],
        ["{LOSS_FN_TYPE}", model.loss_fn.type],
        ["{LOSS_FN_NAME}", model.loss_fn.name],
        ["{LOSS_FN_PARAMS}", model.loss_fn.params],
        ["{OPTIMIZER_TYPE}", model.optimizer.type],
        ["{OPTIMIZER_NAME}", model.optimizer.name],
        ["{OPTIMIZER_PARAMS}", model.optimizer.params.replace("{MODEL}", model_name)],
        ["{OUTPUT_NAME}", f"{model.id}_{model_name}.pt"],
        ["{TRAIN_ID}", str(train_id)],
        ["{NUM_EPOCHS}", str(num_epochs)],
        ["{MINI_BATCHES}", str(mini_batches)],
    ]

    source = train_source_origin
    for old, new in replaces:
        source = source.replace(old, new)

    return source
