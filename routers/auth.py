from datetime import date
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from db import get_db
from auth import verify_password, hash_password, create_access_token, create_refresh_token, decode_refresh_token, get_current_user

router = APIRouter()


class LoginBody(BaseModel):
    usuario: str
    clave: str


class RegisterBody(BaseModel):
    correo: str
    clave: str
    usuario: str
    nombre: str
    apellido_paterno: str
    apellido_materno: str = None
    id_sucursalactiva: int
    id_estado: int = 1
    id_rol: int = 3
    id_perfil: int = 1


class CambiarClaveBody(BaseModel):
    clave_actual: str
    nueva_clave: str


class CambiarSucursalBody(BaseModel):
    id_sucursal: int


@router.post("/register", status_code=201)
def register(body: RegisterBody):
    clave_hash = hash_password(body.clave)
    try:
        with get_db() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """INSERT INTO general_dim_usuario
                       (id, usuario, correo, clave, nombre, apellido_paterno, apellido_materno,
                        id_sucursalactiva, id_estado, id_rol, id_perfil, fecha_creacion)
                       VALUES (UUID(), %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)""",
                    (body.usuario, body.correo, clave_hash, body.nombre, body.apellido_paterno,
                     body.apellido_materno, body.id_sucursalactiva, body.id_estado,
                     body.id_rol, body.id_perfil, date.today()),
                )
        return {"message": "Usuario registrado correctamente"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/login")
def login(body: LoginBody):
    try:
        with get_db() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """SELECT u.*, s.nombre as sucursal_nombre,
                              CONCAT(u.nombre, ' ', u.apellido_paterno, ' ', COALESCE(u.apellido_materno, '')) as nombre_completo
                       FROM general_dim_usuario u
                       LEFT JOIN general_dim_sucursal s ON u.id_sucursalactiva = s.id
                       WHERE u.usuario = %s""",
                    (body.usuario,),
                )
                user = cur.fetchone()

                if not user:
                    raise HTTPException(status_code=401, detail="Usuario o clave incorrectos")
                if user["id_estado"] != 1:
                    raise HTTPException(status_code=403, detail="Usuario inactivo. Contacte al administrador")

                cur.execute(
                    "SELECT 1 FROM usuario_pivot_app_usuario WHERE id_usuario = %s AND id_app = 5",
                    (user["id"],),
                )
                if not cur.fetchone():
                    raise HTTPException(status_code=403, detail="Usuario sin acceso a esta aplicación")

                if not verify_password(body.clave, user["clave"]):
                    raise HTTPException(status_code=401, detail="Usuario o clave incorrectos")

        token = create_access_token(
            identity=user["id"],
            additional_claims={
                "rol": user["id_rol"],
                "perfil": user["id_perfil"],
                "sucursal": user["id_sucursalactiva"],
                "sucursal_nombre": user["sucursal_nombre"],
            },
        )
        refresh_token = create_refresh_token(identity=user["id"])
        return {
            "access_token": token,
            "refresh_token": refresh_token,
            "usuario": user["usuario"],
            "nombre_completo": user["nombre_completo"],
            "id_sucursal": user["id_sucursalactiva"],
            "sucursal_nombre": user["sucursal_nombre"],
            "id_rol": user["id_rol"],
            "id_perfil": user["id_perfil"],
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/refresh")
def refresh(usuario_id: str = Depends(decode_refresh_token)):
    try:
        with get_db() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """SELECT u.id_rol, u.id_perfil, u.id_sucursalactiva, s.nombre as sucursal_nombre
                       FROM general_dim_usuario u
                       LEFT JOIN general_dim_sucursal s ON u.id_sucursalactiva = s.id
                       WHERE u.id = %s AND u.id_estado = 1""",
                    (usuario_id,),
                )
                user = cur.fetchone()
        if not user:
            raise HTTPException(status_code=401, detail="Usuario inactivo o no encontrado")
        token = create_access_token(
            identity=usuario_id,
            additional_claims={
                "rol": user["id_rol"],
                "perfil": user["id_perfil"],
                "sucursal": user["id_sucursalactiva"],
                "sucursal_nombre": user["sucursal_nombre"],
            },
        )
        return {"access_token": token}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/cambiar-clave")
def cambiar_clave(body: CambiarClaveBody, usuario_id: str = Depends(get_current_user)):
    try:
        with get_db() as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT clave FROM general_dim_usuario WHERE id = %s", (usuario_id,))
                user = cur.fetchone()
                if not user or not verify_password(body.clave_actual, user["clave"]):
                    raise HTTPException(status_code=401, detail="Clave actual incorrecta")
                nueva_hash = hash_password(body.nueva_clave)
                cur.execute("UPDATE general_dim_usuario SET clave = %s WHERE id = %s", (nueva_hash, usuario_id))
        return {"message": "Clave actualizada correctamente"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/cambiar-sucursal")
def cambiar_sucursal(body: CambiarSucursalBody, usuario_id: str = Depends(get_current_user)):
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
