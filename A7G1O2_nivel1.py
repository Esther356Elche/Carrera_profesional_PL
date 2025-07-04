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

# Conexión a SQL Server
conn = pyodbc.connect(
*
)

# Consulta
query = """
SELECT 
  Id,
  FechaHCarta,
  Asunto,
  Nivel,
  Usuario,
  Direccion,
  Texto,
  Ubicacion,
  TiempoCierreMinutos,
  NovedadResumenLibre
FROM TM6000_Cartas
WHERE FechaHCarta IS NOT NULL
"""

df = pd.read_sql(query, conn)

# Convertir FechaHCarta a datetime
df['FechaHCarta'] = pd.to_datetime(df['FechaHCarta'], errors='coerce')

# Filtrar por fechas del archivo de configuración
df_filtrado = df[
    (df['FechaHCarta'] >= fecha_inicio) & (df['FechaHCarta'] <= fecha_fin)
].copy()

# Clasificación
df_filtrado['TiempoCierreNivel1'] = df_filtrado['TiempoCierreMinutos'].apply(
    lambda x: 'INFERIOR' if x < 1440 else 'SUPERIOR'
)

df_filtrado['Fecha'] = df_filtrado['FechaHCarta'].dt.date

# Detalle diario
resumen_dia = df_filtrado.groupby('Fecha').agg(
    Total=('Id', 'count'),
    Inferiores=('TiempoCierreNivel1', lambda x: (x == 'INFERIOR').sum())
).reset_index()

resumen_dia['PorcentajeInferiores'] = round(
    (resumen_dia['Inferiores'] / resumen_dia['Total']) * 100, 1
)

# Resumen general
total_dias = len(resumen_dia)
dias_cumplen_90 = (resumen_dia['PorcentajeInferiores'] >= 90).sum()
porcentaje_cumplen_90 = round((dias_cumplen_90 / total_dias) * 100, 1)

A7G1O2_CARRERA_NIVEL1 = pd.DataFrame({
    "TotalDias": [total_dias],
    "DiasCumplen90": [dias_cumplen_90],
    "PorcentajeDiasCumplen90": [porcentaje_cumplen_90]
})

# Mostrar resultados
print("Resumen Diario:")
print(resumen_dia.head())

print("\nResumen General:")
print(A7G1O2_CARRERA_NIVEL1)

# --- Redondear columnas float a 1 decimal
for df in [resumen_dia, A7G1O2_CARRERA_NIVEL1]:
    float_cols = df.select_dtypes(include='float').columns
    df[float_cols] = df[float_cols].round(1)

# --- Guardar CSVs
resumen_dia.to_csv("data/nivel1_diario.csv", index=False, encoding='utf-8-sig')
A7G1O2_CARRERA_NIVEL1.to_csv("data/nivel1_resumen.csv", index=False, encoding='utf-8-sig')
