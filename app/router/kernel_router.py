#!/usr/bin/env python
# -*- coding: utf-8 -*-
# app/routes/kernel_route.py

from fastapi import APIRouter, Depends, status

from app.config.kernel import KernelClient, get_client

router = APIRouter(prefix="/kernels", tags=["Kernel"])


@router.post("/", status_code=status.HTTP_201_CREATED)
async def create_kernel(kc: KernelClient = Depends(get_client)):
    await kc.create_kernel()
