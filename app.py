
import streamlit as st
import pandas as pd
import sqlite3

# 1. Función para crear la base de datos perfecta desde cero
def preparar_sistema():
    conn = sqlite3.connect('transporte.db')
    cursor = conn.cursor()
    # Tabla de vehículos
    cursor.execute('''CREATE TABLE IF NOT EXISTS vehiculos 
                     (placa TEXT PRIMARY KEY, modelo TEXT, estado TEXT)''')
    # Tabla de conductores
    cursor.execute('''CREATE TABLE IF NOT EXISTS conductores 
                     ("id conductor" INTEGER PRIMARY KEY, nombre TEXT, turno TEXT, vehiculo_asignado TEXT)''')
    conn.commit()
    conn.close()

# Ejecutamos la preparación
preparar_sistema()

# 2. Funciones de ayuda
def consultar(sql):
    with sqlite3.connect('transporte.db') as conn:
        return pd.read_sql_query(sql, conn)

def ejecutar(sql, params=()):
    with sqlite3.connect('transporte.db') as conn:
        conn.cursor().execute(sql, params)
        conn.commit()

# --- INTERFAZ ---
st.set_page_config(page_title="Falck Pro", layout="wide")
st.title("🚀 Sistema Falck - Versión Limpia")

t1, t2, t3, t4 = st.tabs(["📝 Registro", "🔄 Gestión", "📅 Programación", "👤 Consulta"])

with t1:
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
                        st.success("Guardado!"); st.rerun()
                    else: st.error("Cédula ya existe")

    with col2:
        st.subheader("🚛 Registro Vehículo")
        with st.form("f_veh", clear_on_submit=True):
            placa = st.text_input("Placa").strip().upper()
            modelo = st.text_input("Modelo")
            # AÑADIMOS 'En Ruta' A LAS OPCIONES:
            estado = st.selectbox("Estado Inicial", ["Disponible", "En Ruta", "Mantenimiento"])
            
            if st.form_submit_button("Registrar Vehículo"):
                if placa and modelo:
                    check = consultar(f"SELECT * FROM vehiculos WHERE placa = '{placa}'")
                    if check.empty:
                        ejecutar('INSERT INTO vehiculos VALUES (?,?,?)', (placa, modelo, estado))
                        st.success(f"Vehículo {placa} registrado con éxito.")
                        st.rerun()
                    else:
                        st.error("Esa placa ya existe en el sistema.")


with t2:
    st.subheader("⚙️ Centro de Control del Supervisor")
    
    # 1. Tablas de vista rápida
    df_c = consultar("SELECT * FROM conductores")
    df_v = consultar("SELECT * FROM vehiculos")
    
    col_vista1, col_vista2 = st.columns(2)
    with col_vista1:
        st.caption("Lista de Personal")
        st.dataframe(df_c, use_container_width=True)
    with col_vista2:
        st.caption("Estado de la Flota")
        st.dataframe(df_v, use_container_width=True)
    
    st.divider()

    # 2. Menú de edición inteligente
    accion = st.radio("¿Qué deseas hacer?", ["Editar Conductor", "Editar Vehículo"], horizontal=True)

    if accion == "Editar Conductor" and not df_c.empty:
        # Usamos iloc[0] para asegurar que traemos el ID
        id_sel = st.selectbox("Selecciona Cédula a Modificar:", df_c.iloc[:, 0])
        datos_c = df_c[df_c.iloc[:, 0] == id_sel].iloc[0]

        with st.form("edicion_c"):
            nuevo_nom = st.text_input("Nombre Actualizado", value=datos_c['nombre'])
            nuevo_tur = st.selectbox("Cambiar Turno", ["1", "2", "3"], index=["1", "2", "3"].index(datos_c['turno']))
            
            if st.form_submit_button("💾 Guardar Cambios en Conductor"):
                ejecutar('UPDATE conductores SET nombre = ?, turno = ? WHERE "id conductor" = ?', (nuevo_nom, nuevo_tur, id_sel))
                st.success("Datos actualizados correctamente.")
                st.rerun()

    if accion == "Editar Vehículo" and not df_v.empty:
        placa_sel = st.selectbox("Selecciona Placa a Modificar:", df_v.iloc[:, 0])
        datos_v = df_v[df_v.iloc[:, 0] == placa_sel].iloc[0]

        with st.form("edicion_v"):
            estados = ["Disponible", "En Ruta", "Mantenimiento"]
            nuevo_est = st.selectbox("Actualizar Estado", estados, index=estados.index(datos_v['estado']))
            
            col_b1, col_b2 = st.columns(2)
            if st.form_submit_button("💾 Actualizar Estado"):
                ejecutar('UPDATE vehiculos SET estado = ? WHERE placa = ?', (nuevo_est, placa_sel))
                st.success("Estado de vehículo actualizado.")
                st.rerun()
        
        # El botón de eliminar lo dejamos fuera del formulario de edición por seguridad
        if st.button("🗑️ Eliminar Vehículo de la Base de Datos", type="primary"):
            ejecutar('UPDATE conductores SET vehiculo_asignado = NULL WHERE vehiculo_asignado = ?', (placa_sel,))
            ejecutar('DELETE FROM vehiculos WHERE placa = ?', (placa_sel,))
            st.warning(f"Vehículo {placa_sel} eliminado.")
            st.rerun()


with t3:
    st.subheader("📅 Programación del Día")
    res = consultar('''SELECT c.nombre as Conductor, c.turno as Turno, v.placa as Placa, v.estado as Estado
                       FROM conductores c LEFT JOIN vehiculos v ON c.vehiculo_asignado = v.placa''')
    st.table(res)


# --- PESTAÑA 4: CONSULTA ---
with t4:
    st.subheader("👤 Portal del Conductor")
    cedula = st.number_input("Digita tu Cédula:", step=1, value=None)
    
    if st.button("Consultar Mi Vehículo"):
        if cedula:
            # Actualizamos la consulta para traer también el turno
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
                
                # Formato de respuesta solicitado
                st.success(f"Hola, {nombre_c}, como esta hasta el momento")
                
                st.info(f"""
                Su vehículo asignado será: **{placa_c}** Su turno asignado será: **{turno_c}**
                """)
            else:
                st.error("Cédula no encontrada en el sistema.")