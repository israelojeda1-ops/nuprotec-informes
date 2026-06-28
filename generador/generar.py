
"""
Generador de Dashboard Comercial NUPROTEC
Uso local : DB_PASSWORD=xxx GMAIL_PASS=xxx python generador/generar.py
GitHub    : configurar Secrets DB_PASSWORD y GMAIL_PASS en el repositorio
"""

import os, json, base64, smtplib, urllib.request
import pyodbc, pandas as pd
from datetime import datetime
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

# ══════════════════════════════════════════════════════════════════════════════
# CONFIGURACIÓN
# ══════════════════════════════════════════════════════════════════════════════
DB_CONFIG = {
    'server':   'SQLREPLICA01.SOFTLANDCLOUD.CL,1433',
    'database': 'NUPROTEC1',
    'user':     'NUPROTEC',
    'password': os.environ['DB_PASSWORD'],
}
GMAIL_USER   = 'israelojeda1@gmail.com'
GMAIL_PASS   = os.environ.get('GMAIL_PASS', '')
MAIL_DESTINO = os.environ.get('MAIL_DESTINO', 'israelojeda1@gmail.com')
GITHUB_USER  = 'israelojeda1-ops'
GITHUB_REPO  = 'nuprotec-informes'
GITHUB_TOKEN = os.environ.get('GITHUB_TOKEN', '')   # provisto automáticamente por Actions

# ══════════════════════════════════════════════════════════════════════════════
# CONEXIÓN
# ══════════════════════════════════════════════════════════════════════════════
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

# ══════════════════════════════════════════════════════════════════════════════
# FECHAS
# ══════════════════════════════════════════════════════════════════════════════
now        = datetime.now()
anio       = now.year
mes_act    = now.month
gen_str    = now.strftime('%d/%m/%Y %H:%M')
MESES      = ['','Enero','Febrero','Marzo','Abril','Mayo','Junio',
              'Julio','Agosto','Septiembre','Octubre','Noviembre','Diciembre']
nombre_mes = f'{MESES[mes_act]} {anio}'

# ══════════════════════════════════════════════════════════════════════════════
# QUERIES
# ══════════════════════════════════════════════════════════════════════════════
SQL_RESUMEN = f"""
SELECT
    MONTH(coti.CtFem) AS Mes, vend.VenDes AS Vendedor,
    SUM(CASE WHEN coti.CtEstado='P' THEN 1 ELSE 0 END) AS Pendiente_N,
    SUM(CASE WHEN coti.CtEstado='P' THEN coti.CtSubTotal+coti.CtValflete ELSE 0 END) AS Pendiente_Monto,
    SUM(CASE WHEN coti.CtEstado='V' THEN 1 ELSE 0 END) AS EnNV_N,
    SUM(CASE WHEN coti.CtEstado='V' THEN coti.CtSubTotal+coti.CtValflete ELSE 0 END) AS EnNV_Monto,
    SUM(CASE WHEN coti.CtEstado='R' THEN 1 ELSE 0 END) AS Perdida_N,
    SUM(CASE WHEN coti.CtEstado='R' THEN coti.CtSubTotal+coti.CtValflete ELSE 0 END) AS Perdida_Monto,
    SUM(CASE WHEN coti.CtEstado='N' THEN 1 ELSE 0 END) AS Nula_N,
    SUM(CASE WHEN coti.CtEstado='N' THEN coti.CtSubTotal+coti.CtValflete ELSE 0 END) AS Nula_Monto,
    COUNT(DISTINCT coti.CotNum) AS Total_N,
    SUM(coti.CtSubTotal+coti.CtValflete) AS Total_Monto,
    ROUND(100.0*SUM(CASE WHEN coti.CtEstado='V' THEN 1 ELSE 0 END)
               /NULLIF(COUNT(DISTINCT coti.CotNum),0),1) AS Pct_Conv
FROM NUPROTEC1.softland.nwcotiza AS coti
INNER JOIN NUPROTEC1.softland.cwtvend AS vend ON coti.VenCod=vend.VenCod
WHERE YEAR(coti.CtFem)={anio} AND coti.EnMantencion=0
GROUP BY MONTH(coti.CtFem), vend.VenDes
ORDER BY Mes, Total_Monto DESC
"""

SQL_COTIZACIONES = f"""
SELECT
    MONTH(coti.CtFem) AS Mes,
    coti.CotNum AS NroCotizacion,
    CAST(coti.CtFem AS date) AS Fecha,
    auxi.NomAux AS Cliente,
    vend.VenDes AS Vendedor,
    CASE coti.CtEstado
        WHEN 'P' THEN 'Pendiente' WHEN 'V' THEN 'En NV'
        WHEN 'N' THEN 'Nula'      WHEN 'R' THEN 'Perdida'
        ELSE coti.CtEstado END AS Estado,
    CAST(det.FechaVencto AS date) AS FechaVencimiento,
    CASE
        WHEN coti.CtEstado IN ('N','R') THEN 'Cerrada'
        WHEN coti.CtEstado = 'V'        THEN 'Convertida'
        WHEN det.FechaVencto < GETDATE() THEN 'Vencida'
        WHEN DATEDIFF(DAY,GETDATE(),det.FechaVencto) <= 7  THEN 'Vence <=7d'
        WHEN DATEDIFF(DAY,GETDATE(),det.FechaVencto) <= 15 THEN 'Vence <=15d'
        ELSE 'Vigente'
    END AS Alerta,
    prod.CodGrupo AS Grupo,
    ROUND(SUM(det.CtTotLinea),0) AS MontoLinea,
    coti.CtSubTotal + coti.CtValflete AS NetoCotizacion,
    nv.NVNumero AS NroNV
FROM NUPROTEC1.softland.nwcotiza AS coti
INNER JOIN NUPROTEC1.softland.nwdetcot AS det  ON coti.CotNum=det.CotNum
INNER JOIN NUPROTEC1.softland.cwtauxi  AS auxi ON coti.CodAux=auxi.CodAux
INNER JOIN NUPROTEC1.softland.cwtvend  AS vend ON coti.VenCod=vend.VenCod
INNER JOIN NUPROTEC1.softland.iw_tprod AS prod ON det.CodProd=prod.CodProd
LEFT  JOIN NUPROTEC1.softland.nw_nventa AS nv  ON coti.CotNum=nv.CotNum
LEFT  JOIN NUPROTEC1.softland.iw_gsaen  AS fac
    ON fac.nvnumero=nv.NVNumero AND fac.Tipo IN ('F','B')
    AND fac.Estado='V' AND fac.EnMantencion<>-1
WHERE YEAR(coti.CtFem)={anio} AND coti.EnMantencion=0
GROUP BY MONTH(coti.CtFem),coti.CotNum,coti.CtFem,auxi.NomAux,vend.VenDes,
         coti.CtEstado,det.FechaVencto,prod.CodGrupo,
         coti.CtSubTotal,coti.CtValflete,nv.NVNumero,fac.NroInt
ORDER BY coti.CtFem DESC, coti.CotNum
"""

SQL_NV = f"""
SELECT
    MONTH(nv.nvFem) AS Mes,
    nv.NVNumero AS NroNV,
    auxi.NomAux AS Cliente,
    vend.VenDes AS Vendedor,
    nv.NumOC AS OrdenCompra,
    nv.CotNum AS NroCotizacion,
    CASE est.NVEstado WHEN 'A' THEN 'Activa' WHEN 'C' THEN 'Concluida' ELSE est.NVEstado END AS EstadoNV,
    CASE est.NVEstFact WHEN -1 THEN 'Facturada' WHEN 0 THEN 'Sin facturar'
        ELSE CAST(est.NVEstFact AS varchar(5)) END AS EstadoFacturacion,
    CASE est.NVEstDesp WHEN -1 THEN 'Despachada' WHEN 0 THEN 'Sin despachar'
        ELSE CAST(est.NVEstDesp AS varchar(5)) END AS EstadoDespacho,
    prod.CodGrupo AS Grupo,
    det.nvTotLinea AS ValorLinea,
    nv.nvMonto AS MontoNV,
    COALESCE(CAST(fac.Folio AS varchar(20)),CAST(fac.Factura AS varchar(20)),
             CAST(fac.NroInt AS varchar(20))) AS NroFactura,
    fac.NetoAfecto + fac.NetoExento AS MontoFactura
FROM NUPROTEC1.softland.nw_nventa AS nv
INNER JOIN NUPROTEC1.softland.NW_vsnpEstadoNW AS est ON nv.NVNumero=est.NVNumero
INNER JOIN NUPROTEC1.softland.nw_detnv  AS det  ON nv.NVNumero=det.NVNumero
INNER JOIN NUPROTEC1.softland.cwtauxi   AS auxi ON nv.CodAux=auxi.CodAux
INNER JOIN NUPROTEC1.softland.cwtvend   AS vend ON nv.VenCod=vend.VenCod
INNER JOIN NUPROTEC1.softland.iw_tprod  AS prod ON det.CodProd=prod.CodProd
LEFT  JOIN NUPROTEC1.softland.iw_gsaen  AS fac
    ON fac.nvnumero=nv.NVNumero AND fac.Tipo IN ('F','B')
    AND fac.Estado='V' AND fac.EnMantencion<>-1
WHERE YEAR(nv.nvFem)={anio} AND nv.EnMantencion=0
ORDER BY nv.nvFem DESC, nv.NVNumero, det.nvLinea
"""

SQL_STOCK = """
SELECT
    P.CodProd AS Codigo, P.DesProd AS Producto,
    ISNULL(G.DesGrupo,'—') AS Grupo, ISNULL(S.DesSubGr,'—') AS SubGrupo,
    ISNULL(C.CostoUnitario,0) AS Costo,
    ISNULL(P.PrecioVta,0) AS PrecioNeto,
    SUM(CASE WHEN M.CodBode='08' THEN (M.Ingresos-M.Egresos) ELSE 0 END) AS Stock08,
    SUM(CASE WHEN M.CodBode='20' THEN (M.Ingresos-M.Egresos) ELSE 0 END) AS Stock20,
    SUM(CASE WHEN M.CodBode IN ('08','20') THEN (M.Ingresos-M.Egresos) ELSE 0 END) AS StockTotal
FROM NUPROTEC1.softland.iw_tprod P
INNER JOIN NUPROTEC1.softland.IW_vsnpMovimStockTipoBod M ON P.CodProd=M.CodProd
LEFT  JOIN NUPROTEC1.softland.iw_tgrupo G ON P.CodGrupo=G.CodGrupo
LEFT  JOIN NUPROTEC1.softland.iw_tsubgr S ON P.CodSubGr=S.CodSubGr
LEFT  JOIN (
    SELECT CodProd, CostoUnitario FROM (
        SELECT CodProd, CostoUnitario,
               ROW_NUMBER() OVER (PARTITION BY CodProd ORDER BY Fecha DESC) AS rn
        FROM NUPROTEC1.softland.iw_costop WHERE Fecha <= GETDATE()
    ) X WHERE rn=1
) C ON P.CodProd=C.CodProd
WHERE M.TipoBod='D' AND M.CodBode IN ('08','20')
GROUP BY P.CodProd,P.DesProd,ISNULL(G.DesGrupo,'—'),ISNULL(S.DesSubGr,'—'),
         ISNULL(C.CostoUnitario,0),P.PrecioVta
HAVING SUM(CASE WHEN M.CodBode IN ('08','20') THEN (M.Ingresos-M.Egresos) ELSE 0 END) > 0
ORDER BY ISNULL(G.DesGrupo,'—'), P.DesProd
"""

SQL_FACT = f"""
SELECT
    MONTH(CAB.Fecha) AS Mes,
    CASE CAB.Tipo WHEN 'F' THEN 'Factura' WHEN 'N' THEN 'Nota de Credito'
                  WHEN 'D' THEN 'Nota de Debito' WHEN 'B' THEN 'Boleta'
                  ELSE CAB.Tipo END AS Tipo,
    ISNULL(VEN.VenDes,'Sin vendedor') AS Vendedor,
    CAB.NetoAfecto + CAB.NetoExento AS MontoNeto
FROM NUPROTEC1.softland.iw_gsaen AS CAB
LEFT JOIN NUPROTEC1.softland.cwtvend AS VEN ON CAB.CodVendedor=VEN.VenCod
WHERE YEAR(CAB.Fecha)={anio}
  AND CAB.Tipo IN ('F','N','D','B')
  AND CAB.Estado='V' AND CAB.EnMantencion<>-1
"""

# ══════════════════════════════════════════════════════════════════════════════
# EJECUTAR QUERIES
# ══════════════════════════════════════════════════════════════════════════════
print('Consultando base de datos...')
df_resumen      = qdf(SQL_RESUMEN)
df_cotizaciones = qdf(SQL_COTIZACIONES)
df_nv           = qdf(SQL_NV)
df_stock        = qdf(SQL_STOCK)
df_fact         = qdf(SQL_FACT)
print(f'  Resumen cotizaciones : {len(df_resumen)} filas')
print(f'  Detalle cotizaciones : {len(df_cotizaciones)} filas')
print(f'  Notas de Venta       : {len(df_nv)} filas')
print(f'  Stock                : {len(df_stock)} productos')
print(f'  Facturacion          : {len(df_fact)} documentos')

# ══════════════════════════════════════════════════════════════════════════════
# PROCESAR DATOS → ESTRUCTURAS JS
# ══════════════════════════════════════════════════════════════════════════════
def js_safe(obj):
    s = json.dumps(obj, ensure_ascii=False)
    return s.replace(' ',' ').replace(' ',' ').replace('</', '<\\/')

# ── Tab Cotizaciones: RESUMEN ─────────────────────────────────────────────────
RESUMEN = {}
for m in range(1, 13):
    dfm = df_resumen[df_resumen['Mes'] == m]
    RESUMEN[str(m)] = [
        {
            'Vendedor':        str(r.Vendedor).strip(),
            'EnNV_N':          int(r.EnNV_N),
            'EnNV_Monto':      float(r.EnNV_Monto),
            'Pendiente_N':     int(r.Pendiente_N),
            'Pendiente_Monto': float(r.Pendiente_Monto),
            'Perdida_N':       int(r.Perdida_N),
            'Perdida_Monto':   float(r.Perdida_Monto),
            'Nula_N':          int(r.Nula_N),
            'Nula_Monto':      float(r.Nula_Monto),
            'Total_N':         int(r.Total_N),
            'Total_Monto':     float(r.Total_Monto),
            'Pct_Conv':        float(r.Pct_Conv),
        }
        for _, r in dfm.sort_values('Total_Monto', ascending=False).iterrows()
    ]

# ── Tab Cotizaciones: DATA (detalle para panel lateral) ───────────────────────
DATA = {}
for m in range(1, 13):
    DATA[str(m)] = {}
    dmes = df_cotizaciones[df_cotizaciones['Mes'] == m]
    for vend in dmes['Vendedor'].unique():
        dv = dmes[dmes['Vendedor'] == vend]
        DATA[str(m)][vend] = {}
        for est in ['En NV', 'Pendiente', 'Perdida', 'Nula']:
            de = dv[dv['Estado'] == est]
            if de.empty:
                continue
            cotis = {}
            for _, r in de.iterrows():
                cot = int(r['NroCotizacion'])
                if cot not in cotis:
                    cotis[cot] = {
                        'num':    cot,
                        'fecha':  str(r['Fecha'])[:10],
                        'cliente':str(r['Cliente']).strip(),
                        'alerta': str(r['Alerta']),
                        'vence':  str(r['FechaVencimiento'])[:10] if pd.notna(r['FechaVencimiento']) else '',
                        'grupos': [],
                    }
                cotis[cot]['grupos'].append({'g': str(r['Grupo']), 'm': float(r['MontoLinea'])})
            lista = sorted(cotis.values(), key=lambda x: -sum(g['m'] for g in x['grupos']))
            DATA[str(m)][vend][est] = {
                'cotis': lista,
                'n':     len(lista),
                'monto': float(de['NetoCotizacion'].drop_duplicates().sum()),
            }

# ── Tab Notas de Venta: NV_RESUMEN ───────────────────────────────────────────
NV_RESUMEN = {}
for m in range(1, 13):
    dfm = df_nv[df_nv['Mes'] == m]
    NV_RESUMEN[str(m)] = []
    if dfm.empty:
        continue
    for vend, dv in dfm.groupby('Vendedor'):
        nv_u      = dv.groupby('NroNV').first().reset_index()
        total_n   = len(nv_u)
        activas   = int((nv_u['EstadoNV'] == 'Activa').sum())
        facturadas= int((nv_u['EstadoFacturacion'] == 'Facturada').sum())
        monto_tot = float(nv_u['MontoNV'].sum())
        monto_f   = float(dv.dropna(subset=['NroFactura'])
                          .groupby('NroFactura')['MontoFactura'].first().sum()) \
                    if dv['NroFactura'].notna().any() else 0.0
        NV_RESUMEN[str(m)].append({
            'Vendedor':    str(vend).strip(),
            'Total_N':     total_n,
            'Activas':     activas,
            'Facturadas':  facturadas,
            'SinFacturar': total_n - facturadas,
            'MontoTotal':  monto_tot,
            'MontoFact':   monto_f,
            'MontoPend':   monto_tot - monto_f,
        })
    NV_RESUMEN[str(m)].sort(key=lambda x: -x['MontoTotal'])

# ── Tab Facturación: FACT_RESUMEN ─────────────────────────────────────────────
FACT_RESUMEN = {}
for m in range(1, 13):
    dfm = df_fact[df_fact['Mes'] == m]
    FACT_RESUMEN[str(m)] = []
    if dfm.empty:
        continue
    for vend, dv in dfm.groupby('Vendedor'):
        bruto = float(dv[dv['Tipo'].isin(['Factura','Boleta'])]['MontoNeto'].sum())
        nc    = float(dv[dv['Tipo'] == 'Nota de Credito']['MontoNeto'].sum())
        FACT_RESUMEN[str(m)].append({
            'Vendedor':   str(vend).strip(),
            'N_Facturas': int(len(dv[dv['Tipo'].isin(['Factura','Boleta'])])),
            'N_NC':       int(len(dv[dv['Tipo'] == 'Nota de Credito'])),
            'MontoBruto': bruto,
            'MontoNC':    nc,
            'MontoNeto':  bruto - nc,
        })
    FACT_RESUMEN[str(m)].sort(key=lambda x: -x['MontoNeto'])

# ── Tab Pendientes Año: PEND_ANIO ─────────────────────────────────────────────
PEND_ANIO = {}
for m in range(1, 13):
    dfm = df_cotizaciones[
        (df_cotizaciones['Mes'] == m) & (df_cotizaciones['Estado'] == 'Pendiente')
    ]
    PEND_ANIO[str(m)] = []
    if dfm.empty:
        continue
    for vend, dv in dfm.groupby('Vendedor'):
        PEND_ANIO[str(m)].append({
            'Vendedor': str(vend).strip(),
            'Total':    int(len(dv)),
            'Monto':    float(dv['NetoCotizacion'].sum()),
            'Vencidas': int((dv['Alerta'] == 'Vencida').sum()),
            'Prox7':    int((dv['Alerta'] == 'Vence <=7d').sum()),
            'Prox15':   int((dv['Alerta'] == 'Vence <=15d').sum()),
            'Vigentes': int((dv['Alerta'] == 'Vigente').sum()),
        })
    PEND_ANIO[str(m)].sort(key=lambda x: -x['Monto'])

# ── Tab Stock ─────────────────────────────────────────────────────────────────
STOCK_DATA = [
    {
        'cod':   str(r.Codigo).strip(),
        'prod':  str(r.Producto).strip(),
        'grupo': str(r.Grupo).strip(),
        'sub':   str(r.SubGrupo).strip(),
        'costo': float(r.Costo),
        'precio':float(r.PrecioNeto),
        's08':   float(r.Stock08),
        's20':   float(r.Stock20),
        'total': float(r.StockTotal),
        'valor': round(float(r.StockTotal) * float(r.Costo), 0),
    }
    for _, r in df_stock.iterrows()
]

# ══════════════════════════════════════════════════════════════════════════════
# OPCIONES SELECTOR MES
# ══════════════════════════════════════════════════════════════════════════════
opts = ''.join(
    f'<option value="{m}"{" selected" if m==mes_act else ""}>{MESES[m]} {anio}</option>'
    for m in range(1, 13)
)

# ══════════════════════════════════════════════════════════════════════════════
# TEMPLATE HTML
# ══════════════════════════════════════════════════════════════════════════════
HTML_TEMPLATE = '''<!DOCTYPE html>
<html lang="es">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Dashboard Comercial NUPROTEC ANIO_</title>
<style>
:root{--nu-blue:#1B2A4E;--nu-orange:#C44918;--bg-nv:#d1ecf1;--fg-nv:#0c5460;--bg-pend:#fff3cd;--fg-pend:#856404;--bg-perd:#f8d7da;--fg-perd:#721c24;--bg-nula:#f3f4f6;--fg-nula:#4b5563;}
*{box-sizing:border-box;margin:0;padding:0;}
body{font-family:"Segoe UI",Arial,sans-serif;background:#F9FAFB;color:#111827;padding:1rem;}
.wrap{max-width:1400px;margin:0 auto;}
.top-bar{display:flex;justify-content:space-between;align-items:center;margin-bottom:1rem;flex-wrap:wrap;gap:12px;}
.header h1{font-size:22px;font-weight:600;color:var(--nu-blue);margin-bottom:4px;}
.header p{font-size:13px;color:#6B7280;}
.selector-container{display:flex;align-items:center;gap:8px;}
.selector-container label{font-size:13px;font-weight:600;color:var(--nu-blue);}
.month-select{padding:6px 32px 6px 12px;font-size:13px;border-radius:6px;border:1px solid #D1D5DB;background:white;font-weight:600;color:var(--nu-blue);cursor:pointer;outline:none;}
.month-select:focus{border-color:var(--nu-blue);box-shadow:0 0 0 2px rgba(27,42,78,0.1);}
.tabs-nav{display:flex;gap:4px;margin-bottom:1.5rem;border-bottom:2px solid #E5E7EB;overflow-x:auto;}
.tab-btn{background:none;border:none;padding:10px 16px;font-size:13px;font-weight:600;color:#6B7280;cursor:pointer;border-bottom:2px solid transparent;margin-bottom:-2px;white-space:nowrap;transition:color 0.2s;}
.tab-btn.active{color:var(--nu-blue);border-bottom-color:var(--nu-blue);}
.tab-btn:hover:not(.active){color:#374151;}
.tab-content{display:none;}.tab-content.active{display:block;}
.kpis{display:grid;grid-template-columns:repeat(auto-fit,minmax(190px,1fr));gap:15px;margin-bottom:1.5rem;}
.kpi{background:white;border:1px solid #E5E7EB;border-radius:8px;padding:1rem;border-left:4px solid var(--nu-orange);box-shadow:0 1px 2px rgba(0,0,0,0.05);}
.kpi-lbl{font-size:11px;color:#9CA3AF;text-transform:uppercase;letter-spacing:0.5px;font-weight:600;}
.kpi-val{font-size:24px;font-weight:700;color:var(--nu-blue);margin:4px 0 2px;}
.kpi-sub{font-size:12px;color:#6B7280;}
.split-layout{display:grid;grid-template-columns:1.4fr 1fr;gap:20px;align-items:start;}
.card{background:white;border:1px solid #E5E7EB;border-radius:8px;overflow-x:auto;box-shadow:0 1px 3px rgba(0,0,0,0.05);margin-bottom:1.5rem;}
.card-title{font-size:11px;font-weight:600;color:#6B7280;padding:12px;border-bottom:1px solid #E5E7EB;background:#FAFAFA;text-transform:uppercase;letter-spacing:0.5px;}
table.main{width:100%;border-collapse:collapse;font-size:12px;}
table.main th{font-size:10px;font-weight:600;color:#6B7280;text-align:center;padding:8px;border-bottom:2px solid #E5E7EB;text-transform:uppercase;background:#FAFAFA;white-space:nowrap;}
table.main td{text-align:center;padding:8px;transition:filter 0.1s;}
.clk-cell{cursor:pointer;}.clk-cell:hover{filter:brightness(0.93);}
.row-active td{border-top:1px solid var(--nu-blue);border-bottom:1px solid var(--nu-blue);}
.panel-container{background:white;border:1px solid #E5E7EB;border-radius:8px;display:flex;flex-direction:column;position:sticky;top:20px;height:520px;box-shadow:-5px 0 20px -10px rgba(0,0,0,0.1);border-left:4px solid var(--nu-blue);}
.panel-header{padding:15px;border-bottom:1px solid #E5E7EB;display:flex;justify-content:space-between;align-items:center;background:#FAFAFA;border-radius:0 8px 0 0;position:relative;}
.panel-title{font-size:14px;font-weight:600;color:var(--nu-blue);}
.panel-body{overflow-y:auto;flex-grow:1;padding:0;}
.panel-body::-webkit-scrollbar{width:6px;}.panel-body::-webkit-scrollbar-track{background:#F9FAFB;border-radius:4px;}
.panel-body::-webkit-scrollbar-thumb{background:#D1D5DB;border-radius:4px;}.panel-body::-webkit-scrollbar-thumb:hover{background:#9CA3AF;}
.panel-close-btn{display:none;}
.empty-state{text-align:center;padding:40px 20px;color:#9CA3AF;font-size:13px;}
.lista-table{width:100%;border-collapse:collapse;font-size:11px;}
.lista-table th{font-size:10px;color:#9CA3AF;padding:8px 10px;text-align:center;border-bottom:1px solid #E5E7EB;text-transform:uppercase;position:sticky;top:0;background:#FAFAFA;z-index:2;box-shadow:0 1px 0 #E5E7EB;}
.lista-table td{padding:8px 10px;border-bottom:1px solid #F3F4F6;text-align:center;white-space:nowrap;}
.lista-table td.left{text-align:left;max-width:160px;overflow:hidden;text-overflow:ellipsis;}
.lista-table td.right{text-align:right;font-variant-numeric:tabular-nums;}
.lista-table tr:hover td{background:#F9FAFB;}
.tag{display:inline-block;font-size:10px;padding:2px 6px;border-radius:4px;font-weight:600;}
.stock-search-bar{display:flex;gap:10px;flex-wrap:wrap;align-items:center;margin-bottom:1rem;}
.stock-search-bar input,.stock-search-bar select{padding:6px 12px;border:1px solid #D1D5DB;border-radius:6px;font-size:13px;outline:none;}
.stock-search-bar select{font-weight:600;color:var(--nu-blue);cursor:pointer;}
.modal-overlay{display:none;}
@media(max-width:992px){
  .split-layout{grid-template-columns:1fr;}
  .panel-container{display:none;position:fixed;top:50%;left:50%;transform:translate(-50%,-50%);width:90%;max-width:450px;height:auto;max-height:80vh;z-index:1000;box-shadow:0 20px 25px -5px rgba(0,0,0,0.1);border-left:1px solid #E5E7EB;border-radius:12px;}
  .panel-container.active{display:flex;}
  .panel-header{border-radius:12px 12px 0 0;padding-right:50px;}
  .panel-close-btn{display:flex;position:absolute;right:12px;top:12px;width:32px;height:32px;align-items:center;justify-content:center;background:#E5E7EB;border:none;border-radius:50%;font-size:20px;color:#4B5563;cursor:pointer;}
  .modal-overlay.active{display:block;position:fixed;top:0;left:0;width:100%;height:100%;background:rgba(17,24,39,0.7);z-index:999;}
}
.footer{text-align:center;font-size:11px;color:#9CA3AF;margin-top:2rem;padding-bottom:1rem;}
</style>
</head>
<body>
<div class="wrap">

  <div class="top-bar">
    <div class="header">
      <h1>Dashboard Comercial N&Uuml;PROTEC ANIO_</h1>
      <p>N&Uuml;PROTEC SpA &nbsp;&middot;&nbsp; GEN_</p>
    </div>
    <div class="selector-container">
      <label for="month-select">Periodo:</label>
      <select id="month-select" class="month-select" onchange="onMonthChange(this.value)">OPTS_</select>
    </div>
  </div>

  <nav class="tabs-nav">
    <button class="tab-btn active"  onclick="switchTab(this,\'cotizaciones\')">Cotizaciones</button>
    <button class="tab-btn"         onclick="switchTab(this,\'nv\')">Notas de Venta</button>
    <button class="tab-btn"         onclick="switchTab(this,\'pendientes\')">Pendientes A&ntilde;o</button>
    <button class="tab-btn"         onclick="switchTab(this,\'facturacion\')">Facturaci&oacute;n</button>
    <button class="tab-btn"         onclick="switchTab(this,\'stock\')">Stock</button>
  </nav>

  <!-- ════ TAB 1: COTIZACIONES ════ -->
  <div id="tab-cotizaciones" class="tab-content active">
    <div class="kpis">
      <div class="kpi"><div class="kpi-lbl">Total cotizaciones</div><div id="k-tot-n" class="kpi-val">0</div><div id="k-tot-m" class="kpi-sub">$0 neto</div></div>
      <div class="kpi"><div class="kpi-lbl">Convertidas a NV</div><div id="k-nv-n" class="kpi-val">0</div><div id="k-nv-m" class="kpi-sub">$0 monto NV</div></div>
      <div class="kpi"><div class="kpi-lbl">Tasa de conversi&oacute;n</div><div id="k-pct" class="kpi-val">0%</div><div id="k-pct-s" class="kpi-sub">sobre total</div></div>
      <div class="kpi"><div class="kpi-lbl">Pendientes</div><div id="k-pend-n" class="kpi-val">0</div><div id="k-pend-m" class="kpi-sub">$0 en cartera</div></div>
    </div>
    <div class="split-layout">
      <div class="card">
        <div class="card-title">Desempe&ntilde;o por vendedor &mdash; Clic en n&uacute;mero para ver detalle</div>
        <table class="main">
          <thead><tr>
            <th style="text-align:left;border-right:1px solid #E5E7EB">Vendedor</th>
            <th>NV N&deg;</th><th style="border-right:1px solid #E5E7EB">NV Monto</th>
            <th>Pend N&deg;</th><th style="border-right:1px solid #E5E7EB">Pend Monto</th>
            <th>Perd N&deg;</th><th style="border-right:1px solid #E5E7EB">Perd Monto</th>
            <th>Nula N&deg;</th><th style="border-right:1px solid #E5E7EB">Nula Monto</th>
            <th>Total N&deg;</th><th>Total Monto</th><th>Conv.</th>
          </tr></thead>
          <tbody id="coti-tbody"></tbody>
        </table>
      </div>
      <div id="detail-panel" class="panel-container">
        <div class="panel-header">
          <div id="panel-title" class="panel-title">Detalle</div>
          <button class="panel-close-btn" onclick="closeModal()">&times;</button>
        </div>
        <div id="panel-body" class="panel-body">
          <div class="empty-state">Selecciona un n&uacute;mero coloreado para ver el detalle.</div>
        </div>
      </div>
    </div>
  </div>

  <!-- ════ TAB 2: NOTAS DE VENTA ════ -->
  <div id="tab-nv" class="tab-content">
    <div class="kpis">
      <div class="kpi"><div class="kpi-lbl">Total NVs</div><div id="nv-n" class="kpi-val">0</div><div id="nv-m" class="kpi-sub">$0 monto</div></div>
      <div class="kpi"><div class="kpi-lbl">Facturadas</div><div id="nv-fact-n" class="kpi-val">0</div><div id="nv-fact-m" class="kpi-sub">$0 facturado</div></div>
      <div class="kpi"><div class="kpi-lbl">Sin facturar</div><div id="nv-sf-n" class="kpi-val">0</div><div id="nv-sf-m" class="kpi-sub">$0 pendiente</div></div>
    </div>
    <div class="card">
      <div class="card-title">Notas de Venta por vendedor</div>
      <table class="main">
        <thead><tr>
          <th style="text-align:left;border-right:1px solid #E5E7EB">Vendedor</th>
          <th>Total NVs</th><th style="border-right:1px solid #E5E7EB">Activas</th>
          <th style="background:#DCFCE7">Facturadas</th>
          <th style="background:#FEF9C3;border-right:1px solid #E5E7EB">Sin facturar</th>
          <th>Monto total</th><th>Facturado</th><th>Pendiente</th>
        </tr></thead>
        <tbody id="nv-tbody"></tbody>
      </table>
    </div>
  </div>

  <!-- ════ TAB 3: PENDIENTES AÑO ════ -->
  <div id="tab-pendientes" class="tab-content">
    <div class="card">
      <div class="card-title">Cotizaciones pendientes por mes &mdash; Acumulado a&ntilde;o completo</div>
      <div id="pend-content" style="overflow-x:auto"></div>
    </div>
  </div>

  <!-- ════ TAB 4: FACTURACIÓN ════ -->
  <div id="tab-facturacion" class="tab-content">
    <div class="kpis">
      <div class="kpi"><div class="kpi-lbl">Facturado bruto</div><div id="f-bruto" class="kpi-val">$0</div><div id="f-bruto-n" class="kpi-sub">0 documentos</div></div>
      <div class="kpi"><div class="kpi-lbl">Notas de cr&eacute;dito</div><div id="f-nc" class="kpi-val">$0</div><div id="f-nc-n" class="kpi-sub">0 NC</div></div>
      <div class="kpi"><div class="kpi-lbl">Neto mes</div><div id="f-neto" class="kpi-val">$0</div><div id="f-neto-s" class="kpi-sub">despu&eacute;s de NC</div></div>
    </div>
    <div class="card">
      <div class="card-title">Facturaci&oacute;n por vendedor</div>
      <table class="main">
        <thead><tr>
          <th style="text-align:left;border-right:1px solid #E5E7EB">Vendedor</th>
          <th>N&deg; Facturas</th><th style="border-right:1px solid #E5E7EB">Monto bruto</th>
          <th>N&deg; NC</th><th style="border-right:1px solid #E5E7EB">Monto NC</th>
          <th>Neto final</th>
        </tr></thead>
        <tbody id="fact-tbody"></tbody>
      </table>
    </div>
  </div>

  <!-- ════ TAB 5: STOCK ════ -->
  <div id="tab-stock" class="tab-content">
    <div class="stock-search-bar">
      <input type="text" id="st-search" placeholder="Buscar producto o c&oacute;digo..." oninput="filterStock()">
      <select id="st-grupo" onchange="filterStock()"><option value="">Todos los grupos</option></select>
      <span id="st-count" style="font-size:12px;color:#6B7280"></span>
    </div>
    <div class="card">
      <div class="card-title">Stock actual &mdash; Bodegas 08 (Chesterton) y 20 (Recoleta)</div>
      <div style="overflow-x:auto">
        <table class="main">
          <thead><tr>
            <th style="text-align:left">Producto</th>
            <th style="text-align:left;border-right:1px solid #E5E7EB">Grupo</th>
            <th>Bod.08</th><th>Bod.20</th>
            <th style="border-right:1px solid #E5E7EB">Total</th>
            <th>Costo unit.</th><th>Precio neto</th><th>Valor stock</th>
          </tr></thead>
          <tbody id="st-tbody"></tbody>
        </table>
      </div>
    </div>
  </div>

  <div class="footer">N&Uuml;PROTEC SpA &nbsp;&middot;&nbsp; Informe generado autom&aacute;ticamente &nbsp;&middot;&nbsp; GEN_</div>
</div>
<div id="modal-overlay" class="modal-overlay" onclick="closeModal()"></div>

<script>
var RESUMEN    = RESUMEN_;
var DATA       = DATA_;
var NV_RES     = NV_RES_;
var FACT_RES   = FACT_RES_;
var PEND_ANIO  = PEND_;
var STOCK      = STOCK_;
var Q          = String.fromCharCode(39);
var mesActual  = \'MES_\';
var lastRow    = null;
var stockAll   = STOCK.slice();
var stockFilt  = stockAll.slice();
var MESES_ABR  = [\'\',\'Ene\',\'Feb\',\'Mar\',\'Abr\',\'May\',\'Jun\',\'Jul\',\'Ago\',\'Sep\',\'Oct\',\'Nov\',\'Dic\'];

function clp(v){ return \'$\' + Math.round(v).toLocaleString(\'es-CL\'); }
function n0(v){ return v || 0; }

function switchTab(btn, id){
  document.querySelectorAll(\'.tab-btn\').forEach(function(b){ b.classList.remove(\'active\'); });
  document.querySelectorAll(\'.tab-content\').forEach(function(c){ c.classList.remove(\'active\'); });
  btn.classList.add(\'active\');
  document.getElementById(\'tab-\' + id).classList.add(\'active\');
}

function onMonthChange(mes){
  mesActual = String(mes);
  updateCotiTab(mes);
  updateNVTab(mes);
  updateFactTab(mes);
}

/* ══ TAB COTIZACIONES ══════════════════════════════════════════════ */
function updateCotiTab(mes){
  mes = String(mes); mesActual = mes;
  var rows = RESUMEN[mes] || [];
  var tn=0,tm=0,tnv=0,tnvm=0,pn=0,pm=0;
  rows.forEach(function(r){
    tn+=r.Total_N; tm+=r.Total_Monto; tnv+=r.EnNV_N; tnvm+=r.EnNV_Monto;
    pn+=r.Pendiente_N; pm+=r.Pendiente_Monto;
  });
  var pct = tn>0 ? Math.round(tnv/tn*1000)/10 : 0;
  document.getElementById(\'k-tot-n\').textContent = tn;
  document.getElementById(\'k-tot-m\').textContent = clp(tm)+\' neto\';
  document.getElementById(\'k-nv-n\').textContent  = tnv;
  document.getElementById(\'k-nv-m\').textContent  = clp(tnvm)+\' monto NV\';
  document.getElementById(\'k-pct\').textContent   = pct+\'%\';
  document.getElementById(\'k-pct-s\').textContent = \'sobre \'+tn+\' cotizaciones\';
  document.getElementById(\'k-pend-n\').textContent= pn;
  document.getElementById(\'k-pend-m\').textContent= clp(pm)+\' en cartera\';

  var tbody = document.getElementById(\'coti-tbody\');
  if(!rows.length){ tbody.innerHTML=\'<tr><td colspan="12" style="text-align:center;padding:40px;color:#9CA3AF">Sin datos para este periodo.</td></tr>\'; resetPanel(); return; }

  var html=\'\';
  var s={nv_n:0,nv_m:0,pnd_n:0,pnd_m:0,prd_n:0,prd_m:0,nla_n:0,nla_m:0,tot_n:0,tot_m:0};
  rows.forEach(function(row){
    s.nv_n+=row.EnNV_N; s.nv_m+=row.EnNV_Monto;
    s.pnd_n+=row.Pendiente_N; s.pnd_m+=row.Pendiente_Monto;
    s.prd_n+=row.Perdida_N; s.prd_m+=row.Perdida_Monto;
    s.nla_n+=row.Nula_N; s.nla_m+=row.Nula_Monto;
    s.tot_n+=row.Total_N; s.tot_m+=row.Total_Monto;
    var vnd = row.Vendedor;
    var cols=[
      {e:\'En NV\',   n:row.EnNV_N,     m:row.EnNV_Monto,     bg:\'var(--bg-nv)\',  fg:\'var(--fg-nv)\'},
      {e:\'Pendiente\',n:row.Pendiente_N,m:row.Pendiente_Monto,bg:\'var(--bg-pend)\',fg:\'var(--fg-pend)\'},
      {e:\'Perdida\',  n:row.Perdida_N,  m:row.Perdida_Monto,  bg:\'var(--bg-perd)\',fg:\'var(--fg-perd)\'},
      {e:\'Nula\',     n:row.Nula_N,     m:row.Nula_Monto,     bg:\'var(--bg-nula)\',fg:\'var(--fg-nula)\'}
    ];
    html+=\'<tr style="border-bottom:1px solid #E5E7EB">\';
    html+=\'<td style="padding:8px;font-weight:600;text-align:left;border-right:1px solid #E5E7EB">\'+vnd+\'</td>\';
    cols.forEach(function(col,ci){
      var br=ci===3?\'border-right:1px solid #E5E7EB;\':\'\'
      if(col.n>0){
        var oc=\'showDetail(\'+Q+vnd+Q+\',\'+Q+col.e+Q+\',this)\';
        html+=\'<td class="clk-cell" onclick="\'+oc+\'" style="background:\'+col.bg+\';color:\'+col.fg+\';font-weight:700">\'+col.n+\'</td>\';
        html+=\'<td class="clk-cell" onclick="\'+oc+\'" style="background:\'+col.bg+\';color:\'+col.fg+\';\'+br+\'">\'+clp(col.m)+\'</td>\';
      } else {
        html+=\'<td style="color:#D1D5DB">0</td><td style="color:#D1D5DB;\'+br+\'">$0</td>\';
      }
    });
    html+=\'<td style="padding:8px;font-weight:600;text-align:right;border-left:1px solid #E5E7EB">\'+row.Total_N+\'</td>\';
    html+=\'<td style="padding:8px;font-weight:600;text-align:right">\'+clp(row.Total_Monto)+\'</td>\';
    html+=\'<td style="padding:8px;font-weight:700;color:var(--nu-blue);text-align:right">\'+row.Pct_Conv+\'%</td>\';
    html+=\'</tr>\';
  });
  var sp = s.tot_n>0 ? Math.round(s.nv_n/s.tot_n*1000)/10 : 0;
  html+=\'<tr style="background:#F3F4F6;border-top:2px solid #D1D5DB;font-weight:700">\';
  html+=\'<td style="padding:8px;text-align:left;border-right:1px solid #E5E7EB;color:#374151;font-size:11px;text-transform:uppercase;letter-spacing:.5px">TOTAL</td>\';
  html+=\'<td style="background:var(--bg-nv);color:var(--fg-nv)">\'+s.nv_n+\'</td><td style="background:var(--bg-nv);color:var(--fg-nv);border-right:1px solid #E5E7EB">\'+clp(s.nv_m)+\'</td>\';
  html+=\'<td style="background:var(--bg-pend);color:var(--fg-pend)">\'+s.pnd_n+\'</td><td style="background:var(--bg-pend);color:var(--fg-pend);border-right:1px solid #E5E7EB">\'+clp(s.pnd_m)+\'</td>\';
  html+=\'<td style="background:var(--bg-perd);color:var(--fg-perd)">\'+s.prd_n+\'</td><td style="background:var(--bg-perd);color:var(--fg-perd);border-right:1px solid #E5E7EB">\'+clp(s.prd_m)+\'</td>\';
  html+=\'<td style="background:var(--bg-nula);color:var(--fg-nula)">\'+s.nla_n+\'</td><td style="background:var(--bg-nula);color:var(--fg-nula);border-right:1px solid #E5E7EB">\'+clp(s.nla_m)+\'</td>\';
  html+=\'<td style="padding:8px;text-align:right;border-left:1px solid #E5E7EB">\'+s.tot_n+\'</td>\';
  html+=\'<td style="padding:8px;text-align:right">\'+clp(s.tot_m)+\'</td>\';
  html+=\'<td style="padding:8px;text-align:right;color:var(--nu-blue)">\'+sp+\'%</td></tr>\';
  tbody.innerHTML = html;
  resetPanel();
}

function resetPanel(){
  if(lastRow) lastRow.classList.remove(\'row-active\');
  lastRow = null;
  document.getElementById(\'panel-title\').textContent = \'Detalle\';
  document.getElementById(\'panel-body\').innerHTML = \'<div class="empty-state">Selecciona un n&uacute;mero coloreado para ver el detalle.</div>\';
}

function showDetail(vend, estado, cellEl){
  if(lastRow) lastRow.classList.remove(\'row-active\');
  lastRow = cellEl.parentElement;
  lastRow.classList.add(\'row-active\');
  var cm={\'En NV\':\'var(--fg-nv)\',\'Pendiente\':\'var(--fg-pend)\',\'Perdida\':\'var(--fg-perd)\',\'Nula\':\'var(--fg-nula)\'};
  document.getElementById(\'panel-title\').innerHTML=\'<span style="color:\'+cm[estado]+\'">\'+estado+\'</span> &middot; <span style="color:#6B7280">\'+vend+\'</span>\';
  var d = DATA[mesActual] && DATA[mesActual][vend] && DATA[mesActual][vend][estado];
  if(!d||!d.cotis.length){ document.getElementById(\'panel-body\').innerHTML=\'<div class="empty-state">Sin datos.</div>\'; return; }
  var ac={\'Vencida\':\'#DC2626\',\'Vence <=7d\':\'#D97706\',\'Vence <=15d\':\'#CA8A04\',\'Vigente\':\'#6B7280\',\'Convertida\':\'#0c5460\',\'Cerrada\':\'#9CA3AF\'};
  var html=\'<table class="lista-table"><thead><tr><th>N&deg;</th><th class="left">Fecha</th><th class="left">Cliente</th><th>Grupo</th><th>Alerta</th><th class="right">Monto</th></tr></thead><tbody>\';
  d.cotis.forEach(function(c){
    var nG=c.grupos.length;
    c.grupos.forEach(function(g,gi){
      html+=\'<tr>\';
      if(gi===0){
        var rs=nG>1?\' rowspan="\'+nG+\'"\':\'\';
        html+=\'<td\'+rs+\' style="font-weight:600;color:var(--nu-blue)">\'+c.num+\'</td>\';
        html+=\'<td\'+rs+\' class="left" style="color:#9CA3AF">\'+c.fecha+\'</td>\';
        html+=\'<td\'+rs+\' class="left"><strong style="color:#374151">\'+c.cliente+\'</strong></td>\';
      }
      html+=\'<td><span class="tag" style="background:#F3F4F6;color:#374151">\'+g.g+\'</span></td>\';
      if(gi===0){
        var col=ac[c.alerta]||\'#6B7280\';
        html+=\'<td\'+( nG>1?\' rowspan="\'+nG+\'"\':\'\' )+\'><span style="font-size:10px;color:\'+col+\';font-weight:600">\'+c.alerta+\'</span></td>\';
      }
      html+=\'<td class="right" style="font-weight:500">\'+clp(g.m)+\'</td></tr>\';
    });
  });
  html+=\'<tr style="background:#F9FAFB;border-top:2px solid #E5E7EB"><td colspan="5" class="right" style="font-size:10px;color:#6B7280;font-weight:600;padding:12px 10px">TOTAL</td><td class="right" style="font-weight:700;color:var(--nu-blue);font-size:13px;padding:12px 10px">\'+clp(d.monto)+\'</td></tr>\';
  html+=\'</tbody></table>\';
  document.getElementById(\'panel-body\').innerHTML = html;
  if(window.innerWidth<=992){
    document.getElementById(\'detail-panel\').classList.add(\'active\');
    document.getElementById(\'modal-overlay\').classList.add(\'active\');
    document.body.style.overflow=\'hidden\';
  }
}

function closeModal(){
  document.getElementById(\'detail-panel\').classList.remove(\'active\');
  document.getElementById(\'modal-overlay\').classList.remove(\'active\');
  document.body.style.overflow=\'\';
  if(lastRow) lastRow.classList.remove(\'row-active\');
}

/* ══ TAB NOTAS DE VENTA ════════════════════════════════════════════ */
function updateNVTab(mes){
  mes=String(mes);
  var rows=NV_RES[mes]||[];
  var tn=0,tm=0,fn=0,fm=0,sn=0,sm=0;
  rows.forEach(function(r){ tn+=r.Total_N; tm+=r.MontoTotal; fn+=r.Facturadas; fm+=r.MontoFact; sn+=r.SinFacturar; sm+=r.MontoPend; });
  document.getElementById(\'nv-n\').textContent=tn;
  document.getElementById(\'nv-m\').textContent=clp(tm)+\' monto\';
  document.getElementById(\'nv-fact-n\').textContent=fn;
  document.getElementById(\'nv-fact-m\').textContent=clp(fm)+\' facturado\';
  document.getElementById(\'nv-sf-n\').textContent=sn;
  document.getElementById(\'nv-sf-m\').textContent=clp(sm)+\' pendiente\';
  var tbody=document.getElementById(\'nv-tbody\');
  if(!rows.length){ tbody.innerHTML=\'<tr><td colspan="8" style="text-align:center;padding:40px;color:#9CA3AF">Sin datos.</td></tr>\'; return; }
  var html=\'\'; var s={n:0,a:0,f:0,sf:0,m:0,mf:0,mp:0};
  rows.forEach(function(r){
    s.n+=r.Total_N; s.a+=r.Activas; s.f+=r.Facturadas; s.sf+=r.SinFacturar; s.m+=r.MontoTotal; s.mf+=r.MontoFact; s.mp+=r.MontoPend;
    html+=\'<tr style="border-bottom:1px solid #E5E7EB">\';
    html+=\'<td style="padding:8px;font-weight:600;text-align:left;border-right:1px solid #E5E7EB">\'+r.Vendedor+\'</td>\';
    html+=\'<td style="font-weight:600">\'+r.Total_N+\'</td>\';
    html+=\'<td style="color:var(--fg-nv);border-right:1px solid #E5E7EB">\'+r.Activas+\'</td>\';
    html+=\'<td style="background:#DCFCE7;color:#15803D;font-weight:700">\'+r.Facturadas+\'</td>\';
    html+=\'<td style="background:#FEF9C3;color:#D97706;font-weight:700;border-right:1px solid #E5E7EB">\'+r.SinFacturar+\'</td>\';
    html+=\'<td style="text-align:right;font-weight:600">\'+clp(r.MontoTotal)+\'</td>\';
    html+=\'<td style="text-align:right;color:#15803D">\'+clp(r.MontoFact)+\'</td>\';
    html+=\'<td style="text-align:right;color:#D97706">\'+clp(r.MontoPend)+\'</td></tr>\';
  });
  html+=\'<tr style="background:#F3F4F6;border-top:2px solid #D1D5DB;font-weight:700">\';
  html+=\'<td style="padding:8px;text-align:left;border-right:1px solid #E5E7EB;font-size:11px;text-transform:uppercase;color:#374151">TOTAL</td>\';
  html+=\'<td>\'+s.n+\'</td><td style="border-right:1px solid #E5E7EB">\'+s.a+\'</td>\';
  html+=\'<td style="background:#DCFCE7;color:#15803D">\'+s.f+\'</td>\';
  html+=\'<td style="background:#FEF9C3;color:#D97706;border-right:1px solid #E5E7EB">\'+s.sf+\'</td>\';
  html+=\'<td style="text-align:right">\'+clp(s.m)+\'</td>\';
  html+=\'<td style="text-align:right;color:#15803D">\'+clp(s.mf)+\'</td>\';
  html+=\'<td style="text-align:right;color:#D97706">\'+clp(s.mp)+\'</td></tr>\';
  tbody.innerHTML=html;
}

/* ══ TAB PENDIENTES AÑO ════════════════════════════════════════════ */
function updatePendTab(){
  var vendedores={};
  for(var m=1;m<=12;m++){
    (PEND_ANIO[String(m)]||[]).forEach(function(r){
      if(!vendedores[r.Vendedor]) vendedores[r.Vendedor]={};
      vendedores[r.Vendedor][m]=r;
    });
  }
  var html=\'<table class="main" style="font-size:11px"><thead><tr>\';
  html+=\'<th style="text-align:left;border-right:1px solid #E5E7EB;min-width:130px">Vendedor</th>\';
  for(var m=1;m<=12;m++) html+=\'<th colspan="2" style="border-right:1px solid #E5E7EB">\'+MESES_ABR[m]+\'</th>\';
  html+=\'<th>Total N&deg;</th><th>Total $</th></tr>\';
  html+=\'<tr><th style="border-right:1px solid #E5E7EB"></th>\';
  for(var m=1;m<=12;m++) html+=\'<th style="font-size:9px">N&deg;</th><th style="font-size:9px;border-right:1px solid #E5E7EB">Monto</th>\';
  html+=\'<th></th><th></th></tr></thead><tbody>\';
  Object.keys(vendedores).sort().forEach(function(vend){
    var tot_n=0, tot_m=0;
    html+=\'<tr style="border-bottom:1px solid #E5E7EB">\';
    html+=\'<td style="padding:6px 8px;font-weight:600;text-align:left;border-right:1px solid #E5E7EB">\'+vend+\'</td>\';
    for(var m=1;m<=12;m++){
      var d=vendedores[vend][m];
      if(d&&d.Total>0){
        tot_n+=d.Total; tot_m+=d.Monto;
        var bg=d.Vencidas>0?\'background:var(--bg-perd);color:var(--fg-perd)\':d.Prox7>0?\'background:var(--bg-pend);color:var(--fg-pend)\':\'background:var(--bg-nv);color:var(--fg-nv)\';
        html+=\'<td style="\'+bg+\';font-weight:700;font-size:11px">\'+d.Total+\'</td>\';
        html+=\'<td style="text-align:right;border-right:1px solid #E5E7EB;font-size:10px">\'+clp(d.Monto)+\'</td>\';
      } else {
        html+=\'<td style="color:#D1D5DB;font-size:11px">&mdash;</td><td style="color:#D1D5DB;border-right:1px solid #E5E7EB">&mdash;</td>\';
      }
    }
    html+=\'<td style="padding:6px 8px;font-weight:700;text-align:right">\'+tot_n+\'</td>\';
    html+=\'<td style="padding:6px 8px;font-weight:700;text-align:right">\'+clp(tot_m)+\'</td></tr>\';
  });
  html+=\'</tbody></table>\';
  document.getElementById(\'pend-content\').innerHTML=html;
}

/* ══ TAB FACTURACIÓN ════════════════════════════════════════════════ */
function updateFactTab(mes){
  mes=String(mes);
  var rows=FACT_RES[mes]||[];
  var bruto=0,nc=0,neto=0,nf=0,nnc=0;
  rows.forEach(function(r){ bruto+=r.MontoBruto; nc+=r.MontoNC; neto+=r.MontoNeto; nf+=r.N_Facturas; nnc+=r.N_NC; });
  document.getElementById(\'f-bruto\').textContent=clp(bruto);
  document.getElementById(\'f-bruto-n\').textContent=nf+\' documentos\';
  document.getElementById(\'f-nc\').textContent=clp(nc);
  document.getElementById(\'f-nc-n\').textContent=nnc+\' NC emitidas\';
  document.getElementById(\'f-neto\').textContent=clp(neto);
  document.getElementById(\'f-neto-s\').textContent=\'despu&eacute;s de NC\';
  var tbody=document.getElementById(\'fact-tbody\');
  if(!rows.length){ tbody.innerHTML=\'<tr><td colspan="6" style="text-align:center;padding:40px;color:#9CA3AF">Sin datos.</td></tr>\'; return; }
  var html=\'\'; var s={nf:0,mb:0,nc_n:0,nc:0,nt:0};
  rows.forEach(function(r){
    s.nf+=r.N_Facturas; s.mb+=r.MontoBruto; s.nc_n+=r.N_NC; s.nc+=r.MontoNC; s.nt+=r.MontoNeto;
    html+=\'<tr style="border-bottom:1px solid #E5E7EB">\';
    html+=\'<td style="padding:8px;font-weight:600;text-align:left;border-right:1px solid #E5E7EB">\'+r.Vendedor+\'</td>\';
    html+=\'<td style="font-weight:600">\'+r.N_Facturas+\'</td>\';
    html+=\'<td style="text-align:right;border-right:1px solid #E5E7EB">\'+clp(r.MontoBruto)+\'</td>\';
    html+=\'<td style="color:#721c24">\'+(r.N_NC>0?r.N_NC:\'&mdash;\')+\'</td>\';
    html+=\'<td style="text-align:right;color:#721c24;border-right:1px solid #E5E7EB">\'+(r.MontoNC>0?clp(r.MontoNC):\'&mdash;\')+\'</td>\';
    html+=\'<td style="text-align:right;font-weight:700;color:var(--nu-blue)">\'+clp(r.MontoNeto)+\'</td></tr>\';
  });
  html+=\'<tr style="background:#F3F4F6;border-top:2px solid #D1D5DB;font-weight:700">\';
  html+=\'<td style="padding:8px;text-align:left;border-right:1px solid #E5E7EB;font-size:11px;text-transform:uppercase;color:#374151">TOTAL</td>\';
  html+=\'<td>\'+s.nf+\'</td><td style="text-align:right;border-right:1px solid #E5E7EB">\'+clp(s.mb)+\'</td>\';
  html+=\'<td>\'+s.nc_n+\'</td><td style="text-align:right;color:#721c24;border-right:1px solid #E5E7EB">\'+clp(s.nc)+\'</td>\';
  html+=\'<td style="text-align:right;color:var(--nu-blue)">\'+clp(s.nt)+\'</td></tr>\';
  tbody.innerHTML=html;
}

/* ══ TAB STOCK ══════════════════════════════════════════════════════ */
function initStock(){
  var grupos=[...new Set(stockAll.map(function(s){ return s.grupo; }))].sort();
  var sel=document.getElementById(\'st-grupo\');
  grupos.forEach(function(g){
    var o=document.createElement(\'option\'); o.value=g; o.textContent=g; sel.appendChild(o);
  });
  filterStock();
}

function filterStock(){
  var q=document.getElementById(\'st-search\').value.toLowerCase();
  var g=document.getElementById(\'st-grupo\').value;
  stockFilt=stockAll.filter(function(s){
    return (!g||s.grupo===g) && (!q||s.prod.toLowerCase().includes(q)||s.cod.toLowerCase().includes(q));
  });
  renderStock();
}

function renderStock(){
  var tbody=document.getElementById(\'st-tbody\');
  document.getElementById(\'st-count\').textContent=stockFilt.length+\' productos\';
  if(!stockFilt.length){ tbody.innerHTML=\'<tr><td colspan="8" style="text-align:center;padding:40px;color:#9CA3AF">Sin resultados.</td></tr>\'; return; }
  var html=\'\'; var ss08=0,ss20=0,stot=0,sval=0;
  stockFilt.forEach(function(s){
    ss08+=s.s08; ss20+=s.s20; stot+=s.total; sval+=s.valor;
    html+=\'<tr style="border-bottom:1px solid #F3F4F6">\';
    html+=\'<td style="padding:6px 8px;text-align:left;max-width:220px;overflow:hidden;text-overflow:ellipsis;white-space:nowrap" title="\'+s.prod+\'">\'+s.prod+\'</td>\';
    html+=\'<td style="padding:6px 8px;text-align:left;border-right:1px solid #E5E7EB"><span class="tag" style="background:#F3F4F6;color:#374151">\'+s.grupo+\'</span></td>\';
    html+=\'<td>\'+s.s08.toLocaleString(\'es-CL\')+\'</td>\';
    html+=\'<td>\'+s.s20.toLocaleString(\'es-CL\')+\'</td>\';
    html+=\'<td style="font-weight:700;border-right:1px solid #E5E7EB">\'+s.total.toLocaleString(\'es-CL\')+\'</td>\';
    html+=\'<td style="text-align:right">\'+clp(s.costo)+\'</td>\';
    html+=\'<td style="text-align:right">\'+clp(s.precio)+\'</td>\';
    html+=\'<td style="text-align:right;font-weight:600;color:var(--nu-blue)">\'+clp(s.valor)+\'</td></tr>\';
  });
  html+=\'<tr style="background:#F3F4F6;border-top:2px solid #D1D5DB;font-weight:700">\';
  html+=\'<td colspan="2" style="padding:8px;text-align:left;border-right:1px solid #E5E7EB;font-size:11px;text-transform:uppercase;color:#374151">TOTAL (\'+stockFilt.length+\' productos)</td>\';
  html+=\'<td>\'+ss08.toLocaleString(\'es-CL\')+\'</td><td>\'+ss20.toLocaleString(\'es-CL\')+\'</td>\';
  html+=\'<td style="border-right:1px solid #E5E7EB">\'+stot.toLocaleString(\'es-CL\')+\'</td>\';
  html+=\'<td colspan="2" style="text-align:right;color:#6B7280;font-size:11px">Valor total stock:</td>\';
  html+=\'<td style="text-align:right;color:var(--nu-blue)">\'+clp(sval)+\'</td></tr>\';
  tbody.innerHTML=html;
}

/* ══ INICIO ══════════════════════════════════════════════════════════ */
updateCotiTab(\'MES_\');
updateNVTab(\'MES_\');
updateFactTab(\'MES_\');
updatePendTab();
initStock();
</script>
</body></html>'''

# Reemplazar placeholders (no f-string para evitar conflicto con llaves CSS)
html = (HTML_TEMPLATE
    .replace('ANIO_',    str(anio))
    .replace('GEN_',     gen_str)
    .replace('OPTS_',    opts)
    .replace('MES_',     str(mes_act))
    .replace('RESUMEN_', js_safe(RESUMEN))
    .replace('DATA_',    js_safe(DATA))
    .replace('NV_RES_',  js_safe(NV_RESUMEN))
    .replace('FACT_RES_',js_safe(FACT_RESUMEN))
    .replace('PEND_',    js_safe(PEND_ANIO))
    .replace('STOCK_',   js_safe(STOCK_DATA))
)

nombre_archivo = f'Dashboard_NUPROTEC_{anio}.html'
with open(nombre_archivo, 'w', encoding='utf-8') as f:
    f.write(html)
print(f'HTML generado: {nombre_archivo} ({len(html)//1024} KB)')

# ══════════════════════════════════════════════════════════════════════════════
# MAIL RESUMEN
# ══════════════════════════════════════════════════════════════════════════════
def clp_py(v):
    try: return f"${int(round(v)):,}".replace(',', '.')
    except: return '—'

datos_m = RESUMEN.get(str(mes_act), [])
tn_m  = sum(r['Total_N']     for r in datos_m)
tm_m  = sum(r['Total_Monto'] for r in datos_m)
nv_m  = sum(r['EnNV_N']      for r in datos_m)
pn_m  = sum(r['Pendiente_N'] for r in datos_m)
pm_m  = sum(r['Pendiente_Monto'] for r in datos_m)
pc_m  = round(nv_m / tn_m * 100, 1) if tn_m else 0
url_pub = f'https://{GITHUB_USER}.github.io/{GITHUB_REPO}/{nombre_archivo}'

filas_m = ''.join(
    f"<tr><td>{r['Vendedor']}</td>"
    f"<td>{r['Pendiente_N']}</td><td>{clp_py(r['Pendiente_Monto'])}</td>"
    f"<td>{r['EnNV_N']}</td><td>{clp_py(r['EnNV_Monto'])}</td>"
    f"<td>{r['Total_N']}</td><td>{clp_py(r['Total_Monto'])}</td>"
    f"<td style='color:#1D4ED8;font-weight:600'>{r['Pct_Conv']}%</td></tr>"
    for r in sorted(datos_m, key=lambda x: -x['Total_Monto'])
)
filas_m += (
    f"<tr style='background:#F9FAFB;font-weight:700;border-top:2px solid #E5E7EB'>"
    f"<td>TOTAL</td><td>{pn_m}</td><td>{clp_py(pm_m)}</td>"
    f"<td>{nv_m}</td><td>—</td><td>{tn_m}</td><td>{clp_py(tm_m)}</td>"
    f"<td style='color:#1D4ED8'>{pc_m}%</td></tr>"
)

MAIL_HTML = f"""<!DOCTYPE html><html lang='es'><head><meta charset='UTF-8'>
<style>
body{{font-family:'Segoe UI',Arial,sans-serif;background:#F3F4F6;margin:0;padding:16px}}
.wrap{{max-width:620px;margin:0 auto;background:#fff;border-radius:10px;overflow:hidden;border:1px solid #E5E7EB}}
.top{{background:#1B2A4E;padding:16px 20px}}
.top h1{{color:#fff;font-size:15px;font-weight:600;margin:0}}
.top p{{color:#93A4C4;font-size:11px;margin:3px 0 0}}
.body{{padding:16px 20px}}
.kpis{{display:grid;grid-template-columns:repeat(3,1fr);gap:8px;margin-bottom:12px}}
.kpi{{background:#F9FAFB;border:1px solid #E5E7EB;border-radius:6px;padding:8px;border-left:3px solid #C44918}}
.kpi-lbl{{font-size:10px;color:#9CA3AF;text-transform:uppercase;letter-spacing:.4px}}
.kpi-val{{font-size:16px;font-weight:700;color:#1B2A4E;margin:2px 0}}
.kpi-sub{{font-size:10px;color:#9CA3AF}}
table{{width:100%;border-collapse:collapse;font-size:12px;margin-bottom:12px}}
th{{font-size:10px;color:#9CA3AF;padding:5px 7px;text-align:right;border-bottom:1px solid #E5E7EB;text-transform:uppercase;background:#FAFAFA}}
th:first-child{{text-align:left}}
td{{padding:5px 7px;border-bottom:1px solid #F3F4F6;text-align:right;color:#111827}}
td:first-child{{text-align:left;font-weight:500}}
.btn{{display:block;background:#1B2A4E;color:#fff;text-align:center;padding:10px;border-radius:7px;text-decoration:none;font-weight:600;font-size:13px}}
.footer{{text-align:center;font-size:10px;color:#9CA3AF;padding:10px}}
</style></head><body>
<div class='wrap'>
  <div class='top'>
    <h1>Dashboard Comercial &mdash; {nombre_mes}</h1>
    <p>N&Uuml;PROTEC SpA &middot; {gen_str}</p>
  </div>
  <div class='body'>
    <p style="font-size:13px;color:#374151;margin-bottom:15px;">
      Estimados, se adjunta el resumen comercial del periodo. Ver el dashboard completo en el link al final.
    </p>
    <div class='kpis'>
      <div class='kpi'><div class='kpi-lbl'>Cotizaciones</div><div class='kpi-val'>{tn_m}</div><div class='kpi-sub'>{clp_py(tm_m)}</div></div>
      <div class='kpi'><div class='kpi-lbl'>En NV</div><div class='kpi-val'>{nv_m}</div><div class='kpi-sub'>{pc_m}% conv.</div></div>
      <div class='kpi'><div class='kpi-lbl'>Pendientes</div><div class='kpi-val'>{pn_m}</div><div class='kpi-sub'>{clp_py(pm_m)}</div></div>
    </div>
    <table><thead><tr>
      <th>Vendedor</th><th>Pend.</th><th>Monto</th>
      <th>En NV</th><th>Monto</th><th>Total</th><th>Monto</th><th>Conv.</th>
    </tr></thead><tbody>{filas_m}</tbody></table>
    <a href='{url_pub}' class='btn'>Ver dashboard completo &rarr;</a>
  </div>
  <div class='footer'>N&Uuml;PROTEC SpA &mdash; Generado autom&aacute;ticamente</div>
</div></body></html>"""

if GMAIL_PASS:
    try:
        msg = MIMEMultipart('alternative')
        msg['Subject'] = f'Dashboard Comercial NUPROTEC — {nombre_mes}'
        msg['From']    = GMAIL_USER
        msg['To']      = MAIL_DESTINO
        msg.attach(MIMEText(MAIL_HTML, 'html'))
        with smtplib.SMTP_SSL('smtp.gmail.com', 465) as s:
            s.login(GMAIL_USER, GMAIL_PASS)
            s.sendmail(GMAIL_USER, MAIL_DESTINO, msg.as_string())
        print(f'Mail enviado a {MAIL_DESTINO}')
    except Exception as e:
        print(f'Error al enviar mail: {e}')
else:
    print('GMAIL_PASS no configurado — mail omitido')
