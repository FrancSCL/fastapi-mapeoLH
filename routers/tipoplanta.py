from fastapi import APIRouter, HTTPException, Depends
from db import get_db
from auth import get_current_user

router = APIRouter()

_FIELDS = "id, nombre, factor_productivo, id_empresa, descripcion FROM mapeo_dim_tipoplanta"


@router.get("/")
def obtener_tipos_planta(_: str = Depends(get_current_user)):
    try:
        with get_db() as conn:
            with conn.cursor() as cur:
                cur.execute(f"SELECT {_FIELDS} ORDER BY nombre ASC")
                return cur.fetchall()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/empresa/{empresa_id}")
def obtener_tipos_por_empresa(empresa_id: int, _: str = Depends(get_current_user)):
    try:
        with get_db() as conn:
            with conn.cursor() as cur:
                cur.execute(f"SELECT {_FIELDS} WHERE id_empresa = %s ORDER BY nombre ASC", (empresa_id,))
                return cur.fetchall()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/buscar/{nombre}")
def buscar_tipos_planta(nombre: str, _: str = Depends(get_current_user)):
    try:
        with get_db() as conn:
            with conn.cursor() as cur:
                cur.execute(f"SELECT {_FIELDS} WHERE nombre LIKE %s ORDER BY nombre ASC", (f"%{nombre}%",))
                return cur.fetchall()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{tipo_id}")
def obtener_tipo_planta(tipo_id: str, _: str = Depends(get_current_user)):
    try:
        with get_db() as conn:
            with conn.cursor() as cur:
                cur.execute(f"SELECT {_FIELDS} WHERE id = %s", (tipo_id,))
                result = cur.fetchone()
        if not result:
            raise HTTPException(status_code=404, detail="Tipo de planta no encontrado")
        return result
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
