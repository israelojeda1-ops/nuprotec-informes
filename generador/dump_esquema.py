#!/usr/bin/env python3
"""
Vuelca el esquema de la base Softland (NUPROTEC1) a archivos en el repo,
para usarlo como "base de conocimiento" del proyecto.

Genera en docs/esquema/:
  - tablas.csv           : todas las tablas/vistas (sysobjects) con conteo de filas
  - columnas.csv         : todas las columnas de cada tabla (INFORMATION_SCHEMA)
  - iw_gsaen.md          : detalle de columnas de iw_gsaen (encabezado de ventas)
  - iw_gsaen_muestra.csv : muestra de filas de iw_gsaen (para ver datos reales)

Solo SELECT. No modifica la base.
"""
import os
import pyodbc
import pandas as pd

DB_CONFIG = {
    'server':   'SQLREPLICA01.SOFTLANDCLOUD.CL,1433',
    'database': 'NUPROTEC1',
    'user':     'NUPROTEC',
    'password': os.environ['DB_PASSWORD'],
}


def get_connection():
    cs = (
        f"DRIVER={{ODBC Driver 17 for SQL Server}};"
        f"SERVER={DB_CONFIG['server']};"
        f"DATABASE={DB_CONFIG['database']};"
        f"UID={DB_CONFIG['user']};"
        f"PWD={DB_CONFIG['password']};"
        "Encrypt=no;"
    )
    return pyodbc.connect(cs, timeout=60)


def qdf(sql):
    with get_connection() as conn:
        return pd.read_sql(sql, conn)


OUT = 'docs/esquema'
os.makedirs(OUT, exist_ok=True)

# ── 1. Tablas y vistas ────────────────────────────────────────────────────────
print('Volcando tablas...')
tablas = qdf("""
    SELECT s.name AS Esquema, t.name AS Tabla, t.type_desc AS Tipo,
           ISNULL(p.rows, 0) AS Filas
    FROM sys.objects t
    JOIN sys.schemas s ON s.schema_id = t.schema_id
    LEFT JOIN sys.partitions p ON p.object_id = t.object_id AND p.index_id IN (0,1)
    WHERE t.type IN ('U','V')
    ORDER BY s.name, t.name
""")
tablas.to_csv(f'{OUT}/tablas.csv', index=False, encoding='utf-8-sig')
print(f'  {len(tablas)} tablas/vistas')

# ── 2. Todas las columnas ─────────────────────────────────────────────────────
print('Volcando columnas...')
columnas = qdf("""
    SELECT TABLE_SCHEMA AS Esquema, TABLE_NAME AS Tabla, COLUMN_NAME AS Columna,
           DATA_TYPE AS Tipo, CHARACTER_MAXIMUM_LENGTH AS Largo,
           IS_NULLABLE AS Nulable, ORDINAL_POSITION AS Pos
    FROM INFORMATION_SCHEMA.COLUMNS
    ORDER BY TABLE_SCHEMA, TABLE_NAME, ORDINAL_POSITION
""")
columnas.to_csv(f'{OUT}/columnas.csv', index=False, encoding='utf-8-sig')
print(f'  {len(columnas)} columnas')

# ── 3. Detalle de iw_gsaen ────────────────────────────────────────────────────
print('Detalle iw_gsaen...')
cols_gsaen = columnas[columnas['Tabla'].str.lower() == 'iw_gsaen']
with open(f'{OUT}/iw_gsaen.md', 'w', encoding='utf-8') as f:
    f.write('# Columnas de iw_gsaen (encabezado de ventas / facturas)\n\n')
    f.write('| # | Columna | Tipo | Largo | Nulable |\n')
    f.write('|---|---------|------|-------|--------|\n')
    for _, r in cols_gsaen.iterrows():
        f.write(f"| {r['Pos']} | {r['Columna']} | {r['Tipo']} | "
                f"{r['Largo'] if pd.notna(r['Largo']) else ''} | {r['Nulable']} |\n")

# ── 4. Muestra de iw_gsaen (para ver referencia/forma de pago) ────────────────
print('Muestra iw_gsaen...')
try:
    muestra = qdf("""
        SELECT TOP 200 *
        FROM NUPROTEC1.softland.iw_gsaen
        WHERE Estado='V' AND EnMantencion<>-1
        ORDER BY Fecha DESC
    """)
    muestra.to_csv(f'{OUT}/iw_gsaen_muestra.csv', index=False, encoding='utf-8-sig')
    print(f'  {len(muestra)} filas de muestra, {len(muestra.columns)} columnas')
except Exception as e:
    print(f'  No se pudo obtener muestra: {e}')

print('Esquema volcado en', OUT)
