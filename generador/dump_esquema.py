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

# ── 5. Muestras de tablas de caja / forma de pago (para Arqueo) ───────────────
print('Muestras de tablas de pago/caja...')
PAGO_TABLES = [
    'vw_movcaja', 'vw_tcaja', 'vw_apecaja', 'vw_ttarje',
    'xwtfpago', 'pwformaspago', 'cwtauxpagos',
]
for tbl in PAGO_TABLES:
    try:
        m = qdf(f"SELECT TOP 80 * FROM NUPROTEC1.softland.{tbl}")
        m.to_csv(f'{OUT}/muestra_{tbl}.csv', index=False, encoding='utf-8-sig')
        print(f'  {tbl}: {len(m)} filas, {len(m.columns)} cols')
    except Exception as e:
        print(f'  {tbl}: no disponible ({str(e)[:80]})')

# Mapeo de FmaPago en iw_gsaen: valores distintos y su relación con caja
try:
    fp = qdf("""
        SELECT FmaPago, COUNT(*) AS N
        FROM NUPROTEC1.softland.iw_gsaen
        WHERE YEAR(Fecha) >= 2025
        GROUP BY FmaPago ORDER BY N DESC
    """)
    fp.to_csv(f'{OUT}/iw_gsaen_fmapago.csv', index=False, encoding='utf-8-sig')
    print(f'  FmaPago distintos: {len(fp)}')
except Exception as e:
    print(f'  FmaPago: {str(e)[:80]}')

# ── 6. Referencias DTE (forma de pago en RazonRef) ────────────────────────────
print('Muestra referencias DTE (forma de pago)...')
try:
    ref = qdf("""
        SELECT TOP 400
            r.Tipo, r.NroInt, r.CodRefSII, r.CodRef, r.FolioRef, r.RazonRef, r.Glosa,
            cab.Fecha, cab.Folio, cab.Total, cab.NomAux
        FROM NUPROTEC1.softland.IW_GSaEn_RefDTE AS r
        JOIN NUPROTEC1.softland.iw_gsaen AS cab
            ON cab.Tipo = r.Tipo AND cab.NroInt = r.NroInt
        WHERE YEAR(cab.Fecha) >= 2025
        ORDER BY cab.Fecha DESC
    """)
    ref.to_csv(f'{OUT}/muestra_refdte.csv', index=False, encoding='utf-8-sig')
    print(f'  refdte: {len(ref)} filas')
    # distintos CodRefSII / CodRef
    d1 = qdf("""
        SELECT r.CodRefSII, r.CodRef, COUNT(*) AS N
        FROM NUPROTEC1.softland.IW_GSaEn_RefDTE r
        JOIN NUPROTEC1.softland.iw_gsaen cab ON cab.Tipo=r.Tipo AND cab.NroInt=r.NroInt
        WHERE YEAR(cab.Fecha) >= 2025
        GROUP BY r.CodRefSII, r.CodRef ORDER BY N DESC
    """)
    d1.to_csv(f'{OUT}/refdte_codigos.csv', index=False, encoding='utf-8-sig')
    print(f'  codigos ref: {len(d1)}')
except Exception as e:
    print(f'  refdte: {str(e)[:120]}')

# ── 7. Documentos recientes (julio) con su forma de pago (referencia) ─────────
print('Documentos recientes con forma de pago...')
try:
    hoy = qdf("""
        SELECT
            cab.Fecha, cab.Tipo AS TipoDoc, cab.Folio, cab.NomAux AS Cliente,
            cab.RutAux, cab.Total,
            r.CodRefSII, r.CodRef, r.FolioRef AS NumOperacion, r.RazonRef AS FormaPago
        FROM NUPROTEC1.softland.iw_gsaen AS cab
        LEFT JOIN NUPROTEC1.softland.IW_GSaEn_RefDTE AS r
            ON cab.Tipo = r.Tipo AND cab.NroInt = r.NroInt
        WHERE cab.Fecha >= '2026-07-01'
          AND cab.Estado='V' AND cab.EnMantencion<>-1
        ORDER BY cab.Fecha DESC, cab.Folio
    """)
    hoy.to_csv(f'{OUT}/muestra_docs_julio.csv', index=False, encoding='utf-8-sig')
    print(f'  docs julio: {len(hoy)} filas')
except Exception as e:
    print(f'  docs julio: {str(e)[:120]}')

print('Esquema volcado en', OUT)
