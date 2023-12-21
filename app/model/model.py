#!/usr/bin/env python
# -*- coding: utf-8 -*-
# app/model/model.py

import io
import json

import torchvision.transforms as transforms
from fastapi import HTTPException
from jaydebeapi import Connection
from PIL import Image
from pydantic import BaseModel
from torch import Tensor


class RequestInferenceImage(BaseModel):
    train_id: int
    data_id: int
    # TODO: 모델 정보를 바탕으로 width, height 추출하는 방법 리서치
    width: int = 32
    height: int = 32


def default_str(dict, key, defulat="") -> str:
    return dict[key] if key in dict else defulat


class Component(BaseModel):
    type: str
    name: str
    params: str
    code: str

    def __init__(self, json_raw) -> None:
        obj = json.loads(json_raw)
        super().__init__(
            type=obj["type"],
            name=obj["name"],
            params=default_str(obj, "params"),
            code=default_str(obj, "code"),
        )

    def is_container(self):
        return self.type in [
            "Module",
            "Sequential",
            "ModuleList",
            "ModuleDict",
            "ParameterList",
        ]


class Model(BaseModel):
    id: int
    name: str
    desc: str
    layers: list[Component]
    loss_fn: Component
    optimizer: Component

    def __init__(self, id, name, desc, loss_fn_raw, optimizer_raw) -> None:
        super().__init__(
            id=id,
            name=name,
            desc=desc,
            layers=[],
            loss_fn=Component(loss_fn_raw),
            optimizer=Component(optimizer_raw),
        )

    def append_layer(self, json_raw) -> None:
        self.layers.append(Component(json_raw))

    def get_source_classname(self):
        return self.name[0].upper() + self.name[1:]

    def get_source_name(self):
        return self.name.lower()


def get_model_from_db(model_id: int, db: Connection) -> Model:
    try:
        cursor = db.cursor()

        cursor.execute(f"SELECT * FROM ML_MODEL WHERE ID={model_id}")
        result = cursor.fetchone()

        if not result:
            raise HTTPException(status_code=404, detail="model not found")

        model = Model(*result)

        cursor.execute(f"SELECT LAYER FROM ML_MODEL_LAYER WHERE MID={model_id}")
        result = cursor.fetchall()

        for (json_raw,) in result:
            model.append_layer(json_raw)

        return model
    finally:
        cursor.close()


def get_inference_image_from_db(req: RequestInferenceImage, db: Connection) -> Tensor:
    try:
        cursor = db.cursor()

        cursor.execute(f"SELECT DATA FROM ML_INFERENCE WHERE ID={req.data_id}")
        result = cursor.fetchone()

        if not result:
            raise HTTPException(
                status_code=404, detail="inference input data not found"
            )

        (blob,) = result
        image = Image.open(io.BytesIO(bytes(blob.getBytes(1, int(blob.length())))))
        transform = transforms.Compose(
            [transforms.Resize((req.width, req.height)), transforms.ToTensor()]
        )

        return transform(image).unsqueeze(0)
    finally:
        cursor.close()
