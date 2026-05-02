 import streamlit as st
import pandas as pd
import sqlite3

# --- 1. CONFIGURACIÓN INICIAL ---
st.set_page_config(page_title="Falck Pro - Gestión", layout="wide", initial_sidebar_state="collapsed")

# CSS Limpio: Sin márgenes negativos para no ocultar la flecha del celular
st.markdown("""
    <style>
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    
    .cabecera-roja {
        background-color: #e20613;
        padding: 12px;
        border-radius: 8px;
        color: white;
        display: flex;
        align-items: center;
        justify-content: space-around;
        margin-bottom: 20px;
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
    .res-nombre { font-size: 28px !important; font-weight: bold; color: white !important; margin:0;}
    .res-detalle { font-size: 22px !important; color: white !important; margin: 5px 0;}

    /* Botones más robustos para uso táctil */
    div.stButton > button {
        width: 100%;
        height: 45px !important;
        font-weight: bold;
    }
    </style>
    """, unsafe_allow_html=True)

# --- 2. BASE DE DATOS (ESTRUCTURA CORREGIDA) ---
def preparar_sistema():
    conn = sqlite3.connect('transporte.db')
    cursor = conn.cursor()
    # Tablas con nombres de columnas seguros (sin espacios)
    cursor.execute('''CREATE TABLE IF NOT EXISTS vehiculos (
                        placa TEXT PRIMARY KEY, 
                        modelo TEXT, 
                        estado TEXT)''')
    cursor.execute('''CREATE TABLE IF NOT EXISTS conductores (
                        cedula TEXT PRIMARY KEY, 
                        nombre TEXT, 
                        turno TEXT, 
                        vehiculo_asignado TEXT)''')
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

# --- 3. FUNCIONES DE INTERFAZ ---
def limpiar_pantalla():
    st.session_state["campo_cedula"] = ""
    st.session_state.mostrar_resultado = False

# --- 4. GESTIÓN DE SESIÓN ---
if 'autenticado' not in st.session_state:
    st.session_state.autenticado = False
if 'mostrar_resultado' not in st.session_state:
    st.session_state.mostrar_resultado = False

# --- 5. ENCABEZADO VISUAL ---
st.markdown(f"""
    <div class="cabecera-roja">
        <img src="https://upload.wikimedia.org/wikipedia/commons/e/e5/Falck_Logo.svg" width="70">
        <div style="text-align: center;">
            <p class="titulo-mini">SISTEMA DE GESTIÓN DE FLOTA</p>
            <p class="slogan-mini">CONDUCIENDO CON COMPROMISO Y SEGURIDAD</p>
        </div>
    </div>
    """, unsafe_allow_html=True)

# --- 6. NAVEGACIÓN Y SEGURIDAD (BARRA LATERAL) ---
st.sidebar.title("Menú del Sistema")

# Filtro estricto: El conductor solo ve la consulta. El supervisor ve el resto si se loguea.
if not st.session_state.autenticado:
    menu_activo = "👤 Consulta"
    st.sidebar.info("Modo Conductor Activo")
    with st.sidebar.expander("🔑 Acceso Supervisor"):
        clave = st.text_input("Contraseña", type="password")
        if st.button("Ingresar"):
            if clave == "falck2026":
                st.session_state.autenticado = True
                st.rerun()
            else:
                st.error("Credenciales incorrectas")
else:
    st.sidebar.success("Supervisor Verificado")
    menu_activo = st.sidebar.radio("Módulos Administrativos:", ["👤 Consulta", "📝 Registro", "🔄 Gestión", "📅 Programación"])
    st.sidebar.divider()
    if st.sidebar.button("🚪 Cerrar Sesión Segura"):
        st.session_state.autenticado = False
        st.rerun()

# --- 7. MÓDULOS DE LA APLICACIÓN ---

if menu_activo == "👤 Consulta":
    st.markdown("### 📋 Consulta de Turno y Vehículo")
    
    st.text_input("Número de Cédula:", key="campo_cedula", placeholder="Digita tu cédula aquí...")

    c1, c2 = st.columns(2)
    with c1:
        if st.button("🔍 CONSULTAR", type="primary"):
            if st.session_state.campo_cedula.strip():
                st.session_state.mostrar_resultado = True
            else:
                st.warning("Por favor, ingresa un número de cédula.")
    with c2:
        st.button("🧹 LIMPIAR", on_click=limpiar_pantalla)

    if st.session_state.mostrar_resultado and st.session_state.campo_cedula:
        cedula_ingresada = st.session_state.campo_cedula.strip()
        try:
            # Consulta SQL segura y adaptada a la nueva estructura
            query = f"""
                SELECT c.nombre, v.placa, c.turno 
                FROM conductores c 
                LEFT JOIN vehiculos v ON c.vehiculo_asignado = v.placa 
                WHERE c.cedula = '{cedula_ingresada}'
            """
            res = consultar(query)
            
            if not res.empty:
                nombre_cond = res.iloc[0]['nombre']
                placa_veh = res.iloc[0]['placa'] if pd.notna(res.iloc[0]['placa']) else 'SIN ASIGNAR'
                turno_cond = res.iloc[0]['turno']
                
                st.markdown(f"""
                    <div class="resultado-consulta">
                        <p class="res-nombre">Hola, {nombre_cond}</p>
                        <p class="res-detalle">Vehículo: <strong>{placa_veh}</strong></p>
                        <p class="res-detalle">Turno asignado: <strong>{turno_cond}</strong></p>
                    </div>
                """, unsafe_allow_html=True)
            else:
                st.error("Cédula no encontrada en la base de datos.")
        except Exception as e:
            st.error(f"Error de conexión con la base de datos. Detalle: {e}")

elif menu_activo == "📝 Registro":
    st.header("📝 Registro de Personal y Flota")
    
    col_cond, col_veh = st.columns(2)
    
    with col_cond:
        st.subheader("👤 Nuevo Conductor")
        try:
            # Buscar vehículos que no estén asignados a nadie
            vehiculos_libres = consultar('''
                SELECT placa FROM vehiculos 
                WHERE placa NOT IN (SELECT vehiculo_asignado FROM conductores WHERE vehiculo_asignado IS NOT NULL AND vehiculo_asignado != '')
            ''')
            lista_placas = vehiculos_libres['placa'].tolist() if not vehiculos_libres.empty else ["Sin vehículos libres"]
        except:
            lista_placas = ["Base de datos vacía"]

        with st.form("form_conductor", clear_on_submit=True):
            cedula_nueva = st.text_input("Cédula")
            nombre_nuevo = st.text_input("Nombre Completo")
            turno_nuevo = st.selectbox("Turno Asignado", ["Mañana", "Tarde", "Noche"])
            placa_asignar = st.selectbox("Asignar Vehículo", lista_placas)
            
            if st.form_submit_button("Guardar Conductor"):
                if cedula_nueva and nombre_nuevo:
                    placa_final = placa_asignar if placa_asignar != "Sin vehículos libres" and placa_asignar != "Base de datos vacía" else None
                    try:
                        ejecutar('INSERT INTO conductores (cedula, nombre, turno, vehiculo_asignado) VALUES (?, ?, ?, ?)', 
                                 (cedula_nueva, nombre_nuevo, turno_nuevo, placa_final))
                        st.success(f"Conductor {nombre_nuevo} registrado con éxito.")
                    except sqlite3.IntegrityError:
                        st.error("Esta cédula ya está registrada.")
                else:
                    st.warning("La cédula y el nombre son obligatorios.")

    with col_veh:
        st.subheader("🚑 Nuevo Vehículo")
        with st.form("form_vehiculo", clear_on_submit=True):
            placa_nueva = st.text_input("Placa del Vehículo").upper()
            modelo_nuevo = st.text_input("Modelo / Marca")
            estado_nuevo = st.selectbox("Estado Inicial", ["Disponible", "En Ruta", "Mantenimiento"])
            
            if st.form_submit_button("Registrar Vehículo"):
                if placa_nueva:
                    try:
                        ejecutar('INSERT INTO vehiculos (placa, modelo, estado) VALUES (?, ?, ?)', 
                                 (placa_nueva, modelo_nuevo, estado_nuevo))
                        st.success(f"Vehículo {placa_nueva} registrado.")
                    except sqlite3.IntegrityError:
                        st.error("Esta placa ya existe en el sistema.")
                else:
                    st.warning("La placa es obligatoria.")

elif menu_activo == "🔄 Gestión":
    st.header("⚙️ Gestión y Estado de Flota")
    try:
        df_vehiculos = consultar("SELECT placa, modelo, estado FROM vehiculos")
        if not df_vehiculos.empty:
            st.dataframe(df_vehiculos, use_container_width=True, hide_index=True)
            
            st.divider()
            st.subheader("Actualizar Estado Rápido")
            with st.form("form_actualizar_estado"):
                placa_seleccionada = st.selectbox("Selecciona la placa:", df_vehiculos['placa'].tolist())
                nuevo_estado = st.selectbox("Selecciona el nuevo estado:", ["Disponible", "En Ruta", "Mantenimiento"])
                
                if st.form_submit_button("Actualizar"):
                    ejecutar('UPDATE vehiculos SET estado = ? WHERE placa = ?', (nuevo_estado, placa_seleccionada))
                    st.success(f"El estado de la unidad {placa_seleccionada} ha cambiado a {nuevo_estado}.")
                    st.rerun()
        else:
            st.info("Aún no hay vehículos registrados en el sistema para gestionar.")
    except Exception as e:
        st.error(f"Error al cargar la gestión: {e}")

elif menu_activo == "📅 Programación":
    st.header("📅 Vista General de Programación")
    try:
        # Consulta robusta para unir la información de ambas tablas
        query_general = '''
            SELECT 
                c.cedula as "Cédula", 
                c.nombre as "Conductor", 
                c.turno as "Turno", 
                IFNULL(v.placa, 'Sin Asignar') as "Vehículo", 
                IFNULL(v.estado, 'N/A') as "Estado Unidad"
            FROM conductores c
            LEFT JOIN vehiculos v ON c.vehiculo_asignado = v.placa
        '''
        datos_completos = consultar(query_general)
        
        if not datos_completos.empty:
            st.dataframe(datos_completos, use_container_width=True, hide_index=True)
        else:
            st.info("No hay conductores programados todavía. Ve a la pestaña 'Registro' para iniciar.")
    except Exception as e:
        st.error(f"No se pudo cargar la programación. Verifica la base de datos. Detalle: {e}")
