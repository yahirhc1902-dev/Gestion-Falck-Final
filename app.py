import streamlit as st
import pandas as pd
import sqlite3

# --- 1. CONFIGURACIÓN Y ESTILOS ---
st.set_page_config(page_title="Falck Pro", layout="wide", initial_sidebar_state="collapsed")

# CSS Corregido: ¡Ya NO ocultamos el header para que el celular muestre el botón > !
st.markdown("""
    <style>
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    .stApp { margin-top: -30px; }
    
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
    st.session_state["campo_cedula"] = ""
    st.session_state.mostrar_resultado = False

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

# --- 5. NAVEGACIÓN (SIDEBAR PARA SUPERVISOR) ---
st.sidebar.title("Menú Supervisor")

if not st.session_state.autenticado:
    menu_activo = "👤 Consulta"
    with st.sidebar.expander("🔑 Ingreso Seguro"):
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

# --- 6. CONTENIDO COMPLETO DE LAS PESTAÑAS ---

if menu_activo == "👤 Consulta":
    st.markdown("### 📋 Consulta de Turno")
    
    st.text_input("Número de Cédula:", key="campo_cedula", placeholder="Escribe aquí...")

    col1, col2 = st.columns(2)
    with col1:
        if st.button("🔍 CONSULTAR", type="primary"):
            if st.session_state.campo_cedula:
                st.session_state.mostrar_resultado = True
            else:
                st.warning("Ingresa una cédula")

    with col2:
        st.button("🧹 LIMPIAR", on_click=limpiar_pantalla)

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
            st.error("Error en la consulta.")

elif menu_activo == "📝 Registro":
    st.header("📝 Registro de Datos")
    c1, c2 = st.columns(2)
    with c1:
        st.subheader("Registrar Conductor")
        libres = consultar('SELECT placa FROM vehiculos WHERE placa NOT IN (SELECT vehiculo_asignado FROM conductores WHERE vehiculo_asignado IS NOT NULL)')
        with st.form("f_cond", clear_on_submit=True):
            id_c = st.text_input("Cédula (Solo números)")
            nom_c = st.text_input("Nombre Completo")
            tur_c = st.selectbox("Turno", ["1", "2", "3"])
            pla_c = st.selectbox("Asignar Placa", libres.iloc[:,0] if not libres.empty else ["No hay vehículos"])
            if st.form_submit_button("Guardar"):
                if id_c and nom_c:
                    ejecutar('INSERT INTO conductores VALUES (?,?,?,?)', (id_c, nom_c, tur_c, pla_c))
                    st.success("Guardado correctamente."); st.rerun()

    with c2:
        st.subheader("Registrar Vehículo")
        with st.form("f_veh", clear_on_submit=True):
            placa = st.text_input("Placa").upper()
            mod = st.text_input("Modelo")
            est = st.selectbox("Estado", ["Disponible", "En Ruta", "Mantenimiento"])
            if st.form_submit_button("Registrar"):
                if placa and mod:
                    ejecutar('INSERT INTO vehiculos VALUES (?,?,?)', (placa, mod, est))
                    st.success("Registrado correctamente."); st.rerun()

elif menu_activo == "🔄 Gestión":
    st.header("⚙️ Gestión de Flota")
    df_v = consultar("SELECT * FROM vehiculos")
    if not df_v.empty:
        placa_sel = st.selectbox("Selecciona vehículo a actualizar:", df_v['placa'])
        with st.form("ed_v"):
            nuevo_est = st.selectbox("Nuevo Estado:", ["Disponible", "En Ruta", "Mantenimiento"])
            if st.form_submit_button("Actualizar Estado"):
                ejecutar('UPDATE vehiculos SET estado = ? WHERE placa = ?', (nuevo_est, placa_sel))
                st.success(f"Estado de {placa_sel} actualizado."); st.rerun()
    else:
        st.info("No hay vehículos registrados aún.")

elif menu_activo == "📅 Programación":
    st.header("📅 Tabla General")
    datos = consultar('SELECT c.nombre, c.turno, v.placa, v.estado FROM conductores c LEFT JOIN vehiculos v ON c.vehiculo_asignado = v.placa')
    st.dataframe(datos, use_container_width=True)
