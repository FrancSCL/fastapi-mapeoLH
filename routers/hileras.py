from typing import Optional
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from db import get_db
from auth import get_current_user

router = APIRouter()


class HileraCreate(BaseModel):
    hilera: int
    id_cuartel: int


class HileraUpdate(BaseModel):
    hilera: Optional[int] = None
    id_cuartel: Optional[int] = None


class MultiplesHileras(BaseModel):
    id_cuartel: int
    n_hileras: int


@router.get("/")
def obtener_hileras(_: str = Depends(get_current_user)):
    try:
        with get_db() as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT id, hilera, id_cuartel FROM general_dim_hilera ORDER BY hilera ASC")
                return cur.fetchall()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/con-cuartel")
def obtener_hileras_con_cuartel(_: str = Depends(get_current_user)):
    try:
        with get_db() as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    SELECT h.id, h.hilera, h.id_cuartel, c.nombre as nombre_cuartel
                    FROM general_dim_hilera h
                    LEFT JOIN general_dim_cuartel c ON h.id_cuartel = c.id
                    ORDER BY h.hilera ASC
                """)
                return cur.fetchall()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/cuartel/{cuartel_id}/progreso")
def obtener_progreso_hileras(cuartel_id: int, _: str = Depends(get_current_user)):
    """Retorna el conteo de plantas por hilera para un cuartel. 1 sola query SQL."""
    try:
        with get_db() as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    SELECT h.id, COUNT(p.id) AS n_plantas
                    FROM general_dim_hilera h
                    LEFT JOIN general_dim_planta p ON p.id_hilera = h.id
                    WHERE h.id_cuartel = %s
                    GROUP BY h.id
                """, (cuartel_id,))
                rows = cur.fetchall()
        return {row["id"]: row["n_plantas"] for row in rows}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/cuartel/{cuartel_id}/con-info")
def obtener_hileras_por_cuartel_con_info(cuartel_id: int, _: str = Depends(get_current_user)):
    try:
        with get_db() as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    SELECT h.id, h.hilera, h.id_cuartel, c.nombre as nombre_cuartel
                    FROM general_dim_hilera h
                    LEFT JOIN general_dim_cuartel c ON h.id_cuartel = c.id
                    WHERE h.id_cuartel = %s
                    ORDER BY h.hilera ASC
                """, (cuartel_id,))
                return cur.fetchall()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/cuartel/{cuartel_id}")
def obtener_hileras_por_cuartel(cuartel_id: int, _: str = Depends(get_current_user)):
    try:
        with get_db() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    "SELECT id, hilera, id_cuartel FROM general_dim_hilera WHERE id_cuartel = %s ORDER BY hilera ASC",
                    (cuartel_id,),
                )
                return cur.fetchall()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/numero/{numero_hilera}")
def obtener_hileras_por_numero(numero_hilera: int, _: str = Depends(get_current_user)):
    try:
        with get_db() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    "SELECT id, hilera, id_cuartel FROM general_dim_hilera WHERE hilera = %s ORDER BY hilera ASC",
                    (numero_hilera,),
                )
                return cur.fetchall()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{hilera_id}")
def obtener_hilera(hilera_id: int, _: str = Depends(get_current_user)):
    try:
        with get_db() as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT id, hilera, id_cuartel FROM general_dim_hilera WHERE id = %s", (hilera_id,))
                result = cur.fetchone()
        if not result:
            raise HTTPException(status_code=404, detail="Hilera no encontrada")
        return result
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/", status_code=201)
def crear_hilera(body: HileraCreate, _: str = Depends(get_current_user)):
    try:
        with get_db() as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT id FROM general_dim_cuartel WHERE id = %s", (body.id_cuartel,))
                if not cur.fetchone():
                    raise HTTPException(status_code=404, detail="Cuartel no encontrado")
                cur.execute(
                    "SELECT id FROM general_dim_hilera WHERE id_cuartel = %s AND hilera = %s",
                    (body.id_cuartel, body.hilera),
                )
                if cur.fetchone():
                    raise HTTPException(status_code=400, detail="Ya existe una hilera con ese número en este cuartel")
                cur.execute(
                    "INSERT INTO general_dim_hilera (hilera, id_cuartel) VALUES (%s, %s)",
                    (body.hilera, body.id_cuartel),
                )
                new_id = cur.lastrowid
        return {"message": "Hilera creada exitosamente", "id": new_id}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/agregar-multiples")
def agregar_multiples_hileras(body: MultiplesHileras, _: str = Depends(get_current_user)):
    try:
        with get_db() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    "SELECT COUNT(*) as total FROM general_dim_hilera WHERE id_cuartel = %s",
                    (body.id_cuartel,),
                )
                total_actual = cur.fetchone()["total"]
                nuevas = list(range(total_actual + 1, body.n_hileras + 1))
                if nuevas:
                    cur.executemany(
                        "INSERT INTO general_dim_hilera (hilera, id_cuartel) VALUES (%s, %s)",
                        [(i, body.id_cuartel) for i in nuevas],
                    )
                cur.execute(
                    "UPDATE general_dim_cuartel SET n_hileras = %s WHERE id = %s",
                    (max(body.n_hileras, total_actual), body.id_cuartel),
                )
        return {"message": f"Se agregaron {len(nuevas)} hileras nuevas", "hileras_agregadas": nuevas}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/{hilera_id}")
def actualizar_hilera(hilera_id: int, body: HileraUpdate, _: str = Depends(get_current_user)):
    try:
        data = body.model_dump(exclude_none=True)
        if not data:
            raise HTTPException(status_code=400, detail="No hay campos para actualizar")
        with get_db() as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT id FROM general_dim_hilera WHERE id = %s", (hilera_id,))
                if not cur.fetchone():
                    raise HTTPException(status_code=404, detail="Hilera no encontrada")
                sets = ", ".join(f"{k} = %s" for k in data)
                cur.execute(
                    f"UPDATE general_dim_hilera SET {sets} WHERE id = %s",
                    list(data.values()) + [hilera_id],
                )
        return {"message": "Hilera actualizada exitosamente", "id": hilera_id}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/{hilera_id}")
def eliminar_hilera(hilera_id: int, _: str = Depends(get_current_user)):
    try:
        with get_db() as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT id FROM general_dim_hilera WHERE id = %s", (hilera_id,))
                if not cur.fetchone():
                    raise HTTPException(status_code=404, detail="Hilera no encontrada")
                cur.execute("DELETE FROM general_dim_hilera WHERE id = %s", (hilera_id,))
        return {"message": "Hilera eliminada exitosamente", "id": hilera_id}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
