import sqlite3
from datetime import datetime
from pathlib import Path

DB_PATH = Path(__file__).parent / "bot.db"

_SEED_CLIENTES = [
    # email, nombre, plan, precio_bs, ciclo_dias, fecha_renovacion, saldo_favor_bs, numero_cliente
    (
        "test1@gmail.com",
        "Luis Enrique",
        "200 mbps",
        24702.46,
        30,
        "14/09/2026",
        25216.11,
        "428032736",
    ),
    (
        "test2@gmail.com",
        "María Pérez",
        "400 mbps",
        31890.00,
        30,
        "20/09/2026",
        0.00,
        "428019284",
    ),
    (
        "test3@gmail.com",
        "Carlos Rodríguez",
        "1 Gbps",
        58340.75,
        30,
        "05/09/2026",
        12000.50,
        "428057612",
    ),
]


def init_db():
    conn = sqlite3.connect(DB_PATH)
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS clientes (
            email TEXT PRIMARY KEY,
            nombre TEXT NOT NULL,
            plan TEXT NOT NULL,
            precio_bs REAL NOT NULL,
            ciclo_dias INTEGER NOT NULL,
            fecha_renovacion TEXT NOT NULL,
            saldo_favor_bs REAL NOT NULL,
            numero_cliente TEXT NOT NULL
        )
        """
    )
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS escalamientos_soporte (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            consulta TEXT NOT NULL,
            motivo TEXT NOT NULL,
            creado_en TEXT NOT NULL
        )
        """
    )
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS pagos_reportados (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            email TEXT NOT NULL,
            numero_cliente TEXT NOT NULL,
            canal TEXT NOT NULL,
            dato_identificador TEXT NOT NULL,
            fecha_pago TEXT NOT NULL,
            monto_bs TEXT NOT NULL,
            reportado_en TEXT NOT NULL,
            FOREIGN KEY (email) REFERENCES clientes (email)
        )
        """
    )
    conn.executemany(
        """
        INSERT OR IGNORE INTO clientes
            (email, nombre, plan, precio_bs, ciclo_dias, fecha_renovacion, saldo_favor_bs, numero_cliente)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """,
        _SEED_CLIENTES,
    )
    conn.commit()
    conn.close()


def get_cliente_by_email(email: str) -> dict | None:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    row = conn.execute(
        "SELECT * FROM clientes WHERE email = ?", (email.strip().lower(),)
    ).fetchone()
    conn.close()
    return dict(row) if row else None


def insert_escalamiento(consulta: str, motivo: str) -> None:
    conn = sqlite3.connect(DB_PATH)
    conn.execute(
        """
        INSERT INTO escalamientos_soporte (consulta, motivo, creado_en)
        VALUES (?, ?, ?)
        """,
        (consulta, motivo, datetime.now().isoformat(timespec="seconds")),
    )
    conn.commit()
    conn.close()


def insert_pago_reportado(
    email: str,
    numero_cliente: str,
    canal: str,
    dato_identificador: str,
    fecha_pago: str,
    monto_bs: str,
) -> None:
    conn = sqlite3.connect(DB_PATH)
    conn.execute(
        """
        INSERT INTO pagos_reportados
            (email, numero_cliente, canal, dato_identificador, fecha_pago, monto_bs, reportado_en)
        VALUES (?, ?, ?, ?, ?, ?, ?)
        """,
        (
            email,
            numero_cliente,
            canal,
            dato_identificador,
            fecha_pago,
            monto_bs,
            datetime.now().isoformat(timespec="seconds"),
        ),
    )
    conn.commit()
    conn.close()