import streamlit as st
import pandas as pd
import sqlite3

# --- 1. CONFIGURACIÓN Y ESTILOS (CSS) ---
st.set_page_config(page_title="Falck Pro - Gestión de Flota", layout="wide")

st.markdown("""
    <style>
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    .stApp { margin-top: -75px; }
    
    /* Cabecera Roja Compacta */
    .cabecera-roja {
        background-color: #e20613;
        padding: 10px 15px;
        border-radius: 8px;
        color: white;
        display: flex;
        align-items: center;
        justify-content: space-between;
        margin-bottom: 15px;
    }
    .titulo-mini { font-size: 18px !important; font-weight: bold; margin: 0; }
    .slogan-mini { font-size: 11px !important; font-style: italic; margin: 0; }

    /* Respuesta de Consulta (Grande y Blanca) */
    .resultado-consulta {
        background-color: #262730;
        padding: 20px;
        border-radius: 12px;
        border-left: 8px solid #e20613;
        color: white !important;
        margin-top: 15px;
    }
    .res-nombre { font-size: 28px !important; font-weight: bold; color: white !important; margin-bottom: 5px; }
    .res-detalle { font-size: 20px !important; color: white !important; margin: 5px 0; }

    /* Ajuste para botones pequeños en línea */
    div.stButton > button {
        height: 35px !important;
        padding-top: 0px !important;
        padding-bottom: 0px !important;
    }
    </style>
    """, unsafe_allow_html=True)

# --- 2. BASE DE DATOS ---
def preparar_sistema():
    conn = sqlite3.connect('transporte.db')
    cursor = conn.cursor()
    cursor.execute('CREATE TABLE IF NOT EXISTS vehiculos (placa TEXT PRIMARY KEY, modelo TEXT, estado TEXT)')
    cursor.execute('CREATE TABLE IF NOT EXISTS conductores ("id conductor" INTEGER PRIMARY KEY, nombre TEXT, turno TEXT, vehiculo_asignado TEXT)')
    conn.commit()
    conn.close()

preparar_sistema()

def consultar(sql):
    with sqlite3.connect('transporte.db') as conn:
        return pd.read_sql_query(sql, conn)

def ejecutar(sql, params=()):
    with sqlite3.connect('transporte.db') as conn:
        conn.cursor().execute(sql, params)
        conn.commit()

# --- 3. ENCABEZADO ---
# Usamos el logo proporcionado
logo_url = "https://upload.wikimedia.org/wikipedia/commons/e/e5/Falck_Logo.svg" 

st.markdown(f"""
    <div class="cabecera-roja">
        <img src="{logo_url}" width="70">
        <div style="text-align: right;">
            <p class="titulo-mini">SISTEMA DE GESTIÓN DE FLOTA</p>
            <p class="slogan-mini">CONDUCIENDO CON COMPROMISO Y SEGURIDAD</p>
        </div>
    </div>
    """, unsafe_allow_html=True)

# --- 4. CONTROL DE SESIÓN ---
if 'autenticado' not in st.session_state:
    st.session_state.autenticado = False
if 'consulta_realizada' not in st.session_state:
    st.session_state.consulta_realizada = False

# --- 5. LÓGICA DE NAVEGACIÓN ---
if st.session_state.autenticado:
    menu = st.sidebar.radio("Navegación:", ["👤 Consulta", "📝 Registro", "🔄 Gestión", "📅 Programación"])
    if st.sidebar.button("🚪 CERRAR SESIÓN"):
        st.session_state.autenticado = False
        st.rerun()
else:
    menu = "👤 Consulta"

# --- 6. CONTENIDO ---

if menu == "👤 Consulta":
    st.markdown("### 📋 Consulta de Asignación")
    
    # Campo de texto limpio (sin +/-)
    cedula_txt = st.text_input("Número de Cédula:", placeholder="Escribe aquí...", key="input_cedula")
    
    # Botones en la misma fila y más pequeños
    col_btn1, col_btn2, col_espacio = st.columns([1, 1, 2])
    
    with col_btn1:
        if st.button("🔍 CONSULTAR", type="primary", use_container_width=True):
            if cedula_txt.isdigit():
                st.session_state.consulta_realizada = True
            else:
                st.error("Ingresa solo números.")
                
    with col_btn2:
        if st.button("🧹 LIMPIAR", use_container_width=True):
            st.session_state.consulta_realizada = False
            st.rerun()

    # Mostrar resultado si se consultó
    if st.session_state.consulta_realizada and cedula_txt:
        res = consultar(f'SELECT c.nombre, v.placa, c.turno FROM conductores c LEFT JOIN vehiculos v ON c.vehiculo_asignado = v.placa WHERE c."id conductor" = {cedula_txt}')
        if not res.empty:
            st.markdown(f"""
                <div class="resultado-consulta">
                    <p class="res-nombre">Hola, {res.iloc[0,0]}</p>
                    <p class="res-detalle">Vehículo: <strong>{res.iloc[0,1] if res.iloc[0,1] else 'PENDIENTE'}</strong></p>
                    <p class="res-detalle">Turno: <strong>{res.iloc[0,2]}</strong></p>
                </div>
            """, unsafe_allow_html=True)
        else:
            st.error("Cédula no encontrada.")

    # Acceso Supervisor (Visible en móvil al final de la consulta)
    if not st.session_state.autenticado:
        st.divider()
        with st.expander("🔑 Acceso Administrativo"):
            clave = st.text_input("Contraseña de Supervisor", type="password")
            if st.button("Ingresar al Sistema"):
                if clave == "falck2026":
                    st.session_state.autenticado = True
                    st.rerun()
                else:
                    st.error("Clave incorrecta")

elif menu == "📝 Registro":
    st.header("📝 Registro de Personal y Vehículos")
    c1, c2 = st.columns(2)
    with c1:
        st.subheader("Registrar Conductor")
        with st.form("f_cond", clear_on_submit=True):
            id_c = st.text_input("Cédula")
            nom_c = st.text_input("Nombre")
            tur_c = st.selectbox("Turno", ["1", "2", "3"])
            if st.form_submit_button("Guardar"):
                if id_c and nom_c:
                    ejecutar('INSERT INTO conductores VALUES (?,?,?,NULL)', (id_c, nom_c, tur_c))
                    st.success("Guardado"); st.rerun()
    with c2:
        st.subheader("Registrar Vehículo")
        with st.form("f_veh", clear_on_submit=True):
            placa = st.text_input("Placa").upper()
            mod = st.text_input("Modelo")
            if st.form_submit_button("Registrar"):
                ejecutar('INSERT INTO vehiculos VALUES (?,?,"Disponible")', (placa, mod))
                st.success("Registrado"); st.rerun()

elif menu == "🔄 Gestión":
    st.header("⚙️ Gestión de Flota")
    # Lógica de asignación y edición aquí...
    st.info("Módulo administrativo activo.")

elif menu == "📅 Programación":
    st.header("📅 Tabla de Control")
    st.dataframe(consultar('SELECT * FROM conductores'), use_container_width=True)
