import streamlit as st
import pandas as pd
import sqlite3

# --- 1. CONFIGURACIÓN Y ESTILOS ---
st.set_page_config(page_title="Falck Pro - Gestión", layout="wide", initial_sidebar_state="collapsed")

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
    div.stButton > button { width: 100%; height: 45px !important; font-weight: bold; }
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

# --- 5. NAVEGACIÓN ---
st.sidebar.title("Menú del Sistema")

if not st.session_state.autenticado:
    menu_activo = "👤 Consulta"
    with st.sidebar.expander("🔑 Acceso Supervisor"):
        clave = st.text_input("Contraseña", type="password")
        if st.button("Ingresar"):
            if clave == "falck2026":
                st.session_state.autenticado = True
                st.rerun()
            else:
                st.error("Credenciales incorrectas")
else:
    menu_activo = st.sidebar.radio("Módulos:", ["👤 Consulta", "📝 Registro", "🔄 Gestión", "📅 Programación"])
    if st.sidebar.button("🚪 Cerrar Sesión"):
        st.session_state.autenticado = False
        st.rerun()

# --- 6. MÓDULOS ---

if menu_activo == "👤 Consulta":
    st.markdown("### 📋 Consulta de Turno")
    st.text_input("Número de Cédula:", key="campo_cedula")
    c1, c2 = st.columns(2)
    with c1:
        if st.button("🔍 CONSULTAR", type="primary"):
            st.session_state.mostrar_resultado = True
    with c2:
        if st.button("🧹 LIMPIAR"):
            st.session_state.campo_cedula = ""
            st.session_state.mostrar_resultado = False
            st.rerun()

    if st.session_state.mostrar_resultado and st.session_state.campo_cedula:
        res = consultar(f'SELECT c.nombre, v.placa, c.turno FROM conductores c LEFT JOIN vehiculos v ON c.vehiculo_asignado = v.placa WHERE c."id conductor" = "{st.session_state.campo_cedula}"')
        if not res.empty:
            st.markdown(f'<div class="resultado-consulta"><h2>Hola, {res.iloc[0,0]}</h2><p>Unidad: {res.iloc[0,1]}</p><p>Turno: {res.iloc[0,2]}</p></div>', unsafe_allow_html=True)
        else:
            st.error("Cédula no encontrada.")

elif menu_activo == "📝 Registro":
    st.header("📝 Registro de Datos")
    col_cond, col_veh = st.columns(2)
    with col_cond:
        st.subheader("👤 Nuevo Conductor")
        libres = consultar('SELECT placa FROM vehiculos WHERE placa NOT IN (SELECT vehiculo_asignado FROM conductores WHERE vehiculo_asignado IS NOT NULL)')
        lista_p = ["Sin asignar"] + libres['placa'].tolist() if not libres.empty else ["Sin asignar"]
        with st.form("f_cond", clear_on_submit=True):
            id_c = st.text_input("Cédula")
            nom_c = st.text_input("Nombre")
            tur_c = st.selectbox("Turno", ["1", "2", "3"])
            pla_c = st.selectbox("Vehículo", lista_p)
            if st.form_submit_button("Guardar"):
                if id_c and nom_c:
                    ejecutar('INSERT INTO conductores VALUES (?,?,?,?)', (id_c, nom_c, tur_c, (None if pla_c=="Sin asignar" else pla_c)))
                    st.success("Registrado"); st.rerun()

    with col_veh:
        st.subheader("🚑 Nuevo Vehículo")
        with st.form("f_veh", clear_on_submit=True):
            placa = st.text_input("Placa").upper()
            mod = st.text_input("Modelo")
            est = st.selectbox("Estado", ["Disponible", "En Ruta", "Mantenimiento"])
            if st.form_submit_button("Registrar"):
                if placa:
                    ejecutar('INSERT INTO vehiculos VALUES (?,?,?)', (placa, mod, est))
                    st.success("Vehículo registrado"); st.rerun()

elif menu_activo == "🔄 Gestión":
    st.header("⚙️ Gestión y Edición")
    t_cond, t_veh = st.tabs(["🧑‍✈️ Conductores", "🚑 Vehículos"])
    
    with t_cond:
        df_c = consultar('SELECT "id conductor" as Cédula, nombre as Nombre, turno as Turno, vehiculo_asignado as Vehículo FROM conductores')
        st.dataframe(df_c, use_container_width=True, hide_index=True)
        
        if not df_c.empty:
            col_ed1, col_ed2 = st.columns(2)
            with col_ed1:
                with st.expander("📝 EDITAR CONDUCTOR"):
                    sel_c = st.selectbox("Cédula a editar:", df_c['Cédula'].tolist())
                    datos_actuales = df_c[df_c['Cédula'] == sel_c].iloc[0]
                    
                    nuevo_nom = st.text_input("Corregir Nombre:", value=datos_actuales['Nombre'])
                    nuevo_tur = st.selectbox("Cambiar Turno:", ["1", "2", "3"], index=["1", "2", "3"].index(str(datos_actuales['Turno'])))
                    
                    # Para cambiar vehículo
                    libres = consultar('SELECT placa FROM vehiculos WHERE placa NOT IN (SELECT vehiculo_asignado FROM conductores WHERE vehiculo_asignado IS NOT NULL AND "id conductor" != ?)', (sel_c,))
                    lista_p = ["Sin asignar"] + libres['placa'].tolist()
                    
                    nuevo_veh = st.selectbox("Reasignar Vehículo:", lista_p)
                    
                    if st.button("Guardar Cambios"):
                        v_final = None if nuevo_veh == "Sin asignar" else nuevo_veh
                        ejecutar('UPDATE conductores SET nombre = ?, turno = ?, vehiculo_asignado = ? WHERE "id conductor" = ?', 
                                 (nuevo_nom, nuevo_tur, v_final, sel_c))
                        st.success("Datos actualizados"); st.rerun()
            
            with col_ed2:
                with st.expander("🗑️ ELIMINAR CONDUCTOR"):
                    borrar_c = st.selectbox("Cédula a borrar:", df_c['Cédula'].tolist())
                    if st.button("Confirmar Eliminación", type="primary"):
                        ejecutar('DELETE FROM conductores WHERE "id conductor" = ?', (borrar_c,))
                        st.rerun()

    with t_veh:
        df_v = consultar("SELECT placa as Placa, modelo as Modelo, estado as Estado FROM vehiculos")
        st.dataframe(df_v, use_container_width=True, hide_index=True)
        if not df_v.empty:
            with st.expander("🔄 ACTUALIZAR ESTADO / ELIMINAR"):
                sel_v = st.selectbox("Vehículo:", df_v['Placa'].tolist())
                n_est = st.selectbox("Estado:", ["Disponible", "En Ruta", "Mantenimiento"])
                c1, c2 = st.columns(2)
                with c1:
                    if st.button("Actualizar Estado"):
                        ejecutar('UPDATE vehiculos SET estado = ? WHERE placa = ?', (n_est, sel_v)); st.rerun()
                with c2:
                    if st.button("Eliminar Vehículo", type="primary"):
                        ejecutar('DELETE FROM vehiculos WHERE placa = ?', (sel_v)); st.rerun()

elif menu_activo == "📅 Programación":
    st.header("📅 Tabla General")
    datos = consultar('SELECT c."id conductor" as Cédula, c.nombre as Conductor, c.turno as Turno, IFNULL(v.placa, "Sin Asignar") as Vehículo, IFNULL(v.estado, "N/A") as Estado FROM conductores c LEFT JOIN vehiculos v ON c.vehiculo_asignado = v.placa')
    st.dataframe(datos, use_container_width=True, hide_index=True)
