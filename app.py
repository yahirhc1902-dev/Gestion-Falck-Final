import streamlit as st
import pandas as pd
import sqlite3

# --- 1. CONFIGURACIÓN Y ESTILOS (CSS) ---
st.set_page_config(page_title="Falck Sistema v3", layout="wide")

# Inyección de CSS para ocultar menús, limpiar la interfaz y dar formato
st.markdown("""
    <style>
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    .stApp { margin-top: -60px; }
    
    /* Encabezado Rojo Compacto */
    .cabecera-roja {
        background-color: #e20613;
        padding: 10px 20px;
        border-radius: 8px;
        color: white;
        display: flex;
        align-items: center;
        justify-content: space-between;
        margin-bottom: 15px;
    }
    .titulo-mini { font-size: 20px !important; font-weight: bold; margin: 0; padding: 0; }
    .slogan-mini { font-size: 12px !important; font-style: italic; margin: 0; padding: 0; }

    /* Estilo para la respuesta de Consulta (Grande y Blanca) */
    .resultado-consulta {
        background-color: #262730;
        padding: 30px;
        border-radius: 15px;
        border-left: 10px solid #e20613;
        color: white !important;
        margin-top: 20px;
    }
    .res-nombre { font-size: 32px !important; font-weight: bold; color: white !important; margin-bottom: 10px; }
    .res-detalle { font-size: 24px !important; color: white !important; }
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

# --- 3. ENCABEZADO (LOGO, TÍTULO, ESLOGAN) ---
st.markdown(f"""
    <div class="cabecera-roja">
        <img src="https://upload.wikimedia.org/wikipedia/commons/e/e5/Falck_Logo.svg" width="90">
        <div style="text-align: right;">
            <p class="titulo-mini">SISTEMA DE GESTIÓN DE FLOTA</p>
            <p class="slogan-mini">CONDUCIENDO CON COMPROMISO Y SEGURIDAD</p>
        </div>
    </div>
    """, unsafe_allow_html=True)

# --- 4. GESTIÓN DE SESIÓN (SUPERVISOR) ---
if 'autenticado' not in st.session_state:
    st.session_state.autenticado = False

st.sidebar.markdown("### Control de Acceso")

if not st.session_state.autenticado:
    with st.sidebar.expander("🔐 Ingreso Supervisor"):
        clave = st.text_input("Contraseña", type="password")
        if st.button("Acceder"):
            if clave == "falck2026":
                st.session_state.autenticado = True
                st.rerun()
            else:
                st.error("Clave incorrecta")
else:
    # Botón de salida para cerrar la interfaz del supervisor
    if st.sidebar.button("🚪 CERRAR SESIÓN", use_container_width=True):
        st.session_state.autenticado = False
        st.rerun()

# Navegación según el rol
if st.session_state.autenticado:
    menu = st.sidebar.radio("Menú:", ["👤 Consulta", "📝 Registro", "🔄 Gestión", "📅 Programación"])
else:
    menu = "👤 Consulta"
    st.sidebar.info("Modo Conductor (Solo Consulta)")

# --- 5. LÓGICA DE LAS PESTAÑAS ---

if menu == "👤 Consulta":
    st.markdown("### 📋 Buscador de Vehículo Asignado")
    cedula = st.number_input("Ingresa tu número de cédula:", step=1, value=None)
    
    if st.button("REALIZAR CONSULTA", type="primary"):
        if cedula:
            res = consultar(f'SELECT c.nombre, v.placa, c.turno FROM conductores c LEFT JOIN vehiculos v ON c.vehiculo_asignado = v.placa WHERE c."id conductor" = {cedula}')
            if not res.empty:
                nombre_c = res.iloc[0,0]
                placa_c = res.iloc[0,1] if res.iloc[0,1] else "SIN VEHÍCULO ASIGNADO"
                turno_c = res.iloc[0,2]
                
                # RESPUESTA LIMPIA: Letras blancas, fondo oscuro, tamaño grande
                st.markdown(f"""
                    <div class="resultado-consulta">
                        <p class="res-nombre">Hola, {nombre_c}</p>
                        <p class="res-detalle">Tu vehículo asignado es: <strong>{placa_c}</strong></p>
                        <p class="res-detalle">Tu turno es: <strong>{turno_c}</strong></p>
                    </div>
                """, unsafe_allow_html=True)
            else:
                st.error("Cédula no encontrada en la base de datos.")
        else:
            st.warning("Por favor, digita un número de cédula válido.")

elif menu == "📝 Registro":
    st.header("📝 Registro de Datos")
    c1, c2 = st.columns(2)
    with c1:
        st.subheader("Registrar Conductor")
        libres = consultar('SELECT placa FROM vehiculos WHERE placa NOT IN (SELECT vehiculo_asignado FROM conductores WHERE vehiculo_asignado IS NOT NULL)')
        with st.form("f_c", clear_on_submit=True):
            id_c = st.number_input("Cédula", step=1, value=None)
            nom_c = st.text_input("Nombre Completo")
            tur_c = st.selectbox("Turno", ["1", "2", "3"])
            pla_c = st.selectbox("Asignar Placa", libres.iloc[:,0] if not libres.empty else ["No hay vehículos"])
            if st.form_submit_button("Guardar Conductor"):
                if id_c and nom_c and pla_c != "No hay vehículos":
                    ejecutar('INSERT INTO conductores VALUES (?,?,?,?)', (id_c, nom_c, tur_c, pla_c))
                    st.success("Conductor registrado con éxito."); st.rerun()

    with c2:
        st.subheader("Registrar Vehículo")
        with st.form("f_v", clear_on_submit=True):
            placa = st.text_input("Placa").upper()
            modelo = st.text_input("Modelo/Año")
            est = st.selectbox("Estado", ["Disponible", "En Ruta", "Mantenimiento"])
            if st.form_submit_button("Registrar Vehículo"):
                if placa and modelo:
                    ejecutar('INSERT INTO vehiculos VALUES (?,?,?)', (placa, modelo, est))
                    st.success("Vehículo añadido."); st.rerun()

elif menu == "🔄 Gestión":
    st.header("⚙️ Gestión de Flota y Estados")
    df_v = consultar("SELECT * FROM vehiculos")
    if not df_v.empty:
        placa_sel = st.selectbox("Selecciona un vehículo para actualizar:", df_v['placa'])
        with st.form("ed_v"):
            nuevo_est = st.selectbox("Nuevo Estado:", ["Disponible", "En Ruta", "Mantenimiento"])
            if st.form_submit_button("Actualizar Estado"):
                ejecutar('UPDATE vehiculos SET estado = ? WHERE placa = ?', (nuevo_est, placa_sel))
                st.success("Estado actualizado."); st.rerun()
        
        st.divider()
        if st.button("❌ Eliminar Vehículo del Sistema", type="primary"):
            ejecutar('UPDATE conductores SET vehiculo_asignado = NULL WHERE vehiculo_asignado = ?', (placa_sel,))
            ejecutar('DELETE FROM vehiculos WHERE placa = ?', (placa_sel,))
            st.warning("Vehículo eliminado."); st.rerun()

elif menu == "📅 Programación":
    st.header("📅 Tabla General de Operaciones")
    res_prog = consultar('SELECT c.nombre as Conductor, c.turno as Turno, v.placa as Placa, v.estado as Estado FROM conductores c LEFT JOIN vehiculos v ON c.vehiculo_asignado = v.placa')
    st.dataframe(res_prog, use_container_width=True)
