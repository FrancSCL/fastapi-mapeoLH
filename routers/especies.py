from typing import Optional
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from db import get_db
from auth import get_current_user

router = APIRouter()


class EspecieCreate(BaseModel):
    nombre: str
    caja_equivalente: float


class EspecieUpdate(BaseModel):
    nombre: Optional[str] = None
    caja_equivalente: Optional[float] = None


@router.get("/")
def obtener_especies(_: str = Depends(get_current_user)):
    try:
        with get_db() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    "SELECT id, nombre, caja_equivalente FROM general_dim_especie ORDER BY nombre ASC"
                )
                return cur.fetchall()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{especie_id}")
def obtener_especie(especie_id: int, _: str = Depends(get_current_user)):
    try:
        with get_db() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    "SELECT id, nombre, caja_equivalente FROM general_dim_especie WHERE id = %s",
                    (especie_id,),
                )
                result = cur.fetchone()
        if not result:
            raise HTTPException(status_code=404, detail="Especie no encontrada")
        return result
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/", status_code=201)
def crear_especie(body: EspecieCreate, _: str = Depends(get_current_user)):
    try:
        with get_db() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    "INSERT INTO general_dim_especie (nombre, caja_equivalente) VALUES (%s, %s)",
                    (body.nombre, body.caja_equivalente),
                )
                new_id = cur.lastrowid
        return {"message": "Especie creada exitosamente", "id": new_id}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/{especie_id}")
def actualizar_especie(especie_id: int, body: EspecieUpdate, _: str = Depends(get_current_user)):
    try:
        data = body.model_dump(exclude_none=True)
        if not data:
            raise HTTPException(status_code=400, detail="No hay campos para actualizar")
        with get_db() as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT id FROM general_dim_especie WHERE id = %s", (especie_id,))
                if not cur.fetchone():
                    raise HTTPException(status_code=404, detail="Especie no encontrada")
                sets = ", ".join(f"{k} = %s" for k in data)
                cur.execute(
                    f"UPDATE general_dim_especie SET {sets} WHERE id = %s",
                    list(data.values()) + [especie_id],
                )
        return {"message": "Especie actualizada exitosamente", "id": especie_id}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/{especie_id}")
def eliminar_especie(especie_id: int, _: str = Depends(get_current_user)):
    try:
        with get_db() as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT id FROM general_dim_especie WHERE id = %s", (especie_id,))
                if not cur.fetchone():
                    raise HTTPException(status_code=404, detail="Especie no encontrada")
                cur.execute("DELETE FROM general_dim_especie WHERE id = %s", (especie_id,))
        return {"message": "Especie eliminada exitosamente", "id": especie_id}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
