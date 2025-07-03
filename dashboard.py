import streamlit as st
import pandas as pd
import json
from datetime import datetime

st.set_page_config(layout="wide", page_title="Cuadro de mando - Indicadores")

# --- Estilos personalizados
st.markdown(
    """
    <style>
    .main {
        background-color: #2d2d2d;
    }

    div[data-testid="stSidebar"] {
        background-color: #1f1f1f;
    }

    .stDataFrame div {
        color: white !important;
        text-align: center !important;
    }

    .stDataFrame th {
        background-color: #3a3a3a !important;
        color: white !important;
        text-align: center !important;
    }

    .stDataFrame td {
        background-color: #3a3a3a !important;
        color: white !important;
        text-align: center !important;
    }

    .css-1kbsu7v {
        text-align: center !important;
    }
    </style>
    """,
    unsafe_allow_html=True
)

# --- Leer fechas del archivo JSON
with open("config_fechas.json", "r", encoding="utf-8") as f:
    config = json.load(f)

# --- Sidebar para seleccionar fechas
st.sidebar.title("🗓️ Configurar intervalo de fechas")
fecha_inicio = st.sidebar.date_input("Fecha inicio", datetime.strptime(config["fecha_inicio"], "%Y-%m-%d"))
fecha_fin = st.sidebar.date_input("Fecha fin", datetime.strptime(config["fecha_fin"], "%Y-%m-%d"))

# --- Actualizar JSON si cambian las fechas
config["fecha_inicio"] = fecha_inicio.strftime("%Y-%m-%d")
config["fecha_fin"] = fecha_fin.strftime("%Y-%m-%d")
with open("config_fechas.json", "w", encoding="utf-8") as f:
    json.dump(config, f, indent=2)

# --- Cabecera
st.title("INDICADORES CARRERA PROFESIONAL")
st.markdown(f"### Intervalo analizado: **{fecha_inicio.strftime('%d/%m/%Y')}** a **{fecha_fin.strftime('%d/%m/%Y')}**")

# --- Cargar y redondear columnas tipo float a 1 decimal
def cargar_csv_redondeado(path):
    df = pd.read_csv(path, encoding="utf-8-sig")
    float_cols = df.select_dtypes(include='float').columns
    df[float_cols] = df[float_cols].round(1)
    return df

seguimientos_diario = cargar_csv_redondeado("data/seguimientos_diario.csv")
seguimientos_resumen = cargar_csv_redondeado("data/seguimientos_resumen.csv")
nivel1_diario = cargar_csv_redondeado("data/nivel1_diario.csv")
nivel1_resumen = cargar_csv_redondeado("data/nivel1_resumen.csv")
asuntos_entidades = cargar_csv_redondeado("data/asuntos_entidades.csv")

# --- Tabs
tab1, tab2, tab3 = st.tabs(["A7G1O1_Seguimientos", "A7G1O2_nivel1", "A7G1O3_Asunto_Entidades"])

with tab1:
    st.subheader("A7G1O1 - Seguimientos")
    st.markdown("El indicador calcula el porcentaje de días en los que los asuntos de este nivel se resuelven en menos de 24 horas.")
    st.dataframe(seguimientos_diario, use_container_width=True)
    st.markdown("**El estándar establecido es del 90%:**")
    st.dataframe(seguimientos_resumen, use_container_width=True)

with tab2:
    st.subheader("A7G1O2 - Tiempo cierre Nivel 1")
    st.markdown("El objetivo es alcanzar la tasa base de vigilancias relacionadas con los seguimientos activos.")
    st.dataframe(nivel1_diario, use_container_width=True)
    st.markdown("**El estándar establecido es del 90%:**")
    st.dataframe(nivel1_resumen, use_container_width=True)

with tab3:
    st.subheader("A7G1O3 - Asuntos por turno")
    st.markdown("El objetivo es incrementar en un 5% las identificaciones de asuntos relacionados con ruidos y comportamientos incívicos en la vía pública, especialmente en horario nocturno.")
    st.dataframe(asuntos_entidades, use_container_width=True)
