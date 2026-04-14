from datetime import datetime
from typing import Optional
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
import uuid
from db import get_db
from auth import get_current_user

router = APIRouter()

_FIELDS = "id, id_evaluador, hora_registro, id_planta, id_tipoplanta, imagen, id_mapeo FROM mapeo_fact_registro"


class RegistroCreate(BaseModel):
    id_planta: int
    id_tipoplanta: int
    imagen: Optional[str] = None
    id_mapeo: Optional[str] = None


class RegistroUpdate(BaseModel):
    id_planta: Optional[int] = None
    id_tipoplanta: Optional[int] = None
    imagen: Optional[str] = None
    id_mapeo: Optional[str] = None


@router.get("/")
def obtener_registros(_: str = Depends(get_current_user)):
    try:
        with get_db() as conn:
            with conn.cursor() as cur:
                cur.execute(f"SELECT {_FIELDS} ORDER BY hora_registro DESC")
                return cur.fetchall()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/evaluador/{evaluador_id}")
def obtener_por_evaluador(evaluador_id: str, _: str = Depends(get_current_user)):
    try:
        with get_db() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    f"SELECT {_FIELDS} WHERE id_evaluador = %s ORDER BY hora_registro DESC",
                    (evaluador_id,),
                )
                return cur.fetchall()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/planta/{planta_id}")
def obtener_por_planta(planta_id: str, _: str = Depends(get_current_user)):
    try:
        with get_db() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    f"SELECT {_FIELDS} WHERE id_planta = %s ORDER BY hora_registro DESC",
                    (planta_id,),
                )
                return cur.fetchall()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/hilera/{hilera_id}")
def obtener_por_hilera(hilera_id: int, _: str = Depends(get_current_user)):
    try:
        with get_db() as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    SELECT r.id, r.id_evaluador, r.hora_registro, r.id_planta, r.id_tipoplanta, r.imagen, r.id_mapeo,
                           p.planta as numero_planta, p.ubicacion, tp.nombre as tipo_planta_nombre
                    FROM mapeo_fact_registro r
                    INNER JOIN general_dim_planta p ON r.id_planta = p.id
                    LEFT JOIN mapeo_dim_tipoplanta tp ON r.id_tipoplanta = tp.id
                    WHERE p.id_hilera = %s
                    ORDER BY p.planta ASC, r.hora_registro DESC
                """, (hilera_id,))
                return cur.fetchall()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/mapeo/{mapeo_id}")
def obtener_por_mapeo(mapeo_id: str, _: str = Depends(get_current_user)):
    try:
        with get_db() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    f"SELECT {_FIELDS} WHERE id_mapeo = %s ORDER BY hora_registro DESC",
                    (mapeo_id,),
                )
                return cur.fetchall()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{registro_id}")
def obtener_registro(registro_id: str, _: str = Depends(get_current_user)):
    try:
        with get_db() as conn:
            with conn.cursor() as cur:
                cur.execute(f"SELECT {_FIELDS} WHERE id = %s", (registro_id,))
                result = cur.fetchone()
        if not result:
            raise HTTPException(status_code=404, detail="Registro no encontrado")
        return result
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/", status_code=201)
def crear_registro(body: RegistroCreate, usuario_id: str = Depends(get_current_user)):
    try:
        registro_id = str(uuid.uuid4())
        with get_db() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    "INSERT INTO mapeo_fact_registro "
                    "(id, id_evaluador, hora_registro, id_planta, id_tipoplanta, imagen, id_mapeo) "
                    "VALUES (%s,%s,%s,%s,%s,%s,%s)",
                    (registro_id, usuario_id, datetime.now(), body.id_planta, body.id_tipoplanta, body.imagen, body.id_mapeo),
                )
        return {"message": "Registro creado exitosamente", "id": registro_id}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/{registro_id}")
def actualizar_registro(registro_id: str, body: RegistroUpdate, _: str = Depends(get_current_user)):
    try:
        data = body.model_dump(exclude_none=True)
        if not data:
            raise HTTPException(status_code=400, detail="No hay campos para actualizar")
        with get_db() as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT id FROM mapeo_fact_registro WHERE id = %s", (registro_id,))
                if not cur.fetchone():
                    raise HTTPException(status_code=404, detail="Registro no encontrado")
                sets = ", ".join(f"{k} = %s" for k in data)
                cur.execute(
                    f"UPDATE mapeo_fact_registro SET {sets} WHERE id = %s",
                    list(data.values()) + [registro_id],
                )
        return {"message": "Registro actualizado exitosamente", "id": registro_id}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/{registro_id}")
def eliminar_registro(registro_id: str, _: str = Depends(get_current_user)):
    try:
        with get_db() as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT id FROM mapeo_fact_registro WHERE id = %s", (registro_id,))
                if not cur.fetchone():
                    raise HTTPException(status_code=404, detail="Registro no encontrado")
                cur.execute("DELETE FROM mapeo_fact_registro WHERE id = %s", (registro_id,))
        return {"message": "Registro eliminado exitosamente", "id": registro_id}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
