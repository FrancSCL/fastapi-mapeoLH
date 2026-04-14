from datetime import datetime
from typing import Optional
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
import uuid
from db import get_db
from auth import get_current_user

router = APIRouter()


class RegistroMapeoCreate(BaseModel):
    id_temporada: int
    id_cuartel: int
    fecha_inicio: str
    id_estado: int
    fecha_termino: Optional[str] = None


class RegistroMapeoUpdate(BaseModel):
    id_temporada: Optional[int] = None
    id_cuartel: Optional[int] = None
    fecha_inicio: Optional[str] = None
    fecha_termino: Optional[str] = None
    id_estado: Optional[int] = None


class FinalizarMapeoBody(BaseModel):
    fecha_termino: Optional[str] = None
    estado: Optional[int] = None


def _parse_date(value: str, field: str):
    try:
        return datetime.strptime(value, "%Y-%m-%d").date()
    except ValueError:
        raise HTTPException(status_code=400, detail=f"La fecha {field} debe estar en formato YYYY-MM-DD")


@router.get("/estadisticas")
def obtener_estadisticas(_: str = Depends(get_current_user)):
    try:
        with get_db() as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    SELECT
                        COUNT(*) as total,
                        SUM(id_estado = 1) as en_progreso,
                        SUM(id_estado = 2) as finalizados,
                        SUM(id_estado = 3) as pausados
                    FROM mapeo_fact_registromapeo
                """)
                row = cur.fetchone()
        total = row["total"] or 0
        finalizados = row["finalizados"] or 0
        return {
            "total_registros": total,
            "en_progreso": row["en_progreso"] or 0,
            "finalizados": finalizados,
            "pausados": row["pausados"] or 0,
            "porcentaje_completado_general": round(finalizados / total * 100, 2) if total > 0 else 0,
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/temporada/{temporada_id}")
def obtener_por_temporada(temporada_id: int, _: str = Depends(get_current_user)):
    try:
        with get_db() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    "SELECT id, id_temporada, id_cuartel, fecha_inicio, fecha_termino, id_estado "
                    "FROM mapeo_fact_registromapeo WHERE id_temporada = %s ORDER BY fecha_inicio DESC",
                    (temporada_id,),
                )
                return cur.fetchall()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/cuartel/{cuartel_id}")
def obtener_por_cuartel(cuartel_id: int, _: str = Depends(get_current_user)):
    try:
        with get_db() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    "SELECT id, id_temporada, id_cuartel, fecha_inicio, fecha_termino, id_estado "
                    "FROM mapeo_fact_registromapeo WHERE id_cuartel = %s ORDER BY fecha_inicio DESC",
                    (cuartel_id,),
                )
                return cur.fetchall()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/estado/{estado_id}")
def obtener_por_estado(estado_id: int, _: str = Depends(get_current_user)):
    try:
        with get_db() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    "SELECT id, id_temporada, id_cuartel, fecha_inicio, fecha_termino, id_estado "
                    "FROM mapeo_fact_registromapeo WHERE id_estado = %s ORDER BY fecha_inicio DESC",
                    (estado_id,),
                )
                return cur.fetchall()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{registro_id}/progreso")
def obtener_progreso(registro_id: str, _: str = Depends(get_current_user)):
    """Progreso del mapeo por hilera. Antes: N*2+1 queries. Ahora: 2 queries."""
    try:
        with get_db() as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    SELECT rm.id_cuartel, c.nombre as nombre_cuartel
                    FROM mapeo_fact_registromapeo rm
                    LEFT JOIN general_dim_cuartel c ON rm.id_cuartel = c.id
                    WHERE rm.id = %s
                """, (registro_id,))
                registro = cur.fetchone()
                if not registro:
                    raise HTTPException(status_code=404, detail="Registro de mapeo no encontrado")

                cur.execute("""
                    SELECT
                        h.id AS id_hilera,
                        h.hilera,
                        COUNT(DISTINCT p.id)  AS total_plantas,
                        COUNT(DISTINCT r.id)  AS plantas_mapeadas
                    FROM general_dim_hilera h
                    LEFT JOIN general_dim_planta p ON p.id_hilera = h.id
                    LEFT JOIN mapeo_fact_registro r
                           ON r.id_planta = p.id AND r.id_mapeo = %s
                    WHERE h.id_cuartel = %s
                    GROUP BY h.id, h.hilera
                    ORDER BY h.hilera ASC
                """, (registro_id, registro["id_cuartel"]))
                hileras_data = cur.fetchall()

        hileras_completadas = 0
        hileras_con_progreso = []
        for h in hileras_data:
            total = h["total_plantas"]
            mapeadas = h["plantas_mapeadas"]
            if mapeadas == 0:
                estado = "pendiente"
            elif mapeadas >= total > 0:
                estado = "completado"
                hileras_completadas += 1
            else:
                estado = "en_progreso"
            hileras_con_progreso.append({
                "id_hilera": h["id_hilera"],
                "hilera": h["hilera"],
                "total_plantas": total,
                "plantas_mapeadas": mapeadas,
                "porcentaje": round(mapeadas / total * 100, 2) if total > 0 else 0,
                "estado": estado,
            })

        total_hileras = len(hileras_con_progreso)
        return {
            "id_registro": registro_id,
            "cuartel": registro["nombre_cuartel"],
            "total_hileras": total_hileras,
            "hileras_completadas": hileras_completadas,
            "porcentaje_general": round(hileras_completadas / total_hileras * 100, 2) if total_hileras > 0 else 0,
            "hileras": hileras_con_progreso,
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/")
def obtener_registros_mapeo(_: str = Depends(get_current_user)):
    try:
        with get_db() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    "SELECT id, id_temporada, id_cuartel, fecha_inicio, fecha_termino, id_estado "
                    "FROM mapeo_fact_registromapeo ORDER BY fecha_inicio DESC"
                )
                return cur.fetchall()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{registro_id}")
def obtener_registro_mapeo(registro_id: str, _: str = Depends(get_current_user)):
    try:
        with get_db() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    "SELECT id, id_temporada, id_cuartel, fecha_inicio, fecha_termino, id_estado "
                    "FROM mapeo_fact_registromapeo WHERE id = %s",
                    (registro_id,),
                )
                result = cur.fetchone()
        if not result:
            raise HTTPException(status_code=404, detail="Registro de mapeo no encontrado")
        return result
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/", status_code=201)
def crear_registro_mapeo(body: RegistroMapeoCreate, _: str = Depends(get_current_user)):
    try:
        fecha_inicio = _parse_date(body.fecha_inicio, "fecha_inicio")
        fecha_termino = _parse_date(body.fecha_termino, "fecha_termino") if body.fecha_termino else None
        registro_id = str(uuid.uuid4())
        with get_db() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    "INSERT INTO mapeo_fact_registromapeo "
                    "(id, id_temporada, id_cuartel, fecha_inicio, fecha_termino, id_estado) "
                    "VALUES (%s,%s,%s,%s,%s,%s)",
                    (registro_id, body.id_temporada, body.id_cuartel, fecha_inicio, fecha_termino, body.id_estado),
                )
        return {"mensaje": "Registro de mapeo creado exitosamente", "id": registro_id}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/{registro_id}")
def actualizar_registro_mapeo(registro_id: str, body: RegistroMapeoUpdate, _: str = Depends(get_current_user)):
    try:
        data = {}
        if body.id_temporada is not None:
            data["id_temporada"] = body.id_temporada
        if body.id_cuartel is not None:
            data["id_cuartel"] = body.id_cuartel
        if body.id_estado is not None:
            data["id_estado"] = body.id_estado
        if body.fecha_inicio is not None:
            data["fecha_inicio"] = _parse_date(body.fecha_inicio, "fecha_inicio")
        if body.fecha_termino is not None:
            data["fecha_termino"] = _parse_date(body.fecha_termino, "fecha_termino")
        if not data:
            raise HTTPException(status_code=400, detail="No hay campos para actualizar")

        with get_db() as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT id FROM mapeo_fact_registromapeo WHERE id = %s", (registro_id,))
                if not cur.fetchone():
                    raise HTTPException(status_code=404, detail="Registro de mapeo no encontrado")
                sets = ", ".join(f"{k} = %s" for k in data)
                cur.execute(
                    f"UPDATE mapeo_fact_registromapeo SET {sets} WHERE id = %s",
                    list(data.values()) + [registro_id],
                )
        return {"mensaje": "Registro de mapeo actualizado exitosamente"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/{registro_id}/finalizar")
def finalizar_registro_mapeo(registro_id: str, body: FinalizarMapeoBody, _: str = Depends(get_current_user)):
    try:
        id_estado = body.estado if body.estado is not None else 2
        if body.fecha_termino:
            try:
                fecha_termino = datetime.fromisoformat(body.fecha_termino.replace("Z", "+00:00")).date()
            except ValueError:
                fecha_termino = datetime.now().date()
        else:
            fecha_termino = datetime.now().date()

        with get_db() as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT id FROM mapeo_fact_registromapeo WHERE id = %s", (registro_id,))
                if not cur.fetchone():
                    raise HTTPException(status_code=404, detail="Registro de mapeo no encontrado")
                cur.execute(
                    "UPDATE mapeo_fact_registromapeo SET id_estado = %s, fecha_termino = %s WHERE id = %s",
                    (id_estado, fecha_termino, registro_id),
                )
        return {"mensaje": "Registro de mapeo finalizado exitosamente", "id": registro_id}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/{registro_id}")
def eliminar_registro_mapeo(registro_id: str, _: str = Depends(get_current_user)):
    try:
        with get_db() as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT id FROM mapeo_fact_registromapeo WHERE id = %s", (registro_id,))
                if not cur.fetchone():
                    raise HTTPException(status_code=404, detail="Registro de mapeo no encontrado")
                cur.execute("DELETE FROM mapeo_fact_registromapeo WHERE id = %s", (registro_id,))
        return {"mensaje": "Registro de mapeo eliminado exitosamente"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
