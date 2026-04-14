from datetime import date
from typing import Optional
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from db import get_db
from auth import get_current_user

router = APIRouter()


class PlantaCreate(BaseModel):
    id_hilera: int
    planta: int
    ubicacion: str


class PlantaUpdate(BaseModel):
    id_hilera: Optional[int] = None
    planta: Optional[int] = None
    ubicacion: Optional[str] = None


@router.get("/")
def obtener_plantas(_: str = Depends(get_current_user)):
    try:
        with get_db() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    "SELECT id, id_hilera, planta, ubicacion, fecha_creacion FROM general_dim_planta ORDER BY planta ASC"
                )
                return cur.fetchall()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/hilera/{hilera_id}")
def obtener_plantas_por_hilera(hilera_id: int, _: str = Depends(get_current_user)):
    try:
        with get_db() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    "SELECT id, id_hilera, planta, ubicacion, fecha_creacion FROM general_dim_planta "
                    "WHERE id_hilera = %s ORDER BY planta ASC",
                    (hilera_id,),
                )
                return cur.fetchall()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/ubicacion/{ubicacion}")
def buscar_plantas_por_ubicacion(ubicacion: str, _: str = Depends(get_current_user)):
    try:
        with get_db() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    "SELECT id, id_hilera, planta, ubicacion, fecha_creacion FROM general_dim_planta "
                    "WHERE ubicacion LIKE %s ORDER BY planta ASC",
                    (f"%{ubicacion}%",),
                )
                return cur.fetchall()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/numero/{numero_planta}")
def obtener_plantas_por_numero(numero_planta: int, _: str = Depends(get_current_user)):
    try:
        with get_db() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    "SELECT id, id_hilera, planta, ubicacion, fecha_creacion FROM general_dim_planta "
                    "WHERE planta = %s ORDER BY planta ASC",
                    (numero_planta,),
                )
                return cur.fetchall()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{planta_id}")
def obtener_planta(planta_id: str, _: str = Depends(get_current_user)):
    try:
        with get_db() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    "SELECT id, id_hilera, planta, ubicacion, fecha_creacion FROM general_dim_planta WHERE id = %s",
                    (planta_id,),
                )
                result = cur.fetchone()
        if not result:
            raise HTTPException(status_code=404, detail="Planta no encontrada")
        return result
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/", status_code=201)
def crear_planta(body: PlantaCreate, _: str = Depends(get_current_user)):
    try:
        with get_db() as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT id FROM general_dim_hilera WHERE id = %s", (body.id_hilera,))
                if not cur.fetchone():
                    raise HTTPException(status_code=404, detail="Hilera no encontrada")
                cur.execute(
                    "SELECT id FROM general_dim_planta WHERE id_hilera = %s AND planta = %s",
                    (body.id_hilera, body.planta),
                )
                if cur.fetchone():
                    raise HTTPException(status_code=400, detail="Ya existe una planta con ese número en esta hilera")
                cur.execute(
                    "INSERT INTO general_dim_planta (id_hilera, planta, ubicacion, fecha_creacion) VALUES (%s, %s, %s, %s)",
                    (body.id_hilera, body.planta, body.ubicacion, date.today()),
                )
                new_id = cur.lastrowid
        return {"message": "Planta creada exitosamente", "id": new_id}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/{planta_id}")
def actualizar_planta(planta_id: str, body: PlantaUpdate, _: str = Depends(get_current_user)):
    try:
        data = body.model_dump(exclude_none=True)
        if not data:
            raise HTTPException(status_code=400, detail="No hay campos para actualizar")
        with get_db() as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT id FROM general_dim_planta WHERE id = %s", (planta_id,))
                if not cur.fetchone():
                    raise HTTPException(status_code=404, detail="Planta no encontrada")
                sets = ", ".join(f"{k} = %s" for k in data)
                cur.execute(
                    f"UPDATE general_dim_planta SET {sets} WHERE id = %s",
                    list(data.values()) + [planta_id],
                )
        return {"message": "Planta actualizada exitosamente", "id": planta_id}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/{planta_id}")
def eliminar_planta(planta_id: str, _: str = Depends(get_current_user)):
    try:
        with get_db() as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT id FROM general_dim_planta WHERE id = %s", (planta_id,))
                if not cur.fetchone():
                    raise HTTPException(status_code=404, detail="Planta no encontrada")
                cur.execute("DELETE FROM general_dim_planta WHERE id = %s", (planta_id,))
        return {"message": "Planta eliminada exitosamente", "id": planta_id}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
