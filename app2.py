import streamlit as st
import pandas as pd
import yfinance as yf
import plotly.express as px
import numpy as np

st.set_page_config(page_title="Gestor de Cartera - Rendimiento", layout="wide")

st.title("📊 Planificador de Cartera y Rendimiento Mensual")

if 'cartera' not in st.session_state:
    st.session_state.cartera = []

# --- SIDEBAR ---
st.sidebar.header("1. Configuración de Inversión")
monto_total = st.sidebar.number_input("Monto Total ($)", min_value=0.0, value=10000.0)
plazo_anos = st.sidebar.slider("Años de proyección", 1, 40, 10)

st.sidebar.markdown("---")
st.sidebar.header("2. Agregar Activo")
ticker_input = st.sidebar.text_input("Ticker (Ej: AAPL, AL30.BA):").upper()
porcentaje = st.sidebar.slider("% de asignación", 1, 100, 10)

if st.sidebar.button("Añadir a la Cartera"):
    if ticker_input:
        try:
            with st.spinner(f'Analizando {ticker_input}...'):
                t = yf.Ticker(ticker_input)
                hist = t.history(period="1y")
                if not hist.empty:
                    # Tasa mensual promedio para la proyección
                    retorno_anual = (hist['Close'].iloc[-1] / hist['Close'].iloc[0]) - 1
                    tasa_mensual_promedio = (1 + retorno_anual)**(1/12) - 1
                    
                    st.session_state.cartera.append({
                        "Ticker": ticker_input,
                        "Nombre": t.info.get('longName', ticker_input),
                        "Porcentaje": float(porcentaje),
                        "Precio": float(hist['Close'].iloc[-1]),
                        "Tasa_Promedio": float(tasa_mensual_promedio)
                    })
                    st.rerun()
                else:
                    st.sidebar.error("No se encontraron datos.")
        except:
            st.sidebar.error("Error al buscar el ticker.")

if st.sidebar.button("Limpiar Cartera"):
    st.session_state.cartera = []
    st.rerun()

# --- PROCESAMIENTO Y DASHBOARD ---
if st.session_state.cartera:
    df_base = pd.DataFrame(st.session_state.cartera)
    
    # 1. TABLA Y CÁLCULOS
    res_datos = []
    tickers_validos = []
    
    for _, row in df_base.iterrows():
        asignado = monto_total * (row['Porcentaje'] / 100)
        v_final = asignado * (1 + row['Tasa_Promedio'])**(plazo_anos * 12)
        tickers_validos.append(row['Ticker'])
        
        res_datos.append({
            "Ticker": row['Ticker'],
            "Asignación": f"{row['Porcentaje']}%",
            "Monto Inicial": asignado,
            "Rend. Mensual Prom.": f"{row['Tasa_Promedio']*100:.2f}%",
            "Valor Final Est.": v_final,
            "Pct_Num": row['Porcentaje'] # Para el gráfico de torta
        })

    df_res = pd.DataFrame(res_datos)
    
    st.subheader(f"📋 Resumen de Cartera a {plazo_anos} años")
    # Formateo para la tabla
    df_tab = df_res.copy()
    df_tab['Monto Inicial'] = df_tab['Monto Inicial'].map("${:,.2f}".format)
    df_tab['Valor Final Est.'] = df_tab['Valor Final Est.'].map("${:,.2f}".format)
    st.table(df_tab.drop(columns=['Pct_Num']))

    # MÉTRICAS TOTALES
    t_final = df_res['Valor Final Est.'].sum()
    c1, c2 = st.columns(2)
    c1.metric("Inversión Total", f"${monto_total:,.2f}")
    c2.metric(f"Capital Final ({plazo_anos} años)", f"${t_final:,.2f}", delta=f"{((t_final/monto_total)-1)*100:.1f}%")

    st.markdown("---")
    
    # 2. GRÁFICO DE RENDIMIENTO MENSUAL (BARRAS)
    st.subheader("📊 Rendimiento Mensual del Último Año")
    if tickers_validos:
        try:
            # Descargamos datos históricos
            data = yf.download(tickers_validos, period="1y", progress=False)['Adj Close']
            
            # Si es uno solo, convertimos a DataFrame
            if len(tickers_validos) == 1:
                data = data.to_frame(name=tickers_validos[0])
            
            # Resampleamos a fin de mes y calculamos cambio porcentual
            mensual = data.resample('ME').last().pct_change() * 100
            mensual = mensual.dropna().reset_index()
            
            # Transformamos el DataFrame para que Plotly lo entienda (formato largo)
            mensual_melted = mensual.melt(id_vars='Date', var_name='Ticker', value_name='Rendimiento %')
            mensual_melted['Mes'] = mensual_melted['Date'].dt.strftime('%b %Y')

            fig_bar = px.bar(
                mensual_melted, 
                x='Mes', 
                y='Rendimiento %', 
                color='Ticker',
                barmode='group',
                title="Variación Porcentual Mensual",
                text_auto='.2f'
            )
            st.plotly_chart(fig_bar, use_container_width=True)
        except Exception as e:
            st.error(f"No se pudo generar el gráfico de barras: {e}")

    # 3. GRÁFICO DE TORTA
    st.subheader("🍕 Composición de la Inversión")
    fig_pie = px.pie(df_res, values='Pct_Num', names='Ticker', hole=0.4)
    st.plotly_chart(fig_pie, use_container_width=True)

else:
    st.info("Agregá instrumentos desde la barra lateral para ver el análisis.")
