from fastapi import APIRouter, HTTPException, Depends
from db import get_db
from auth import get_current_user

router = APIRouter()


@router.get("/planta/{planta_id}")
def qr_planta(planta_id: int, _: str = Depends(get_current_user)):
    """Devuelve toda la info de una planta para la vista QR: planta + hilera + cuartel + ultimo mapeo."""
    try:
        with get_db() as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    SELECT p.id, p.planta AS numero_planta, p.ubicacion, p.fecha_creacion,
                           h.id AS hilera_id, h.hilera AS numero_hilera,
                           c.id AS cuartel_id, c.nombre AS cuartel_nombre,
                           v.nombre AS variedad_nombre,
                           e.nombre AS especie_nombre
                    FROM general_dim_planta p
                    JOIN general_dim_hilera h ON p.id_hilera = h.id
                    JOIN general_dim_cuartel c ON h.id_cuartel = c.id
                    LEFT JOIN general_dim_variedad v ON c.id_variedad = v.id
                    LEFT JOIN general_dim_especie e ON v.id_especie = e.id
                    WHERE p.id = %s
                """, (planta_id,))
                planta = cur.fetchone()

                if not planta:
                    raise HTTPException(status_code=404, detail="Planta no encontrada")

                # Obtener ultimo registro de mapeo para esta planta
                cur.execute("""
                    SELECT r.id AS registro_id, r.hora_registro, r.id_evaluador,
                           tp.id AS tipo_planta_id, tp.nombre AS tipo_planta_nombre,
                           r.imagen, r.id_mapeo
                    FROM mapeo_fact_registro r
                    LEFT JOIN mapeo_dim_tipoplanta tp ON r.id_tipoplanta = tp.id
                    WHERE r.id_planta = %s
                    ORDER BY r.hora_registro DESC
                    LIMIT 1
                """, (planta_id,))
                ultimo_mapeo = cur.fetchone()

                return {
                    **planta,
                    "ultimo_mapeo": ultimo_mapeo,
                }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/hilera/{hilera_id}")
def qr_hilera(hilera_id: int, _: str = Depends(get_current_user)):
    """Devuelve toda la info de una hilera para la vista QR: hilera + cuartel + resumen plantas + distribucion tipos."""
    try:
        with get_db() as conn:
            with conn.cursor() as cur:
                # Info de hilera + cuartel + conteos
                cur.execute("""
                    SELECT h.id, h.hilera AS numero_hilera,
                           c.id AS cuartel_id, c.nombre AS cuartel_nombre,
                           v.nombre AS variedad_nombre,
                           e.nombre AS especie_nombre,
                           COUNT(DISTINCT p.id) AS total_plantas,
                           COUNT(DISTINCT r.id_planta) AS plantas_mapeadas
                    FROM general_dim_hilera h
                    JOIN general_dim_cuartel c ON h.id_cuartel = c.id
                    LEFT JOIN general_dim_variedad v ON c.id_variedad = v.id
                    LEFT JOIN general_dim_especie e ON v.id_especie = e.id
                    LEFT JOIN general_dim_planta p ON p.id_hilera = h.id
                    LEFT JOIN mapeo_fact_registro r ON r.id_planta = p.id
                    WHERE h.id = %s
                    GROUP BY h.id, h.hilera, c.id, c.nombre, v.nombre, e.nombre
                """, (hilera_id,))
                hilera = cur.fetchone()

                if not hilera:
                    raise HTTPException(status_code=404, detail="Hilera no encontrada")

                # Distribucion por tipo de planta
                cur.execute("""
                    SELECT tp.id AS tipo_id, tp.nombre, COUNT(*) AS cantidad
                    FROM mapeo_fact_registro r
                    JOIN general_dim_planta p ON r.id_planta = p.id
                    JOIN mapeo_dim_tipoplanta tp ON r.id_tipoplanta = tp.id
                    WHERE p.id_hilera = %s
                    GROUP BY tp.id, tp.nombre
                    ORDER BY cantidad DESC
                """, (hilera_id,))
                tipos = cur.fetchall()

                return {
                    **hilera,
                    "tipos_planta": tipos,
                }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
