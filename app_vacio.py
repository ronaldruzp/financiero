import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from io import BytesIO
import requests

# URL corregida con raw
url = "https://raw.githubusercontent.com/cdaniellopez8/financiero/master/Base_Financiero.xlsx"

# Descargar el archivo
response = requests.get(url)
if response.status_code == 200:
    file_path = BytesIO(response.content)
    finances_df = pd.read_excel(file_path, sheet_name='Finanzas', engine="openpyxl")
else:
    st.error("No se pudo descargar el archivo. Verifica la URL.")




# Sidebar para el filtro de bancos
st.sidebar.header("Bancos")
bancos_disponibles=finances_df["Banco"].unique()
banco_seleccionado=st.sidebar.selectbox("Selecciona el banco",bancos_disponibles)

# Filtrar los datos según el banco seleccionado y crear una copia para evitar el SettingWithCopyWarning
finances_filtrado=finances_df[finances_df["Banco"]==banco_seleccionado].copy()

# Títulos y encabezado principal
st.title("Dashboard Financiero")
st.write(f"Visualización de movimientos financieros para {banco_seleccionado}")

# Calcular los totales basados en el filtro
total_recibido = finances_filtrado[finances_filtrado["Tipo"]=="Recibido"]["Valor de movimiento"].sum()
total_hecho = -finances_filtrado[finances_filtrado["Tipo"]=="Pagado"]["Valor de movimiento"].sum()
impuesto = total_recibido*0.15
utilidad = total_recibido-total_hecho-impuesto

# Mostrar los totales en formato de tarjetas con un tamaño de texto más pequeño
col1, col2, col3, col4 = st.columns(4)

with col1:
    st.markdown(f"<h5 style='font-size:14px;'>Pagos Recibidos</h5><h3 style='font-size:20px;'>${total_recibido:,.2f}</h3>", unsafe_allow_html=True)
with col2:
    st.markdown(f"<h5 style='font-size:14px;'>Pagos Hechos</h5><h3 style='font-size:20px;'>${total_hecho:,.2f}</h3>", unsafe_allow_html=True)
with col3:
    st.markdown(f"<h5 style='font-size:14px;'>Impuesto</h5><h3 style='font-size:20px;'>${impuesto:,.2f}</h3>", unsafe_allow_html=True)
with col4:
    st.markdown(f"<h5 style='font-size:14px;'>Utilidad</h5><h3 style='font-size:20px;'>${utilidad:,.2f}</h3>", unsafe_allow_html=True)

# Convertir la columna de fechas y agregar el mes de forma segura
finances_filtrado.loc[:, 'Fecha de movimiento'] = pd.to_datetime(finances_filtrado["Fecha de movimiento"])
finances_filtrado.loc[:, 'Mes'] = finances_filtrado["Fecha de movimiento"].dt.month_name()

# Reemplazar los nombres de los meses en inglés con español
meses_ingles_a_espanol = {
    'January': 'enero', 'February': 'febrero', 'March': 'marzo', 'April': 'abril', 'May': 'mayo', 'June': 'junio',
    'July': 'julio', 'August': 'agosto', 'September': 'septiembre', 'October': 'octubre', 'November': 'noviembre', 'December': 'diciembre'
}
finances_filtrado.loc[:,'Mes'] = finances_filtrado["Mes"].map(meses_ingles_a_espanol)

# Agrupar los datos por mes y calcular la utilidad
utilidad_mensual = finances_filtrado.groupby(["Mes","Tipo"])["Valor de movimiento"].sum().unstack(fill_value=0)
utilidad_mensual['Impuesto'] = utilidad_mensual["Recibido"]*0.15
utilidad_mensual['Utilidad'] = utilidad_mensual["Recibido"]+utilidad_mensual["Pagado"]-utilidad_mensual["Impuesto"]

# Reindexar para asegurar el orden correcto de los meses en español
utilidad_mensual = utilidad_mensual['Utilidad'].reindex(
    ['enero', 'febrero', 'marzo', 'abril', 'mayo', 'junio', 'julio', 'agosto', 'septiembre', 'octubre', 'noviembre', 'diciembre'], 
    fill_value=0
)

# Calcular la utilidad total correctamente
utilidad_total = utilidad_mensual.sum()

# Crear el gráfico de cascada utilizando Plotly
fig = go.Figure(go.Waterfall(
    name="Utilidad por Mes",
    orientation="v",
    measure=["relative"] * len(utilidad_mensual) + ["total"],
    x= list(utilidad_mensual.index)+["Total"],
    text=[f"${val/1e6:.1f} mill." for val in utilidad_mensual.values] + [f"${utilidad_total/1e6:.1f} mill."],
    y= list(utilidad_mensual.values)+[utilidad_total],
    decreasing={"marker": {"color": "orange"}},
    increasing={"marker": {"color": "green"}},
    totals={"marker": {"color": "blue"}}
))

fig.update_layout(
    title=f"Utilidad por Mes del {banco_seleccionado}",
    waterfallgap=0.3,
    showlegend=False,
    yaxis_title="Utilidad en millones",
    xaxis_title="Meses",
    uniformtext_minsize=8,  # Ajustar el tamaño mínimo del texto
    uniformtext_mode='hide'  # Esconder texto si es muy pequeño
)

# Mostrar el gráfico
st.plotly_chart(fig)

# La utilidad es la suma de 'Recibido' menos 'Pagado' - 'Impuesto' para cada ciudad
utilidad_ciudad = finances_filtrado.groupby(['Ciudad','Tipo'])['Valor de movimiento'].sum().unstack(fill_value=0)
utilidad_ciudad['Impuesto'] = utilidad_ciudad['Recibido']*0.15
utilidad_ciudad['Utilidad'] = utilidad_ciudad['Recibido'] + utilidad_ciudad['Pagado'] - utilidad_ciudad['Impuesto']

# Crear un diagrama de barras horizontales con colores personalizados según si la utilidad es positiva o negativa
colores = ['green' if val > 0 else 'orange' for val in utilidad_ciudad['Utilidad']]

fig2 = go.Figure(go.Bar(
    x= utilidad_ciudad['Utilidad'],
    y= utilidad_ciudad.index,
    orientation='h',
    text=[f"${val/1e6:.1f} mill." for val in utilidad_ciudad['Utilidad']],
    marker_color=colores,  # Aplicar los colores según la condición
    textposition='inside'
))

# Personalizar el diseño
fig2.update_layout(
    title=f"Utilidad por Ciudad para {banco_seleccionado}",
    xaxis_title="Utilidad",
    yaxis_title="Ciudad",
    yaxis=dict(categoryorder="total ascending"),
    uniformtext_minsize=8,  # Ajustar el tamaño mínimo del texto
    uniformtext_mode='hide',  # Esconder texto si es muy pequeño
)

# Mostrar el gráfico en Streamlit
st.plotly_chart(fig2)

# Información adicional
margen = utilidad / total_recibido * 100 if total_recibido > 0 else 0
st.subheader("Detalles de Movimientos")
st.write(f"El número de movimientos es de {len(finances_filtrado)}, siendo {len(finances_filtrado[finances_filtrado['Forma de pago'] == 'Tarjeta'])} hechos con tarjeta, con un margen de ingreso de {margen:.2f} %")


# Tabla detallada
st.dataframe(finances_filtrado.head(10))


# Información adicional
margen = utilidad / total_recibido * 100 if total_recibido > 0 else 0
st.subheader("Detalles de Movimientos")
st.write(f"El número de movimientos es de {len(finances_filtrado)}, siendo {len(finances_filtrado[finances_filtrado['Forma de pago'] == 'Tarjeta'])} hechos con tarjeta, con un margen de ingreso de {margen:.2f} %")


