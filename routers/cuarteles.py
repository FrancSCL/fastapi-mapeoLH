from datetime import date
from typing import Optional
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from db import get_db
from auth import get_current_user

router = APIRouter()

CUARTEL_FIELDS = """
    id, id_ceco, nombre, id_variedad, superficie, ano_plantacion,
    dsh, deh, id_propiedad, id_portainjerto, subdivisionesplanta, id_estado,
    fecha_baja, id_estadoproductivo, n_hileras, id_estadocatastro, id_tiposubdivision
"""


class CuartelCreate(BaseModel):
    id_ceco: int
    nombre: str
    id_variedad: int
    superficie: float
    ano_plantacion: int
    dsh: Optional[float] = None
    deh: Optional[float] = None
    id_propiedad: Optional[int] = None
    id_portainjerto: Optional[int] = None
    subdivisionesplanta: Optional[int] = None
    id_estado: int = 1
    fecha_baja: Optional[date] = None
    id_estadoproductivo: Optional[int] = None
    n_hileras: Optional[int] = None
    id_estadocatastro: Optional[int] = None
    id_tiposubdivision: Optional[int] = None


class CuartelUpdate(BaseModel):
    id_ceco: Optional[int] = None
    nombre: Optional[str] = None
    id_variedad: Optional[int] = None
    superficie: Optional[float] = None
    ano_plantacion: Optional[int] = None
    dsh: Optional[float] = None
    deh: Optional[float] = None
    id_propiedad: Optional[int] = None
    id_portainjerto: Optional[int] = None
    subdivisionesplanta: Optional[int] = None
    id_estado: Optional[int] = None
    fecha_baja: Optional[date] = None
    id_estadoproductivo: Optional[int] = None
    n_hileras: Optional[int] = None
    id_estadocatastro: Optional[int] = None
    id_tiposubdivision: Optional[int] = None


@router.get("/")
def obtener_cuarteles(_: str = Depends(get_current_user)):
    try:
        with get_db() as conn:
            with conn.cursor() as cur:
                cur.execute(f"SELECT {CUARTEL_FIELDS} FROM general_dim_cuartel ORDER BY nombre ASC")
                return cur.fetchall()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/activos")
def obtener_cuarteles_activos(_: str = Depends(get_current_user)):
    try:
        with get_db() as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    SELECT c.id, c.id_ceco, c.nombre, c.id_variedad, c.superficie, c.ano_plantacion,
                           c.dsh, c.deh, c.id_propiedad, c.id_portainjerto, c.subdivisionesplanta, c.id_estado,
                           c.fecha_baja, c.id_estadoproductivo, c.n_hileras, c.id_estadocatastro, c.id_tiposubdivision,
                           ce.nombre as ceco_nombre, ce.id_sucursal, s.nombre as sucursal_nombre
                    FROM general_dim_cuartel c
                    LEFT JOIN general_dim_ceco ce ON c.id_ceco = ce.id
                    LEFT JOIN general_dim_sucursal s ON ce.id_sucursal = s.id
                    WHERE c.id_estado = 1
                    ORDER BY c.nombre ASC
                """)
                return cur.fetchall()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/catastro-finalizado")
def obtener_cuarteles_catastro_finalizado(_: str = Depends(get_current_user)):
    try:
        with get_db() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    f"SELECT {CUARTEL_FIELDS} FROM general_dim_cuartel "
                    "WHERE id_estadocatastro = 3 AND id_estado = 1 ORDER BY nombre ASC"
                )
                return cur.fetchall()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/sucursal/{sucursal_id}")
def obtener_cuarteles_por_sucursal(sucursal_id: int, _: str = Depends(get_current_user)):
    try:
        with get_db() as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    SELECT c.id, c.id_ceco, c.nombre, c.id_variedad, c.superficie, c.ano_plantacion,
                           c.dsh, c.deh, c.id_propiedad, c.id_portainjerto, c.subdivisionesplanta, c.id_estado,
                           c.fecha_baja, c.id_estadoproductivo, c.n_hileras, c.id_estadocatastro, c.id_tiposubdivision,
                           ce.nombre as ceco_nombre, ce.id_sucursal, s.nombre as sucursal_nombre
                    FROM general_dim_cuartel c
                    LEFT JOIN general_dim_ceco ce ON c.id_ceco = ce.id
                    LEFT JOIN general_dim_sucursal s ON ce.id_sucursal = s.id
                    WHERE c.id_estado = 1 AND ce.id_sucursal = %s
                    ORDER BY c.nombre ASC
                """, (sucursal_id,))
                return cur.fetchall()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/ceco/{ceco_id}")
def obtener_cuarteles_por_ceco(ceco_id: int, _: str = Depends(get_current_user)):
    try:
        with get_db() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    f"SELECT {CUARTEL_FIELDS} FROM general_dim_cuartel WHERE id_ceco = %s ORDER BY nombre ASC",
                    (ceco_id,),
                )
                return cur.fetchall()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/variedad/{variedad_id}")
def obtener_cuarteles_por_variedad(variedad_id: int, _: str = Depends(get_current_user)):
    try:
        with get_db() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    f"SELECT {CUARTEL_FIELDS} FROM general_dim_cuartel WHERE id_variedad = %s ORDER BY nombre ASC",
                    (variedad_id,),
                )
                return cur.fetchall()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/buscar/{nombre}")
def buscar_cuarteles(nombre: str, _: str = Depends(get_current_user)):
    try:
        with get_db() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    f"SELECT {CUARTEL_FIELDS} FROM general_dim_cuartel WHERE nombre LIKE %s ORDER BY nombre ASC",
                    (f"%{nombre}%",),
                )
                return cur.fetchall()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{cuartel_id}")
def obtener_cuartel(cuartel_id: int, _: str = Depends(get_current_user)):
    try:
        with get_db() as conn:
            with conn.cursor() as cur:
                cur.execute(f"SELECT {CUARTEL_FIELDS} FROM general_dim_cuartel WHERE id = %s", (cuartel_id,))
                result = cur.fetchone()
        if not result:
            raise HTTPException(status_code=404, detail="Cuartel no encontrado")
        return result
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/", status_code=201)
def crear_cuartel(body: CuartelCreate, _: str = Depends(get_current_user)):
    try:
        with get_db() as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    INSERT INTO general_dim_cuartel
                    (id_ceco, nombre, id_variedad, superficie, ano_plantacion, dsh, deh,
                     id_propiedad, id_portainjerto, subdivisionesplanta, id_estado, fecha_baja,
                     id_estadoproductivo, n_hileras, id_estadocatastro, id_tiposubdivision)
                    VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
                """, (body.id_ceco, body.nombre, body.id_variedad, body.superficie, body.ano_plantacion,
                      body.dsh, body.deh, body.id_propiedad, body.id_portainjerto, body.subdivisionesplanta,
                      body.id_estado, body.fecha_baja, body.id_estadoproductivo, body.n_hileras,
                      body.id_estadocatastro, body.id_tiposubdivision))
                new_id = cur.lastrowid
        return {"message": "Cuartel creado exitosamente", "id": new_id}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/{cuartel_id}")
def actualizar_cuartel(cuartel_id: int, body: CuartelUpdate, _: str = Depends(get_current_user)):
    try:
        data = body.model_dump(exclude_none=True)
        if not data:
            raise HTTPException(status_code=400, detail="No hay campos para actualizar")
        with get_db() as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT id FROM general_dim_cuartel WHERE id = %s", (cuartel_id,))
                if not cur.fetchone():
                    raise HTTPException(status_code=404, detail="Cuartel no encontrado")
                sets = ", ".join(f"{k} = %s" for k in data)
                cur.execute(
                    f"UPDATE general_dim_cuartel SET {sets} WHERE id = %s",
                    list(data.values()) + [cuartel_id],
                )
        return {"message": "Cuartel actualizado exitosamente", "id": cuartel_id}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.patch("/{cuartel_id}/verificar-estado")
def verificar_estado_catastro(cuartel_id: int, _: str = Depends(get_current_user)):
    """Verifica y actualiza id_estadocatastro basado en datos reales.
    No modifica cuarteles ya en estado FINALIZADO (3).
    """
    try:
        with get_db() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    "SELECT id_estadocatastro FROM general_dim_cuartel WHERE id = %s",
                    (cuartel_id,),
                )
                row = cur.fetchone()
                if not row:
                    raise HTTPException(status_code=404, detail="Cuartel no encontrado")
                if row["id_estadocatastro"] == 3:
                    return {"estado": 3, "actualizado": False}
                cur.execute("""
                    SELECT EXISTS (
                        SELECT 1
                        FROM general_dim_planta p
                        JOIN general_dim_hilera h ON p.id_hilera = h.id
                        WHERE h.id_cuartel = %s
                    ) AS tiene_plantas
                """, (cuartel_id,))
                tiene_plantas = cur.fetchone()["tiene_plantas"]
                nuevo_estado = 2 if tiene_plantas else 1
                cur.execute(
                    "UPDATE general_dim_cuartel SET id_estadocatastro = %s WHERE id = %s AND id_estadocatastro != 3",
                    (nuevo_estado, cuartel_id),
                )
        return {"estado": nuevo_estado, "actualizado": True}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/{cuartel_id}")
def eliminar_cuartel(cuartel_id: int, _: str = Depends(get_current_user)):
    try:
        with get_db() as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT id FROM general_dim_cuartel WHERE id = %s", (cuartel_id,))
                if not cur.fetchone():
                    raise HTTPException(status_code=404, detail="Cuartel no encontrado")
                cur.execute(
                    "UPDATE general_dim_cuartel SET id_estado = 0, fecha_baja = %s WHERE id = %s",
                    (date.today(), cuartel_id),
                )
        return {"message": "Cuartel eliminado exitosamente", "id": cuartel_id}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
