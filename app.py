  
import streamlit as st
import pandas as pd
import sqlite3

# --- 1. CONFIGURACIÓN Y ESTILOS (CSS) ---
st.set_page_config(page_title="Falck Sistema v4", layout="wide")

# CSS Ajustado: Quitamos controles de número y mejoramos botones
st.markdown("""
    <style>
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    .stApp { margin-top: -70px; }
    
    /* Encabezado Rojo Compacto */
    .cabecera-roja {
        background-color: #e20613;
        padding: 8px 15px;
        border-radius: 8px;
        color: white;
        display: flex;
        align-items: center;
        justify-content: space-between;
        margin-bottom: 10px;
    }
    .titulo-mini { font-size: 18px !important; font-weight: bold; margin: 0; }
    .slogan-mini { font-size: 11px !important; font-style: italic; margin: 0; }

    /* Respuesta de Consulta Blanca y Grande */
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
    
    /* Quitar flechas de los campos numéricos (por si acaso) */
    input::-webkit-outer-spin-button, input::-webkit-inner-spin-button {
        -webkit-appearance: none; margin: 0;
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
# Intenta cargar tu logo desde GitHub. Si no existe, usa uno genérico.
try:
    url_logo = "logo_falck.png" # Si subes tu foto a GitHub con este nombre, se verá aquí.
except:
    url_logo = "https://upload.wikimedia.org/wikipedia/commons/e/e5/Falck_Logo.svg"

st.markdown(f"""
    <div class="cabecera-roja">
        <img src="{url_logo}" width="80">
        <div style="text-align: right;">
            <p class="titulo-mini">SISTEMA DE GESTIÓN DE FLOTA</p>
            <p class="slogan-mini">CONDUCIENDO CON COMPROMISO Y SEGURIDAD</p>
        </div>
    </div>
    """, unsafe_allow_html=True)

# --- 4. GESTIÓN DE SESIÓN (SUPERVISOR) ---
if 'autenticado' not in st.session_state:
    st.session_state.autenticado = False

st.sidebar.markdown("### Menú de Control")

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
    if st.sidebar.button("🚪 CERRAR SESIÓN", use_container_width=True):
        st.session_state.autenticado = False
        st.rerun()

# Navegación
if st.session_state.autenticado:
    menu = st.sidebar.radio("Ir a:", ["👤 Consulta", "📝 Registro", "🔄 Gestión", "📅 Programación"])
else:
    menu = "👤 Consulta"
    st.sidebar.info("Para ver el menú de supervisor, toca la flecha (>) arriba a la izquierda.")

# --- 5. LÓGICA DE LAS PESTAÑAS ---

if menu == "👤 Consulta":
    st.markdown("### 📋 Buscador de Vehículo")
    
    # Cambiamos number_input por text_input para quitar los símbolos + y -
    cedula_txt = st.text_input("Ingresa tu número de cédula:", placeholder="Solo números...")
    
    c_btn1, c_btn2 = st.columns([1, 1])
    
    with c_btn1:
        btn_consultar = st.button("🔍 CONSULTAR", type="primary", use_container_width=True)
    with c_btn2:
        btn_limpiar = st.button("🧹 LIMPIAR", use_container_width=True)

    if btn_limpiar:
        st.rerun()

    if btn_consultar:
        if cedula_txt:
            # Validamos que sea un número para evitar errores en la DB
            if cedula_txt.isdigit():
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
                    st.error("Cédula no registrada.")
            else:
                st.error("Por favor, ingresa solo números.")

elif menu == "📝 Registro":
    st.header("📝 Registro de Datos")
    c1, c2 = st.columns(2)
    with c1:
        st.subheader("Conductor")
        libres = consultar('SELECT placa FROM vehiculos WHERE placa NOT IN (SELECT vehiculo_asignado FROM conductores WHERE vehiculo_asignado IS NOT NULL)')
        with st.form("f_c", clear_on_submit=True):
            id_c = st.text_input("Cédula (Solo números)")
            nom_c = st.text_input("Nombre Completo")
            tur_c = st.selectbox("Turno", ["1", "2", "3"])
            pla_c = st.selectbox("Asignar Placa", libres.iloc[:,0] if not libres.empty else ["No hay vehículos"])
            if st.form_submit_button("Guardar"):
                if id_c.isdigit() and nom_c:
                    ejecutar('INSERT INTO conductores VALUES (?,?,?,?)', (id_c, nom_c, tur_c, pla_c))
                    st.success("Guardado"); st.rerun()

    with c2:
        st.subheader("Vehículo")
        with st.form("f_v", clear_on_submit=True):
            placa = st.text_input("Placa").upper()
            modelo = st.text_input("Modelo")
            est = st.selectbox("Estado", ["Disponible", "En Ruta", "Mantenimiento"])
            if st.form_submit_button("Registrar"):
                if placa and modelo:
                    ejecutar('INSERT INTO vehiculos VALUES (?,?,?)', (placa, modelo, est))
                    st.success("Registrado"); st.rerun()

elif menu == "🔄 Gestión":
    st.header("⚙️ Gestión de Flota")
    df_v = consultar("SELECT * FROM vehiculos")
    if not df_v.empty:
        placa_sel = st.selectbox("Selecciona vehículo:", df_v['placa'])
        with st.form("ed_v"):
            nuevo_est = st.selectbox("Nuevo Estado:", ["Disponible", "En Ruta", "Mantenimiento"])
            if st.form_submit_button("Actualizar"):
                ejecutar('UPDATE vehiculos SET estado = ? WHERE placa = ?', (nuevo_est, placa_sel))
                st.success("Actualizado"); st.rerun()

elif menu == "📅 Programación":
    st.header("📅 Tabla General")
    st.dataframe(consultar('SELECT c.nombre, c.turno, v.placa, v.estado FROM conductores c LEFT JOIN vehiculos v ON c.vehiculo_asignado = v.placa'), use_container_width=True)
