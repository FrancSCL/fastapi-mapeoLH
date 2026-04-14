import logging
from contextlib import contextmanager

import pymysql
import pymysql.cursors
from dbutils.pooled_db import PooledDB

from config import Config

logger = logging.getLogger(__name__)

_pool: PooledDB | None = None


def _build_pool() -> PooledDB:
    base = dict(
        creator=pymysql,
        maxconnections=10,  # máximo conexiones simultáneas
        mincached=2,        # conexiones pre-abiertas al iniciar
        maxcached=5,        # máximo conexiones inactivas en pool
        blocking=True,      # esperar si pool lleno (no lanzar error)
        charset="utf8mb4",
        cursorclass=pymysql.cursors.DictCursor,
        autocommit=True,
        user=Config.CLOUD_SQL_USER,
        password=Config.CLOUD_SQL_PASSWORD,
        database=Config.CLOUD_SQL_DB,
    )
    if Config.is_cloud_run():
        try:
            pool = PooledDB(
                unix_socket=f"/cloudsql/{Config.CLOUD_SQL_CONNECTION_NAME}",
                **base,
            )
            logger.info("Pool creado via Unix socket")
            return pool
        except Exception as e:
            logger.warning(f"Unix socket falló, usando IP pública: {e}")
            return PooledDB(host=Config.CLOUD_SQL_HOST, port=Config.CLOUD_SQL_PORT, **base)
    else:
        return PooledDB(host=Config.DB_HOST, port=Config.DB_PORT, **base)


def get_db_connection():
    """Retorna una conexión del pool. Llamar .close() devuelve al pool."""
    global _pool
    if _pool is None:
        _pool = _build_pool()
    return _pool.connection()


@contextmanager
def get_db():
    """Context manager que garantiza devolver la conexión al pool."""
    conn = get_db_connection()
    try:
        yield conn
    finally:
        conn.close()
