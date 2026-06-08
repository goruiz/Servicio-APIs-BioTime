"""
Repositorio de huellas dactilares.
Ejecuta queries SQL directamente sobre la tabla iclock_biodata de BioTime.
La tabla se configura con DB_TABLA_HUELLAS en .env (default: iclock_biodata).
"""
import base64
import asyncpg

from app.core.config import settings


class RepositorioHuellas:

    def __init__(self, pool: asyncpg.Pool) -> None:
        self._pool = pool
        self._tabla = settings.DB_TABLA_HUELLAS

    async def obtener_huellas(
        self, page: int = 1, page_size: int = 10
    ) -> tuple[int, list[dict]]:
        """Devuelve (total, registros) de todas las huellas paginadas."""
        offset = (page - 1) * page_size
        async with self._pool.acquire() as conn:
            total: int = await conn.fetchval(f"SELECT COUNT(*) FROM {self._tabla}")
            filas = await conn.fetch(
                f"SELECT * FROM {self._tabla} ORDER BY id LIMIT $1 OFFSET $2",
                page_size,
                offset,
            )
        return total, [dict(fila) for fila in filas]

    async def obtener_huellas_por_empleado(
        self, empleado_id: int, page: int = 1, page_size: int = 10
    ) -> tuple[int, list[dict]]:
        """Devuelve (total, registros) de las huellas de un empleado paginadas."""
        offset = (page - 1) * page_size
        async with self._pool.acquire() as conn:
            total: int = await conn.fetchval(
                f"SELECT COUNT(*) FROM {self._tabla} WHERE employee_id = $1",
                empleado_id,
            )
            filas = await conn.fetch(
                f"SELECT * FROM {self._tabla} WHERE employee_id = $1 ORDER BY id LIMIT $2 OFFSET $3",
                empleado_id,
                page_size,
                offset,
            )
        return total, [dict(fila) for fila in filas]

    async def obtener_templates_por_empleado(self, employee_id: int) -> list[dict]:
        """Devuelve los campos necesarios de templates no nulos de un empleado (sin paginación)."""
        async with self._pool.acquire() as conn:
            filas = await conn.fetch(
                f"SELECT bio_tmp, bio_index, valid FROM {self._tabla} WHERE employee_id = $1 AND bio_tmp IS NOT NULL ORDER BY id",
                employee_id,
            )
        return [dict(fila) for fila in filas]

    async def obtener_templates_completos_por_empleado(self, employee_id: int) -> list[dict]:
        """Devuelve todos los campos necesarios para copiar templates de un empleado."""
        async with self._pool.acquire() as conn:
            filas = await conn.fetch(
                f"""SELECT employee_id, bio_index, bio_type, bio_no, bio_format,
                           major_ver, minor_ver, valid, duress, bio_tmp
                    FROM {self._tabla}
                    WHERE employee_id = $1 AND bio_tmp IS NOT NULL
                    ORDER BY bio_index, bio_no""",
                employee_id,
            )
        return [dict(fila) for fila in filas]

    async def obtener_sns_por_empleado(self, employee_id: int) -> list[str]:
        """Devuelve los SNs de los terminales donde el empleado tiene huellas registradas."""
        async with self._pool.acquire() as conn:
            filas = await conn.fetch(
                f"""SELECT DISTINCT sn FROM {self._tabla}
                    WHERE employee_id = $1 AND bio_tmp IS NOT NULL AND sn IS NOT NULL
                    ORDER BY sn""",
                employee_id,
            )
        return [fila["sn"] for fila in filas]

    async def contar_huellas_por_terminal(self, sn: str) -> int:
        """Devuelve la cantidad de huellas con template no nulo en un terminal."""
        async with self._pool.acquire() as conn:
            return await conn.fetchval(
                f"SELECT COUNT(*) FROM {self._tabla} WHERE sn = $1 AND bio_tmp IS NOT NULL",
                sn,
            )

    async def copiar_huellas_entre_terminales(self, sn_origen: str, sn_destino: str) -> int:
        """Copia todas las huellas de sn_origen a sn_destino en una sola operación SQL.
        Omite registros que ya existan en destino (ON CONFLICT DO NOTHING).
        Devuelve la cantidad de filas efectivamente insertadas."""
        async with self._pool.acquire() as conn:
            resultado = await conn.execute(
                f"""INSERT INTO {self._tabla}
                        (employee_id, bio_index, bio_type, bio_no, bio_format,
                         major_ver, minor_ver, valid, duress, bio_tmp, sn, update_time, status)
                    SELECT employee_id, bio_index, bio_type, bio_no, bio_format,
                           major_ver, minor_ver, valid, duress, bio_tmp, $2, NOW(), 0
                    FROM {self._tabla}
                    WHERE sn = $1 AND bio_tmp IS NOT NULL
                    ON CONFLICT (employee_id, bio_no, bio_index, bio_type, bio_format, major_ver, minor_ver, sn)
                    DO NOTHING""",
                sn_origen,
                sn_destino,
            )
        # asyncpg devuelve "INSERT 0 N" donde N = filas insertadas
        return int(resultado.split()[-1])

    async def obtener_huellas_por_terminal(
        self, sn: str, page: int = 1, page_size: int = 10
    ) -> tuple[int, list[dict]]:
        """Devuelve (total, registros) de las huellas de un terminal paginadas."""
        offset = (page - 1) * page_size
        async with self._pool.acquire() as conn:
            total: int = await conn.fetchval(
                f"SELECT COUNT(*) FROM {self._tabla} WHERE sn = $1",
                sn,
            )
            filas = await conn.fetch(
                f"SELECT * FROM {self._tabla} WHERE sn = $1 ORDER BY employee_id, bio_index LIMIT $2 OFFSET $3",
                sn,
                page_size,
                offset,
            )
        return total, [dict(fila) for fila in filas]

    async def insertar_o_actualizar_template(
        self,
        employee_id: int,
        bio_index: int,
        bio_type: int,
        bio_no: int,
        bio_format: int,
        major_ver: str,
        minor_ver: str,
        valid: int,
        duress: int,
        bio_tmp: str,
        sn: str,
    ) -> None:
        """Inserta un template en iclock_biodata con el sn del terminal destino.
        Si ya existe un registro para ese empleado+dedo, actualiza bio_tmp, valid y sn
        (el sn pasa a ser el del terminal destino, indicando a BioTime que lo sincronice ahí)."""
        async with self._pool.acquire() as conn:
            await conn.execute(
                f"""INSERT INTO {self._tabla}
                        (employee_id, bio_index, bio_type, bio_no, bio_format,
                         major_ver, minor_ver, valid, duress, bio_tmp, sn,
                         update_time, status)
                    VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, NOW(), 0)
                    ON CONFLICT (employee_id, bio_no, bio_index, bio_type, bio_format, major_ver, minor_ver, sn)
                    DO UPDATE SET bio_tmp = EXCLUDED.bio_tmp, valid = EXCLUDED.valid, update_time = NOW()""",
                employee_id, bio_index, bio_type, bio_no, bio_format,
                major_ver, minor_ver, valid, duress, bio_tmp, sn,
            )

    async def obtener_terminal_por_sn(self, sn: str) -> dict | None:
        """Devuelve id, fp_count y finger_fun_on de un terminal.
        finger_fun_on=True si el terminal tiene sensor de huella habilitado (FingerFunOn=1)."""
        async with self._pool.acquire() as conn:
            fila = await conn.fetchrow(
                """SELECT t.id, t.fp_count,
                          COALESCE(tp.param_value = '1', FALSE) AS finger_fun_on
                   FROM iclock_terminal t
                   LEFT JOIN iclock_terminalparameter tp
                          ON tp.terminal_id = t.id AND tp.param_name = 'FingerFunOn'
                   WHERE t.sn = $1""",
                sn,
            )
        return dict(fila) if fila else None

    async def encolar_fingertmp(
        self, terminal_id: int, emp_code: str, bio_index: int, valid: int, bio_tmp: str
    ) -> None:
        """Inserta un comando DATA UPDATE FINGERTMP en iclock_terminalcommand.
        BioTime lo entrega al terminal en el próximo poll ADMS (~10 segundos)."""
        size = len(base64.b64decode(bio_tmp))
        content = f"DATA UPDATE FINGERTMP PIN={emp_code}\tFID={bio_index}\tSize={size}\tValid={valid}\tTMP={bio_tmp}"
        async with self._pool.acquire() as conn:
            await conn.execute(
                "INSERT INTO iclock_terminalcommand (terminal_id, content, commit_time, package) VALUES ($1, $2, NOW(), NULL)",
                terminal_id,
                content,
            )

    async def encolar_fingertmp_masivo(self, sns: list[str] | None = None) -> list[dict]:
        """Encola comandos DATA UPDATE FINGERTMP para todos los templates en iclock_biodata
        de terminales con sensor de huella (fp_count > 0).
        Si sns es None, procesa todos los terminales válidos.
        Devuelve lista de {sn, alias, comandos_encolados}."""
        async with self._pool.acquire() as conn:
            filtro_sn = "AND t.sn = ANY($1::text[])" if sns else ""
            params = [sns] if sns else []
            filas = await conn.fetch(
                f"""SELECT t.id AS terminal_id, t.sn, t.alias, e.emp_code,
                           b.bio_index, b.valid, b.bio_tmp
                    FROM {self._tabla} b
                    JOIN iclock_terminal t ON t.sn = b.sn
                    JOIN iclock_terminalparameter tp
                         ON tp.terminal_id = t.id AND tp.param_name = 'FingerFunOn' AND tp.param_value = '1'
                    JOIN personnel_employee e ON e.id = b.employee_id
                    WHERE b.bio_tmp IS NOT NULL
                    {filtro_sn}
                    ORDER BY t.sn, e.emp_code, b.bio_index""",
                *params,
            )
            if not filas:
                return []
            await conn.executemany(
                "INSERT INTO iclock_terminalcommand (terminal_id, content, commit_time, package) VALUES ($1, $2, NOW(), NULL)",
                [
                    (
                        fila["terminal_id"],
                        f"DATA UPDATE FINGERTMP PIN={fila['emp_code']}\tFID={fila['bio_index']}\tSize={len(base64.b64decode(fila['bio_tmp']))}\tValid={fila['valid']}\tTMP={fila['bio_tmp']}",
                    )
                    for fila in filas
                ],
            )

        conteo: dict[str, dict] = {}
        for fila in filas:
            sn = fila["sn"]
            if sn not in conteo:
                conteo[sn] = {"sn": sn, "alias": fila["alias"], "comandos_encolados": 0}
            conteo[sn]["comandos_encolados"] += 1
        return list(conteo.values())
