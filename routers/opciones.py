from fastapi import APIRouter, HTTPException, Depends
from db import get_db
from auth import get_current_user

router = APIRouter()


@router.get("/")
def opciones_root(_: str = Depends(get_current_user)):
    try:
        with get_db() as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT id, nombre FROM general_dim_labor ORDER BY nombre ASC")
                labores = cur.fetchall() or []
                cur.execute("SELECT id, nombre FROM tarja_dim_unidad WHERE id_estado = 1 ORDER BY nombre ASC")
                unidades = cur.fetchall() or []
                cur.execute("SELECT id, nombre FROM general_dim_cecotipo ORDER BY nombre ASC")
                tipoCecos = cur.fetchall() or []
        return {"labores": labores, "unidades": unidades, "tipoCecos": tipoCecos}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/sucursales")
def obtener_sucursales(usuario_id: str = Depends(get_current_user)):
    try:
        with get_db() as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    SELECT DISTINCT s.id, s.nombre, s.ubicacion
                    FROM general_dim_sucursal s
                    JOIN usuario_pivot_sucursal_usuario p ON s.id = p.id_sucursal
                    WHERE p.id_usuario = %s
                    ORDER BY s.nombre ASC
                """, (usuario_id,))
                return cur.fetchall() or []
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/empresas")
def obtener_empresas(_: str = Depends(get_current_user)):
    try:
        with get_db() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    "SELECT id, nombre, rut, codigo_verificador, fecha_suscripcion FROM general_dim_empresa ORDER BY nombre ASC"
                )
                return cur.fetchall() or []
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
