import streamlit as st
import pandas as pd
import sqlite3

# --- 1. CONFIGURACIÓN Y ESTILOS (CSS) ---
st.set_page_config(page_title="Falck Pro - Gestión", layout="wide")

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

# --- 5. NAVEGACIÓN (SIDEBAR CORRECTA) ---
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
    # Si es supervisor, ve todas las pestañas
    menu_activo = st.sidebar.radio("Navegar a:", ["👤 Consulta", "📝 Registro", "🔄 Gestión", "📅 Programación"])
    if st.sidebar.button("🚪 Cerrar Sesión"):
        st.session_state.autenticado = False
        st.rerun()

# --- 6. CONTENIDO ---

if menu_activo == "👤 Consulta":
    st.markdown("### 📋 Consulta de Turno")
    
    # Usamos key="campo_cedula" para poder resetearlo
    cedula_input = st.text_input("Número de Cédula:", key="campo_cedula", placeholder="Escribe tu cédula aquí...")

    col1, col2 = st.columns(2)
    with col1:
        if st.button("🔍 CONSULTAR", type="primary"):
            if st.session_state.campo_cedula:
                st.session_state.mostrar_resultado = True
            else:
                st.warning("Por favor, ingresa una cédula.")

    with col2:
        if st.button("🧹 LIMPIAR"):
            # RESETEO TOTAL: Borra el texto y oculta el cuadro gris
            st.session_state.campo_cedula = ""
            st.session_state.mostrar_resultado = False
            st.rerun()

    if st.session_state.mostrar_resultado and st.session_state.campo_cedula:
        res = consultar(f'SELECT c.nombre, v.placa, c.turno FROM conductores c LEFT JOIN vehiculos v ON c.vehiculo_asignado = v.placa WHERE c."id conductor" = "{st.session_state.campo_cedula}"')
        if not res.empty:
            st.markdown(f"""
                <div class="resultado-consulta">
                    <p class="res-nombre">Hola, {res.iloc[0,0]}</p>
                    <p class="res-detalle">Tu vehículo: <strong>{res.iloc[0,1] if res.iloc[0,1] else 'SIN ASIGNAR'}</strong></p>
                    <p class="res-detalle">Turno asignado: <strong>{res.iloc[0,2]}</strong></p>
                </div>
            """, unsafe_allow_html=True)
        else:
            st.error("La cédula ingresada no se encuentra en la base de datos.")

elif menu_activo == "📝 Registro":
    st.header("📝 Registro de Datos")
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
                    st.success("Conductor guardado."); st.rerun()
    with c2:
        st.subheader("Registrar Vehículo")
        with st.form("f_veh", clear_on_submit=True):
            placa = st.text_input("Placa").upper()
            mod = st.text_input("Modelo")
            if st.form_submit_button("Registrar"):
                ejecutar('INSERT INTO vehiculos VALUES (?,?,"Disponible")', (placa, mod))
                st.success("Vehículo registrado."); st.rerun()

elif menu_activo == "🔄 Gestión":
    st.header("⚙️ Gestión de Flota")
    # Muestra los datos actuales
    df_v = consultar("SELECT * FROM vehiculos")
    st.dataframe(df_v, use_container_width=True)
    st.info("Aquí puedes actualizar estados en la siguiente fase.")

elif menu_activo == "📅 Programación":
    st.header("📅 Programación General")
    datos = consultar('SELECT c.nombre, c.turno, v.placa, v.estado FROM conductores c LEFT JOIN vehiculos v ON c.vehiculo_asignado = v.placa')
    st.table(datos)
