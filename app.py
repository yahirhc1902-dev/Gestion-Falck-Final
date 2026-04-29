
import streamlit as st
import pandas as pd
import sqlite3

# --- 1. CONFIGURACIÓN Y BASE DE DATOS ---
st.set_page_config(page_title="Sistema Falck Pro", layout="wide")

def preparar_sistema():
    conn = sqlite3.connect('transporte.db')
    cursor = conn.cursor()
    cursor.execute('''CREATE TABLE IF NOT EXISTS vehiculos 
                     (placa TEXT PRIMARY KEY, modelo TEXT, estado TEXT)''')
    cursor.execute('''CREATE TABLE IF NOT EXISTS conductores 
                     ("id conductor" INTEGER PRIMARY KEY, nombre TEXT, turno TEXT, vehiculo_asignado TEXT)''')
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

# --- 2. ENCABEZADO (LOGO Y ESLOGAN) ---
col_logo, col_titulo = st.columns([1, 4])

with col_logo:
    # Logo oficial de Falck desde Wikipedia (puedes cambiar la URL si tienes otra)
    st.image("https://upload.wikimedia.org/wikipedia/commons/e/e5/Falck_Logo.svg", width=160)

with col_titulo:
    st.title("Sistema de Gestión de Flota")
    st.markdown("### *CONDUCIENDO CON COMPROMISO Y SEGURIDAD*")

st.divider()

# --- 3. SEGURIDAD Y NAVEGACIÓN (BARRA LATERAL) ---
st.sidebar.title("Acceso al Sistema")
acceso_supervisor = False

# Expander "escondido" para el supervisor en la parte inferior de la barra lateral
with st.sidebar.expander("🔐 Acceso Supervisor"):
    clave = st.text_input("Contraseña", type="password")
    if clave == "falck2026": # Puedes cambiar esta clave
        acceso_supervisor = True
        st.success("Modo Supervisor Activo")
    elif clave != "":
        st.error("Clave incorrecta")

# Lógica de navegación
if acceso_supervisor:
    menu = st.sidebar.radio("Seleccione Panel:", 
                             ["👤 Consulta de Conductor", "📝 Registro", "🔄 Gestión de Flota", "📅 Programación"])
else:
    menu = "👤 Consulta de Conductor"
    st.sidebar.info("Modo Consulta Activo")

# --- 4. CONTENIDO DE LAS PESTAÑAS ---

# --- OPCIÓN: CONSULTA (LA CARA PÚBLICA) ---
if menu == "👤 Consulta de Conductor":
    st.header("👤 Portal del Conductor")
    cedula = st.number_input("Digita tu Cédula para consultar:", step=1, value=None)
    
    if st.button("Consultar Mi Vehículo"):
        if cedula:
            res = consultar(f'''
                SELECT c.nombre, v.placa, c.turno 
                FROM conductores c 
                LEFT JOIN vehiculos v ON c.vehiculo_asignado = v.placa 
                WHERE c."id conductor" = {cedula}
            ''')
            
            if not res.empty:
                nombre_c = res.iloc[0,0]
                placa_c = res.iloc[0,1] if res.iloc[0,1] else "Pendiente de asignación"
                turno_c = res.iloc[0,2]
                
                st.success(f"Hola, {nombre_c}, bienvenido al sistema.")
                st.info(f"""
                **Su vehículo asignado es:** {placa_c}  
                **Su turno asignado es:** {turno_c}
                """)
            else:
                st.error("Cédula no encontrada. Por favor contacte al supervisor.")

# --- OPCIÓN: REGISTRO (SOLO SUPERVISOR) ---
elif menu == "📝 Registro":
    st.header("📝 Registro de Personal y Equipos")
    col1, col2 = st.columns(2)
    with col1:
        st.subheader("👤 Registro Conductor")
        libres = consultar('SELECT placa FROM vehiculos WHERE placa NOT IN (SELECT vehiculo_asignado FROM conductores WHERE vehiculo_asignado IS NOT NULL)')
        with st.form("f_cond", clear_on_submit=True):
            id_c = st.number_input("Cédula", step=1, value=None)
            nom_c = st.text_input("Nombre")
            tur_c = st.selectbox("Turno", ["1", "2", "3"])
            pla_c = st.selectbox("Placa", libres.iloc[:,0] if not libres.empty else ["No hay vehículos"])
            if st.form_submit_button("Guardar Conductor"):
                if id_c and nom_c and pla_c != "No hay vehículos":
                    check = consultar(f'SELECT * FROM conductores WHERE "id conductor" = {id_c}')
                    if check.empty:
                        ejecutar('INSERT INTO conductores VALUES (?,?,?,?)', (id_c, nom_c, tur_c, pla_c))
                        st.success("¡Conductor guardado!"); st.rerun()
                    else: st.error("La cédula ya existe.")

    with col2:
        st.subheader("🚛 Registro Vehículo")
        with st.form("f_veh", clear_on_submit=True):
            placa = st.text_input("Placa").strip().upper()
            modelo = st.text_input("Modelo")
            estado = st.selectbox("Estado Inicial", ["Disponible", "En Ruta", "Mantenimiento"])
            if st.form_submit_button("Registrar Vehículo"):
                if placa and modelo:
                    check = consultar(f"SELECT * FROM vehiculos WHERE placa = '{placa}'")
                    if check.empty:
                        ejecutar('INSERT INTO vehiculos VALUES (?,?,?)', (placa, modelo, estado))
                        st.success(f"Vehículo {placa} registrado.")
                        st.rerun()
                    else: st.error("Esa placa ya existe.")

# --- OPCIÓN: GESTIÓN (SOLO SUPERVISOR) ---
elif menu == "🔄 Gestión de Flota":
    st.header("⚙️ Centro de Control de Supervisor")
    df_c = consultar("SELECT * FROM conductores")
    df_v = consultar("SELECT * FROM vehiculos")
    
    col_v1, col_v2 = st.columns(2)
    with col_v1:
        st.caption("Personal Registrado")
        st.dataframe(df_c, use_container_width=True)
    with col_v2:
        st.caption("Estado de Vehículos")
        st.dataframe(df_v, use_container_width=True)

    st.divider()
    accion = st.radio("Acción de edición:", ["Editar Conductor", "Editar Vehículo"], horizontal=True)

    if accion == "Editar Conductor" and not df_c.empty:
        id_sel = st.selectbox("Cédula a modificar:", df_c.iloc[:, 0])
        datos_c = df_c[df_c.iloc[:, 0] == id_sel].iloc[0]
        with st.form("edicion_c"):
            nuevo_nom = st.text_input("Nombre", value=datos_c['nombre'])
            nuevo_tur = st.selectbox("Turno", ["1", "2", "3"], index=["1", "2", "3"].index(datos_c['turno']))
            if st.form_submit_button("💾 Guardar"):
                ejecutar('UPDATE conductores SET nombre = ?, turno = ? WHERE "id conductor" = ?', (nuevo_nom, nuevo_tur, id_sel))
                st.success("Cambios guardados."); st.rerun()

    if accion == "Editar Vehículo" and not df_v.empty:
        placa_sel = st.selectbox("Placa a modificar:", df_v.iloc[:, 0])
        datos_v = df_v[df_v.iloc[:, 0] == placa_sel].iloc[0]
        with st.form("edicion_v"):
            estados = ["Disponible", "En Ruta", "Mantenimiento"]
            nuevo_est = st.selectbox("Estado", estados, index=estados.index(datos_v['estado']))
            if st.form_submit_button("💾 Actualizar"):
                ejecutar('UPDATE vehiculos SET estado = ? WHERE placa = ?', (nuevo_est, placa_sel))
                st.success("Estado actualizado."); st.rerun()
        
        if st.button("🗑️ Eliminar Vehículo permanentemente", type="primary"):
            ejecutar('UPDATE conductores SET vehiculo_asignado = NULL WHERE vehiculo_asignado = ?', (placa_sel,))
            ejecutar('DELETE FROM vehiculos WHERE placa = ?', (placa_sel,))
            st.warning(f"Vehículo {placa_sel} eliminado."); st.rerun()

# --- OPCIÓN: PROGRAMACIÓN (SOLO SUPERVISOR) ---
elif menu == "📅 Programación":
    st.header("📅 Programación de Turnos Actual")
    res = consultar('''SELECT c.nombre as Conductor, c.turno as Turno, v.placa as Placa, v.estado as Estado
                       FROM conductores c LEFT JOIN vehiculos v ON c.vehiculo_asignado = v.placa''')
    st.table(res)
