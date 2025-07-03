import pandas as pd
import numpy as np
import re
import pyodbc
import json
from datetime import datetime

# --- Leer fechas desde config_fechas.json
with open("config_fechas.json", "r", encoding="utf-8") as f:
    config = json.load(f)

fecha_inicio = pd.to_datetime(config["fecha_inicio"])
fecha_fin = pd.to_datetime(config["fecha_fin"]) + pd.Timedelta(hours=23, minutes=59, seconds=59)

# Calcular fechas equivalentes de 2024 para comparación
fecha_inicio_2024 = fecha_inicio - pd.DateOffset(years=1)
fecha_fin_2024 = fecha_fin - pd.DateOffset(years=1)

# --- Conexión a la base de datos
conn_str = (
    "Driver={SQL Server};"
    "Server=172.26.178.12;"
    "Database=SE;"
    "Uid=ecandela356;"
    "Pwd=332@Alex356;"
    "Trusted_Connection=no;"
)
con = pyodbc.connect(conn_str)

# --- Consulta todos los registros
query = """
SELECT [IdCarta], [FechaCarta], [Asunto], [Direccion], [Usuario], [Origen],
       [Texto], [GMSn], [GMSo], [Etiqueta], [Ubicacion], [Asignados],
       [Implicados], [Carta], [Condicion], [Documento], [FechaNacimiento],
       [Identificado], [Denunciado], [Detenido], [Area], [Acta], [NovedadResumenLibre]
FROM [_VM6000_Cartas_Entidades_Esther]
WHERE FechaCarta >= ? AND FechaCarta <= ?
   OR FechaCarta >= ? AND FechaCarta <= ?
ORDER BY FechaCarta ASC
"""

# --- Leer datos del periodo actual y anterior
params = (fecha_inicio, fecha_fin, fecha_inicio_2024, fecha_fin_2024)
CARRERA_Entidades = pd.read_sql(query, con, params=params)

# --- Convertir fechas válidas
def convertir_fecha_segura(valor):
    try:
        return pd.to_datetime(valor, format='%d/%m/%Y %H:%M')
    except:
        return pd.NaT

CARRERA_Entidades['FechaCarta'] = CARRERA_Entidades['FechaCarta'].apply(convertir_fecha_segura)
CARRERA_Entidades = CARRERA_Entidades.dropna(subset=['FechaCarta'])

# --- Filtrar por palabras clave en Asunto
filtro = CARRERA_Entidades['Asunto'].str.contains(r"ruido|acto|sucie", flags=re.IGNORECASE, na=False)
CARRERA_Entidades_filtrado = CARRERA_Entidades[filtro].copy()

# --- Asignar Turno
def asignar_turno(hora):
    if "06:30:00" <= hora <= "14:15:00":
        return "Turno 1"
    elif "14:16:00" <= hora <= "22:15:00":
        return "Turno 2"
    elif "22:16:00" <= hora <= "23:59:59" or "00:00:00" <= hora <= "06:29:59":
        return "Turno 3"
    else:
        return "Sin turno"

CARRERA_Entidades_filtrado['Hora'] = CARRERA_Entidades_filtrado['FechaCarta'].dt.strftime('%H:%M:%S')
CARRERA_Entidades_filtrado['Turno'] = CARRERA_Entidades_filtrado['Hora'].apply(asignar_turno)
CARRERA_Entidades_filtrado['Año'] = CARRERA_Entidades_filtrado['FechaCarta'].dt.year

# --- Agrupar por Turno y Año
totalizador = CARRERA_Entidades_filtrado.groupby(['Turno', 'Año']).size().unstack(fill_value=0).reset_index()

# --- Añadir fila Total
fila_total = totalizador.drop(columns='Turno').sum().to_dict()
fila_total['Turno'] = 'Total'
totalizador = pd.concat([totalizador, pd.DataFrame([fila_total])], ignore_index=True)

# --- Variación porcentual si están ambos años
if 2024 in totalizador.columns and 2025 in totalizador.columns:
    totalizador['Variación (%)'] = np.where(
        totalizador[2024] == 0,
        np.nan,
        round(((totalizador[2025] - totalizador[2024]) / totalizador[2024]) * 100, 1)
    )

# --- Guardar resultados
A7G1O3_Carrera_Asunto_Entidades = totalizador

# --- Redondear columnas float a 1 decimal
float_cols = A7G1O3_Carrera_Asunto_Entidades.select_dtypes(include='float').columns
A7G1O3_Carrera_Asunto_Entidades[float_cols] = A7G1O3_Carrera_Asunto_Entidades[float_cols].round(1)

# --- Exportar
hoy = datetime.now().strftime('%Y%m%d')
A7G1O3_Carrera_Asunto_Entidades.to_csv(f"C:/EsriTrainig/Carrera_profesional/A7G1O3_Carrera_Asunto_Entidades_{hoy}.csv", index=False, encoding='utf-8-sig')
A7G1O3_Carrera_Asunto_Entidades.to_csv("data/asuntos_entidades.csv", index=False, encoding='utf-8-sig')
