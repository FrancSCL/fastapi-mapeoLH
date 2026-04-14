from typing import Optional
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from db import get_db
from auth import get_current_user

router = APIRouter()


class VariedadCreate(BaseModel):
    nombre: str
    id_especie: int
    id_forma: int
    id_color: int


class VariedadUpdate(BaseModel):
    nombre: Optional[str] = None
    id_especie: Optional[int] = None
    id_forma: Optional[int] = None
    id_color: Optional[int] = None


@router.get("/")
def obtener_variedades(_: str = Depends(get_current_user)):
    try:
        with get_db() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    "SELECT id, nombre, id_especie, id_forma, id_color FROM general_dim_variedad ORDER BY nombre ASC"
                )
                return cur.fetchall()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{variedad_id}")
def obtener_variedad(variedad_id: int, _: str = Depends(get_current_user)):
    try:
        with get_db() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    "SELECT id, nombre, id_especie, id_forma, id_color FROM general_dim_variedad WHERE id = %s",
                    (variedad_id,),
                )
                result = cur.fetchone()
        if not result:
            raise HTTPException(status_code=404, detail="Variedad no encontrada")
        return result
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/", status_code=201)
def crear_variedad(body: VariedadCreate, _: str = Depends(get_current_user)):
    try:
        with get_db() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    "INSERT INTO general_dim_variedad (nombre, id_especie, id_forma, id_color) VALUES (%s,%s,%s,%s)",
                    (body.nombre, body.id_especie, body.id_forma, body.id_color),
                )
                new_id = cur.lastrowid
        return {"message": "Variedad creada exitosamente", "id": new_id}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/{variedad_id}")
def actualizar_variedad(variedad_id: int, body: VariedadUpdate, _: str = Depends(get_current_user)):
    try:
        data = body.model_dump(exclude_none=True)
        if not data:
            raise HTTPException(status_code=400, detail="No hay campos para actualizar")
        with get_db() as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT id FROM general_dim_variedad WHERE id = %s", (variedad_id,))
                if not cur.fetchone():
                    raise HTTPException(status_code=404, detail="Variedad no encontrada")
                sets = ", ".join(f"{k} = %s" for k in data)
                cur.execute(
                    f"UPDATE general_dim_variedad SET {sets} WHERE id = %s",
                    list(data.values()) + [variedad_id],
                )
        return {"message": "Variedad actualizada exitosamente", "id": variedad_id}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/{variedad_id}")
def eliminar_variedad(variedad_id: int, _: str = Depends(get_current_user)):
    try:
        with get_db() as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT id FROM general_dim_variedad WHERE id = %s", (variedad_id,))
                if not cur.fetchone():
                    raise HTTPException(status_code=404, detail="Variedad no encontrada")
                cur.execute("DELETE FROM general_dim_variedad WHERE id = %s", (variedad_id,))
        return {"message": "Variedad eliminada exitosamente", "id": variedad_id}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
