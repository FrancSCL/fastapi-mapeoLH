from fastapi import APIRouter, HTTPException, Depends
from db import get_db
from auth import get_current_user

router = APIRouter()


@router.get("/")
def obtener_estados_catastro(_: str = Depends(get_current_user)):
    try:
        with get_db() as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT id, nombre FROM mapeo_dim_estadocatastro ORDER BY nombre ASC")
                return cur.fetchall()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/buscar/{nombre}")
def buscar_estados_catastro(nombre: str, _: str = Depends(get_current_user)):
    try:
        with get_db() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    "SELECT id, nombre FROM mapeo_dim_estadocatastro WHERE nombre LIKE %s ORDER BY nombre ASC",
                    (f"%{nombre}%",),
                )
                return cur.fetchall()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{estado_id}")
def obtener_estado_catastro(estado_id: int, _: str = Depends(get_current_user)):
    try:
        with get_db() as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT id, nombre FROM mapeo_dim_estadocatastro WHERE id = %s", (estado_id,))
                result = cur.fetchone()
        if not result:
            raise HTTPException(status_code=404, detail="Estado de catastro no encontrado")
        return result
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
