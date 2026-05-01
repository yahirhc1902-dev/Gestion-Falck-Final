import streamlit as st
import pandas as pd
import sqlite3

# --- 1. CONFIGURACIÓN Y ESTILOS ---
st.set_page_config(page_title="Falck Pro", layout="wide")

st.markdown("""
    <style>
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    .stApp { margin-top: -70px; }
    
    .cabecera-roja {
        background-color: #e20613;
        padding: 10px;
        border-radius: 8px;
        color: white;
        display: flex;
        align-items: center;
        justify-content: space-around;
        margin-bottom: 15px;
    }
    .titulo-mini { font-size: 18px !important; font-weight: bold; margin: 0; }
    .slogan-mini { font-size: 11px !important; font-style: italic; margin: 0; }

    .resultado-consulta {
        background-color: #262730;
        padding: 20px;
        border-radius: 12px;
        border-left: 8px solid #e20613;
        color: white !important;
        margin-top: 15px;
    }
    .res-nombre { font-size: 28px !important; font-weight: bold; color: white !important; }
    .res-detalle { font-size: 22px !important; color: white !important; }

    div.stButton > button {
        width: 100%;
        height: 42px !important;
    }
    </style>
    """, unsafe_allow_html=True)

# --- 2. FUNCIONES DE LIMPIEZA Y DB ---
def limpiar_pantalla():
    # Esta es la forma segura de borrar sin causar errores de SessionState
    st.session_state["campo_cedula"] = ""
    st.session_state.mostrar_resultado = False

def consultar(sql):
    with sqlite3.connect('transporte.db') as conn:
        return pd.read_sql_query(sql, conn)

# --- 3. GESTIÓN DE SESIÓN ---
if 'autenticado' not in st.session_state:
    st.session_state.autenticado = False
if 'mostrar_resultado' not in st.session_state:
    st.session_state.mostrar_resultado = False

# --- 4. ENCABEZADO ---
st.markdown(f"""
    <div class="cabecera-roja">
        <img src="https://upload.wikimedia.org/wikipedia/commons/e/e5/Falck_Logo.svg" width="70">
        <div style="text-align: center;">
            <p class="titulo-mini">SISTEMA DE GESTIÓN DE FLOTA</p>
            <p class="slogan-mini">CONDUCIENDO CON COMPROMISO Y SEGURIDAD</p>
        </div>
    </div>
    """, unsafe_allow_html=True)

# --- 5. NAVEGACIÓN (SIDEBAR) ---
st.sidebar.title("Menú Falck")

if not st.session_state.autenticado:
    menu_activo = "👤 Consulta"
    with st.sidebar.expander("🔑 Ingreso Supervisor"):
        clave = st.text_input("Contraseña", type="password")
        if st.button("Acceder"):
            if clave == "falck2026":
                st.session_state.autenticado = True
                st.rerun()
            else:
                st.error("Clave incorrecta")
else:
    menu_activo = st.sidebar.radio("Navegar a:", ["👤 Consulta", "📝 Registro", "🔄 Gestión", "📅 Programación"])
    if st.sidebar.button("🚪 Cerrar Sesión"):
        st.session_state.autenticado = False
        st.rerun()

# --- 6. CONTENIDO ---

if menu_activo == "👤 Consulta":
    st.markdown("### 📋 Consulta de Turno")
    
    # El campo de texto usa la clave 'campo_cedula'
    st.text_input("Número de Cédula:", key="campo_cedula", placeholder="Escribe aquí...")

    col1, col2 = st.columns(2)
    with col1:
        if st.button("🔍 CONSULTAR", type="primary"):
            if st.session_state.campo_cedula:
                st.session_state.mostrar_resultado = True
            else:
                st.warning("Ingresa una cédula")

    with col2:
        # Usamos on_click para llamar a la función de limpieza de forma segura
        st.button("🧹 LIMPIAR", on_click=limpiar_pantalla)

    # Lógica para mostrar resultados
    if st.session_state.mostrar_resultado and st.session_state.campo_cedula:
        try:
            cedula = st.session_state.campo_cedula
            res = consultar(f'SELECT c.nombre, v.placa, c.turno FROM conductores c LEFT JOIN vehiculos v ON c.vehiculo_asignado = v.placa WHERE c."id conductor" = "{cedula}"')
            if not res.empty:
                st.markdown(f"""
                    <div class="resultado-consulta">
                        <p class="res-nombre">Hola, {res.iloc[0,0]}</p>
                        <p class="res-detalle">Tu vehículo: <strong>{res.iloc[0,1] if res.iloc[0,1] else 'SIN ASIGNAR'}</strong></p>
                        <p class="res-detalle">Turno asignado: <strong>{res.iloc[0,2]}</strong></p>
                    </div>
                """, unsafe_allow_html=True)
            else:
                st.error("Cédula no encontrada.")
        except:
            st.error("Error en la consulta. Verifica los datos.")

elif menu_activo == "📝 Registro":
    st.header("📝 Módulo de Registro")
    st.info("Habilitado para supervisor en la barra lateral.")

# (Las demás pestañas siguen la misma lógica de menu_activo)
