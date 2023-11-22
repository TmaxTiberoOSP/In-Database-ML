#!/usr/bin/env python
# -*- coding: utf-8 -*-
# app/routes/kernel_route.py

from typing import Annotated

from fastapi import APIRouter, Depends, Form, HTTPException, status

from app.config.kernel import KernelClient, get_client

router = APIRouter(prefix="/kernels", tags=["Kernel"])


@router.post("/", status_code=status.HTTP_201_CREATED)
async def create_kernel(kc: KernelClient = Depends(get_client)):
    kernel = await kc.create_kernel()

    return kernel.id


@router.post("/{id}")
async def execute_command(
    id: str, code: Annotated[str, Form()], kc: KernelClient = Depends(get_client)
):
    try:
        kernel = kc.get(id)
        result = await kernel.execute(code)

        return result
    except KeyError:
        raise HTTPException(status_code=404, detail="kernel not found")
