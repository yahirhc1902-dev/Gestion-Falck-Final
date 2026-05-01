import streamlit as st
import pandas as pd
import sqlite3

# --- 1. CONFIGURACIÓN Y ESTILOS (CSS) ---
st.set_page_config(page_title="Falck Pro", layout="wide")

# CSS para ocultar basura visual y dejar la interface limpia
st.markdown("""
    <style>
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    .stApp { margin-top: -70px; }
    
    /* Cabecera Roja Corporativa */
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

    /* Respuesta de Consulta Grande y Blanca */
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

    /* Botones en línea */
    div.stButton > button {
        width: 100%;
        height: 40px !important;
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

# --- 3. GESTIÓN DE ESTADOS (SESIÓN) ---
if 'autenticado' not in st.session_state:
    st.session_state.autenticado = False
if 'cedula_valor' not in st.session_state:
    st.session_state.cedula_valor = ""
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

# --- 5. BARRA LATERAL (EL SISTEMA QUE TE GUSTA) ---
st.sidebar.title("Menú Falck")

if not st.session_state.autenticado:
    with st.sidebar.expander("🔑 Ingreso Supervisor"):
        clave = st.text_input("Contraseña", type="password")
        if st.button("Entrar"):
            if clave == "falck2026":
                st.session_state.autenticado = True
                st.rerun()
            else:
                st.error("Incorrecta")
else:
    # Si el supervisor entra, ve todas las opciones en la izquierda
    opcion = st.sidebar.radio("Navegar a:", ["👤 Consulta", "📝 Registro", "🔄 Gestión", "📅 Programación"])
    if st.sidebar.button("🚪 Cerrar Sesión"):
        st.session_state.autenticado = False
        st.rerun()
    menu_activo = opcion
    st.sidebar.success("Modo Supervisor Activo")
else:
    menu_activo = "👤 Consulta"
    st.sidebar.info("Modo Conductor")

# --- 6. CONTENIDO ---

if menu_activo == "👤 Consulta":
    st.markdown("### 📋 Consulta de Turno")
    
    # Campo de cédula conectado al estado de sesión para poder borrarlo
    cedula_input = st.text_input("Número de Cédula:", value=st.session_state.cedula_valor, placeholder="Escribe aquí...")

    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("🔍 CONSULTAR", type="primary"):
            if cedula_input:
                st.session_state.cedula_valor = cedula_input
                st.session_state.mostrar_resultado = True
            else:
                st.warning("Escribe una cédula")

    with col2:
        if st.button("🧹 LIMPIAR"):
            st.session_state.cedula_valor = ""
            st.session_state.mostrar_resultado = False
            st.rerun()

    # Mostrar la respuesta grande y blanca
    if st.session_state.mostrar_resultado and st.session_state.cedula_valor:
        res = consultar(f'SELECT c.nombre, v.placa, c.turno FROM conductores c LEFT JOIN vehiculos v ON c.vehiculo_asignado = v.placa WHERE c."id conductor" = "{st.session_state.cedula_valor}"')
        if not res.empty:
            st.markdown(f"""
                <div class="resultado-consulta">
                    <p class="res-nombre">Hola, {res.iloc[0,0]}</p>
                    <p class="res-detalle">Vehículo: <strong>{res.iloc[0,1] if res.iloc[0,1] else 'PENDIENTE'}</strong></p>
                    <p class="res-detalle">Turno: <strong>{res.iloc[0,2]}</strong></p>
                </div>
            """, unsafe_allow_html=True)
        else:
            st.error("Cédula no registrada.")

elif menu_activo == "📝 Registro":
    st.header("📝 Registro de Personal")
    # (Aquí va tu código de formularios de registro que ya teníamos)
    st.write("Módulo de registro habilitado para supervisor.")

# ... (El resto de pestañas se mantienen igual bajo la lógica de menu_activo)
