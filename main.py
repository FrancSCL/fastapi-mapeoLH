import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from routers import (
    auth, usuarios, cuarteles, hileras, plantas,
    variedades, especies, tipoplanta,
    registromapeo, registros, estadocatastro, opciones,
    qr,
)

app = FastAPI(title="API Mapeo Agrícola", version="3.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router,           prefix="/api/auth",           tags=["auth"])
app.include_router(usuarios.router,       prefix="/api/usuarios",       tags=["usuarios"])
app.include_router(cuarteles.router,      prefix="/api/cuarteles",      tags=["cuarteles"])
app.include_router(hileras.router,        prefix="/api/hileras",        tags=["hileras"])
app.include_router(plantas.router,        prefix="/api/plantas",        tags=["plantas"])
app.include_router(variedades.router,     prefix="/api/variedades",     tags=["variedades"])
app.include_router(especies.router,       prefix="/api/especies",       tags=["especies"])
app.include_router(tipoplanta.router,     prefix="/api/tipoplanta",     tags=["tipoplanta"])
app.include_router(registromapeo.router,  prefix="/api/registromapeo",  tags=["registromapeo"])
app.include_router(registros.router,      prefix="/api/registros",      tags=["registros"])
app.include_router(estadocatastro.router, prefix="/api/estadocatastro", tags=["estadocatastro"])
app.include_router(opciones.router,       prefix="/api/opciones",       tags=["opciones"])
app.include_router(qr.router,            prefix="/api/qr",             tags=["qr"])


@app.get("/")
def root():
    return {
        "message": "API de Mapeo Agrícola",
        "version": "3.0",
        "status": "active",
        "docs": "/docs",
    }


@app.get("/health")
def health():
    return {"status": "healthy", "version": "3.0"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=int(os.getenv("PORT", 8080)), reload=True)
