from typing import Optional, List
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from db import get_db
from auth import get_current_user, require_admin

router = APIRouter()


class PerfilUpdate(BaseModel):
    nombre: Optional[str] = None
    apellido_paterno: Optional[str] = None
    apellido_materno: Optional[str] = None
    correo: Optional[str] = None


class SucursalActivaBody(BaseModel):
    id_sucursal: int


class SucursalesBody(BaseModel):
    sucursales_ids: List[int]


class AppsBody(BaseModel):
    apps_ids: List[int]


@router.get("/")
def obtener_usuarios(_: str = Depends(require_admin)):
    try:
        with get_db() as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    SELECT u.id, u.usuario, u.correo, u.nombre, u.apellido_paterno, u.apellido_materno,
                           u.id_sucursalactiva, u.id_estado, u.id_rol, u.id_perfil, u.fecha_creacion,
                           s.nombre AS nombre_sucursal
                    FROM general_dim_usuario u
                    LEFT JOIN general_dim_sucursal s ON u.id_sucursalactiva = s.id
                """)
                return cur.fetchall()
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/sucursal-activa")
def obtener_sucursal_activa(usuario_id: str = Depends(get_current_user)):
    try:
        with get_db() as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT id_sucursalactiva FROM general_dim_usuario WHERE id = %s", (usuario_id,))
                u = cur.fetchone()
        if not u or u["id_sucursalactiva"] is None:
            raise HTTPException(status_code=404, detail="No se encontró la sucursal activa")
        return {"sucursal_activa": u["id_sucursalactiva"]}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# Alias para compatibilidad con código que llama /sucursal
@router.get("/sucursal")
def obtener_sucursal_usuario(usuario_id: str = Depends(get_current_user)):
    return obtener_sucursal_activa(usuario_id)


@router.post("/sucursal-activa")
def actualizar_sucursal_activa(body: SucursalActivaBody, usuario_id: str = Depends(get_current_user)):
    try:
        with get_db() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    "SELECT 1 FROM usuario_pivot_sucursal_usuario WHERE id_usuario = %s AND id_sucursal = %s",
                    (usuario_id, body.id_sucursal),
                )
                if not cur.fetchone():
                    raise HTTPException(status_code=403, detail="No tienes acceso a esta sucursal")
                cur.execute(
                    "UPDATE general_dim_usuario SET id_sucursalactiva = %s WHERE id = %s",
                    (body.id_sucursal, usuario_id),
                )
                cur.execute("SELECT nombre FROM general_dim_sucursal WHERE id = %s", (body.id_sucursal,))
                sucursal = cur.fetchone()
        return {
            "message": "Sucursal actualizada correctamente",
            "id_sucursal": body.id_sucursal,
            "sucursal_nombre": sucursal["nombre"] if sucursal else None,
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/sucursales")
def obtener_sucursales(_: str = Depends(require_admin)):
    try:
        with get_db() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    "SELECT id, nombre, ubicacion FROM general_dim_sucursal WHERE id_sucursaltipo = 1 ORDER BY nombre ASC"
                )
                return cur.fetchall()
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/perfil")
def obtener_perfil(usuario_id: str = Depends(get_current_user)):
    try:
        with get_db() as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    SELECT u.id, u.usuario, u.correo, u.nombre, u.apellido_paterno, u.apellido_materno,
                           CONCAT(u.nombre, ' ', u.apellido_paterno, ' ', COALESCE(u.apellido_materno, '')) as nombre_completo,
                           u.id_sucursalactiva, u.id_estado, u.id_rol, u.id_perfil, u.fecha_creacion,
                           s.nombre AS nombre_sucursal
                    FROM general_dim_usuario u
                    LEFT JOIN general_dim_sucursal s ON u.id_sucursalactiva = s.id
                    WHERE u.id = %s
                """, (usuario_id,))
                result = cur.fetchone()
        if not result:
            raise HTTPException(status_code=404, detail="Usuario no encontrado")
        return result
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/perfil")
def actualizar_perfil(body: PerfilUpdate, usuario_id: str = Depends(get_current_user)):
    ALLOWED = {"nombre", "apellido_paterno", "apellido_materno", "correo"}
    try:
        data = {k: v for k, v in body.model_dump(exclude_none=True).items() if k in ALLOWED}
        if not data:
            raise HTTPException(status_code=400, detail="Al menos un campo debe ser proporcionado")
        with get_db() as conn:
            with conn.cursor() as cur:
                sets = ", ".join(f"{k} = %s" for k in data)
                cur.execute(
                    f"UPDATE general_dim_usuario SET {sets} WHERE id = %s",
                    list(data.values()) + [usuario_id],
                )
                cur.execute("""
                    SELECT u.id, u.usuario, u.correo, u.nombre, u.apellido_paterno, u.apellido_materno,
                           CONCAT(u.nombre, ' ', u.apellido_paterno, ' ', COALESCE(u.apellido_materno, '')) as nombre_completo,
                           u.id_sucursalactiva, u.id_estado, u.id_rol, u.id_perfil, u.fecha_creacion,
                           s.nombre AS nombre_sucursal
                    FROM general_dim_usuario u
                    LEFT JOIN general_dim_sucursal s ON u.id_sucursalactiva = s.id
                    WHERE u.id = %s
                """, (usuario_id,))
                updated = cur.fetchone()
        return {"message": "Perfil actualizado correctamente", "usuario": updated}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/apps")
def obtener_apps(_: str = Depends(require_admin)):
    try:
        with get_db() as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT id, nombre FROM general_dim_app ORDER BY nombre ASC")
                return cur.fetchall()
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{target_usuario_id}/sucursales-permitidas")
def obtener_sucursales_permitidas(target_usuario_id: str, _: str = Depends(require_admin)):
    try:
        with get_db() as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    SELECT s.id, s.nombre, s.ubicacion FROM general_dim_sucursal s
                    INNER JOIN usuario_pivot_sucursal_usuario p ON s.id = p.id_sucursal
                    WHERE p.id_usuario = %s AND s.id_sucursaltipo = 1 ORDER BY s.nombre ASC
                """, (target_usuario_id,))
                return cur.fetchall()
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{target_usuario_id}/sucursales-permitidas")
def asignar_sucursales_permitidas(
    target_usuario_id: str, body: SucursalesBody, _: str = Depends(require_admin)
):
    try:
        with get_db() as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT id FROM general_dim_usuario WHERE id = %s", (target_usuario_id,))
                if not cur.fetchone():
                    raise HTTPException(status_code=404, detail="Usuario no encontrado")
                cur.execute("DELETE FROM usuario_pivot_sucursal_usuario WHERE id_usuario = %s", (target_usuario_id,))
                if body.sucursales_ids:
                    cur.executemany(
                        "INSERT INTO usuario_pivot_sucursal_usuario (id_sucursal, id_usuario) VALUES (%s, %s)",
                        [(sid, target_usuario_id) for sid in body.sucursales_ids],
                    )
        return {
            "message": "Sucursales asignadas correctamente",
            "usuario_id": target_usuario_id,
            "sucursales_asignadas": len(body.sucursales_ids),
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/{target_usuario_id}/sucursales-permitidas")
def eliminar_sucursales_permitidas(target_usuario_id: str, _: str = Depends(require_admin)):
    try:
        with get_db() as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT id FROM general_dim_usuario WHERE id = %s", (target_usuario_id,))
                if not cur.fetchone():
                    raise HTTPException(status_code=404, detail="Usuario no encontrado")
                cur.execute("DELETE FROM usuario_pivot_sucursal_usuario WHERE id_usuario = %s", (target_usuario_id,))
                eliminadas = cur.rowcount
        return {"message": "Sucursales eliminadas correctamente", "sucursales_eliminadas": eliminadas}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{target_usuario_id}/apps-permitidas")
def obtener_apps_permitidas(target_usuario_id: str, _: str = Depends(require_admin)):
    try:
        with get_db() as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    SELECT a.id, a.nombre FROM general_dim_app a
                    INNER JOIN usuario_pivot_app_usuario p ON a.id = p.id_app
                    WHERE p.id_usuario = %s ORDER BY a.nombre ASC
                """, (target_usuario_id,))
                return cur.fetchall()
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{target_usuario_id}/apps-permitidas")
def asignar_apps_permitidas(
    target_usuario_id: str, body: AppsBody, _: str = Depends(require_admin)
):
    import uuid as _uuid
    try:
        with get_db() as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT id FROM general_dim_usuario WHERE id = %s", (target_usuario_id,))
                if not cur.fetchone():
                    raise HTTPException(status_code=404, detail="Usuario no encontrado")
                cur.execute("DELETE FROM usuario_pivot_app_usuario WHERE id_usuario = %s", (target_usuario_id,))
                if body.apps_ids:
                    cur.executemany(
                        "INSERT INTO usuario_pivot_app_usuario (id, id_usuario, id_app) VALUES (%s, %s, %s)",
                        [(str(_uuid.uuid4()), target_usuario_id, app_id) for app_id in body.apps_ids],
                    )
        return {
            "message": "Apps asignadas correctamente",
            "usuario_id": target_usuario_id,
            "apps_asignadas": len(body.apps_ids),
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/{target_usuario_id}/apps-permitidas")
def eliminar_apps_permitidas(target_usuario_id: str, _: str = Depends(require_admin)):
    try:
        with get_db() as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT id FROM general_dim_usuario WHERE id = %s", (target_usuario_id,))
                if not cur.fetchone():
                    raise HTTPException(status_code=404, detail="Usuario no encontrado")
                cur.execute("DELETE FROM usuario_pivot_app_usuario WHERE id_usuario = %s", (target_usuario_id,))
                eliminadas = cur.rowcount
        return {"message": "Apps eliminadas correctamente", "apps_eliminadas": eliminadas}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
