import pandas as pd
import numpy as np
import pyodbc
import json
from datetime import datetime

# Leer fechas desde config_fechas.json
with open("config_fechas.json", "r", encoding="utf-8") as f:
    config = json.load(f)

fecha_inicio = pd.to_datetime(config["fecha_inicio"])
fecha_fin = pd.to_datetime(config["fecha_fin"]) + pd.Timedelta(hours=23, minutes=59, seconds=59)

# Configura tu conexión
conn_str = (
*
)
conn = pyodbc.connect(conn_str)

# Consulta SQL sin filtro de fecha
query = """
SELECT 
  [AnotacionUnidad], [Tipo], [FechaHistorico], [Asunto], [Anotacion],
  [Realizado], [TipoPersonal], [Unidad], [IndiceMaestro], [Servicio],
  [IdTurnoHistorico], [Id], [FH], [Informativa], [EsTrafico], [EsOrden],
  [EsLibre], [AnotacionOperativa], [Codigo], [IndiceOrden], [IdOrden],
  [IdHistorico], [GMSn], [GMSo], [Situacion], [Hora], [Agentes],
  [NoRealiza], [NoRealizadoPor], [IdAsunto], [Observaciones], [Area]
FROM [_VM6000_Seguimientos_Ordenes_Esther]
WHERE FH IS NOT NULL
"""

# Leer datos
df = pd.read_sql(query, conn)
df['FH'] = pd.to_datetime(df['FH'], errors='coerce')

# Filtrar por fechas desde JSON
df_filtrado = df[(df['FH'] >= fecha_inicio) & (df['FH'] <= fecha_fin)].copy()

# Agregar columna Fecha
df_filtrado['Fecha'] = df_filtrado['FH'].dt.date

# Agrupar diario
resumen_dia = df_filtrado.groupby('Fecha').agg(
    Total=('Id', 'count'),
    Realizados=('NoRealiza', lambda x: ((x == 0) | (x.isna())).sum())
).reset_index()

# Porcentaje realizados
resumen_dia['PorcentajeRealizados'] = round((resumen_dia['Realizados'] / resumen_dia['Total']) * 100, 1)

# Tasa base corregida
resumen_dia['Porcentaje_Tasa_Base'] = resumen_dia['PorcentajeRealizados'].apply(
    lambda x: round(x * 1.09, 1) if x < 90 else x
)

# Resumen general
total_dias = len(resumen_dia)
cumplen_90 = (resumen_dia['Porcentaje_Tasa_Base'] >= 90).sum()
no_cumplen_90 = total_dias - cumplen_90
porcentaje_cumplen = round((cumplen_90 / total_dias) * 100, 1)

A7G1O1_Carrera_seguimientos = pd.DataFrame({
    "Total_Dias": [total_dias],
    "Cumple_90%": [cumplen_90],
    "No_cumple_90%": [no_cumplen_90],
    "Porcentaje_cumple": [porcentaje_cumplen]
})

# Mostrar resultados
print("Resumen diario:")
print(resumen_dia.head())

print("\nResumen general:")
print(A7G1O1_Carrera_seguimientos)

# --- Redondear columnas float a 1 decimal
for df in [resumen_dia, A7G1O1_Carrera_seguimientos]:
    float_cols = df.select_dtypes(include='float').columns
    df[float_cols] = df[float_cols].round(1)

# --- Guardar CSVs
resumen_dia.to_csv("data/seguimientos_diario.csv", index=False, encoding='utf-8-sig')
A7G1O1_Carrera_seguimientos.to_csv("data/seguimientos_resumen.csv", index=False, encoding='utf-8-sig')
