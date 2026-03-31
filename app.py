import streamlit as st
import pandas as pd
from datetime import date, datetime
import os

# Configuración de la página
st.set_page_config(page_title="Gastos del Hogar", page_icon="💰")
st.title("💰 Gastos del Hogar")

# Autenticación simple (Gmail si está disponible en el entorno Streamlit Cloud)
st.subheader("🔐 Usuario")
user_email = ""
if hasattr(st, "experimental_user"):
    user = st.experimental_user
    if user is not None and user.get("email"):
        user_email = user.get("email")
        st.success(f"Conectado como {user_email}")
    else:
        user_email = st.text_input("Ingresá tu correo de Gmail", "")
else:
    user_email = st.text_input("Ingresá tu correo de Gmail", "")

if not user_email:
    st.warning("Ingresá un usuario (email) para registrar quién crea y edita los gastos.")
    st.stop()

# Archivo donde se guardan los gastos
ARCHIVO = "gastos.csv"

# Crear o cargar el DataFrame
if os.path.exists(ARCHIVO):
    df = pd.read_csv(ARCHIVO)
else:
    df = pd.DataFrame(columns=["Fecha", "Descripcion", "Monto", "Persona", "Categoria", "CreadoPor", "CreadoEn", "ModificadoPor", "ModificadoEn"])

# Asegurar que existan las columnas de auditoría
for col in ["CreadoPor", "CreadoEn", "ModificadoPor", "ModificadoEn"]:
    if col not in df.columns:
        df[col] = ""

# Formulario para cargar un gasto
st.subheader("Cargar nuevo gasto")
col1, col2 = st.columns(2)

with col1:
    fecha = st.date_input("Fecha", value=date.today())
    monto = st.number_input("Monto ($)", min_value=0.0, step=100.0)
    persona = st.selectbox("¿Quién pagó?", ["Yo", "Mi pareja"])

with col2:
    descripcion = st.text_input("Descripción")
    categoria = st.selectbox("Categoría", ["Comida", "Transporte", "Servicios", "Salud", "Entretenimiento", "Otro"])

if st.button("Agregar gasto"):
    if not descripcion.strip() or monto <= 0:
        st.error("Completá descripción y monto válido para guardar el gasto.")
    else:
        ahora = datetime.now().isoformat(sep=" ", timespec="seconds")
        nuevo = pd.DataFrame([[fecha, descripcion, monto, persona, categoria, user_email, ahora, user_email, ahora]],
                             columns=["Fecha", "Descripcion", "Monto", "Persona", "Categoria", "CreadoPor", "CreadoEn", "ModificadoPor", "ModificadoEn"])
        df = pd.concat([df, nuevo], ignore_index=True)
        df.to_csv(ARCHIVO, index=False)
        st.success("✅ Gasto agregado con auditoría!")

# Mostrar historial con auditoría
st.subheader("Historial de gastos")

# Filtro de gastos
st.markdown("**Filtrar gastos**")
with st.expander("Opciones de filtro", expanded=True):
    persona_filter = st.selectbox("Persona", options=["Todos", "Yo", "Mi pareja"], index=0)
    categoria_filter = st.selectbox("Categoría", options=["Todas", "Comida", "Transporte", "Servicios", "Salud", "Entretenimiento", "Otro"], index=0)
    tex_filter = st.text_input("Texto en descripción")
    colf1, colf2 = st.columns(2)
    with colf1:
        desde = st.date_input("Desde", value=df["Fecha"].min() if not df.empty else date.today())
    with colf2:
        hasta = st.date_input("Hasta", value=df["Fecha"].max() if not df.empty else date.today())

    df_filtrado = df.copy()
    if persona_filter != "Todos":
        df_filtrado = df_filtrado[df_filtrado["Persona"] == persona_filter]
    if categoria_filter != "Todas":
        df_filtrado = df_filtrado[df_filtrado["Categoria"] == categoria_filter]
    if tex_filter.strip():
        df_filtrado = df_filtrado[df_filtrado["Descripcion"].str.contains(tex_filter.strip(), case=False, na=False)]
    if not df_filtrado.empty:
        df_filtrado["Fecha"] = pd.to_datetime(df_filtrado["Fecha"], errors="coerce")
        df_filtrado = df_filtrado[(df_filtrado["Fecha"] >= pd.to_datetime(desde)) & (df_filtrado["Fecha"] <= pd.to_datetime(hasta))]

    st.dataframe(df_filtrado, use_container_width=True)

# Edición y borrado de gastos
st.subheader("✏️ Gestionar un gasto")
if not df.empty:
    idx = st.selectbox("Seleccionar fila", df.index, format_func=lambda i: f"{i} - {df.loc[i, 'Descripcion']} (${df.loc[i, 'Monto']})")
    if idx is not None:
        with st.form(key="edit_form"):
            fecha_e = st.date_input("Fecha", value=pd.to_datetime(df.loc[idx, "Fecha"]).date() if pd.notna(df.loc[idx, "Fecha"]) else date.today())
            descripcion_e = st.text_input("Descripción", value=str(df.loc[idx, "Descripcion"]))
            monto_e = st.number_input("Monto ($)", min_value=0.0, value=float(df.loc[idx, "Monto"]), step=100.0)
            persona_e = st.selectbox("¿Quién pagó?", ["Yo", "Mi pareja"], index=0 if df.loc[idx, "Persona"] == "Yo" else 1)
            categoria_e = st.selectbox("Categoría", ["Comida", "Transporte", "Servicios", "Salud", "Entretenimiento", "Otro"], index=["Comida", "Transporte", "Servicios", "Salud", "Entretenimiento", "Otro"].index(df.loc[idx, "Categoria"]) if df.loc[idx, "Categoria"] in ["Comida", "Transporte", "Servicios", "Salud", "Entretenimiento", "Otro"] else 0)
            col_btn1, col_btn2 = st.columns(2)
            submitted = col_btn1.form_submit_button("Guardar cambios")
            borrar = col_btn2.form_submit_button("Eliminar gasto", help="Borra el gasto seleccionado")

            if submitted:
                df.loc[idx, "Fecha"] = fecha_e
                df.loc[idx, "Descripcion"] = descripcion_e
                df.loc[idx, "Monto"] = monto_e
                df.loc[idx, "Persona"] = persona_e
                df.loc[idx, "Categoria"] = categoria_e
                df.loc[idx, "ModificadoPor"] = user_email
                df.loc[idx, "ModificadoEn"] = datetime.now().isoformat(sep=" ", timespec="seconds")
                df.to_csv(ARCHIVO, index=False)
                st.success("✅ Gasto actualizado y auditoría guardada")
            if borrar:
                df = df.drop(idx).reset_index(drop=True)
                df.to_csv(ARCHIVO, index=False)
                st.success("🗑️ Gasto eliminado")

# Resumen
if not df.empty:
    st.subheader("Resumen")
    df["Monto"] = pd.to_numeric(df["Monto"], errors="coerce").fillna(0)
    resumen = df.groupby("Persona")["Monto"].sum().reset_index()
    st.bar_chart(resumen.set_index("Persona"))
    
    total_yo = df[df["Persona"] == "Yo"]["Monto"].sum()
    total_pareja = df[df["Persona"] == "Mi pareja"]["Monto"].sum()
    diferencia = abs(total_yo - total_pareja)
    
    if total_yo > total_pareja:
        st.info(f"💡 Tu pareja te debe ${diferencia:.2f}")
    elif total_pareja > total_yo:
        st.info(f"💡 Vos le debés ${diferencia:.2f} a tu pareja")
    else:
        st.success("✅ ¡Están a mano!")
