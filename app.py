import streamlit as st
import pandas as pd
import yfinance as yf
import plotly.express as px
import numpy as np

# Configuración básica
st.set_page_config(page_title="Inversor Pro", layout="wide")

st.title("🚀 Buscador de Inversiones")

# Inicializar la lista si no existe
if 'lista' not in st.session_state:
    st.session_state.lista = []

# --- BARRA LATERAL ---
st.sidebar.header("🔍 Cargar Activo")
ticker_input = st.sidebar.text_input("Ticker (Ej: AAPL, AL30.BA, GGAL.BA):").upper()

if st.sidebar.button("Agregar"):
    if ticker_input:
        try:
            with st.spinner('Buscando...'):
                t = yf.Ticker(ticker_input)
                # Forzamos la descarga de 1 año para cálculos
                hist = t.history(period="1y")
                
                if not hist.empty:
                    precio = hist['Close'].iloc[-1]
                    # Calculamos el rendimiento del último año
                    rend_anual = (hist['Close'].iloc[-1] / hist['Close'].iloc[0]) - 1
                    tasa_mensual = (1 + rend_anual)**(1/12) - 1
                    
                    nombre = t.info.get('longName', ticker_input)
                    
                    st.session_state.lista.append({
                        "Ticker": ticker_input,
                        "Nombre": nombre,
                        "Precio": float(precio),
                        "Tasa": float(tasa_mensual)
                    })
                    st.sidebar.success(f"¡{ticker_input} agregado!")
                else:
                    st.sidebar.error("No se encontraron precios para ese ticker.")
        except Exception as e:
            st.sidebar.error(f"Error técnico: {e}")

if st.sidebar.button("Borrar Todo"):
    st.session_state.lista = []
    st.rerun()

# --- PANEL PRINCIPAL ---
if st.session_state.lista:
    res = []
    tickers_graf = []
    
    for item in st.session_state.lista:
        # Proyección a 10 años (120 meses)
        valor_10_anos = item['Precio'] * (1 + item['Tasa'])**120
        
        # Riesgo (Volatilidad)
        try:
            # Usamos un bloque simple para el riesgo
            hist_vol = yf.download(item['Ticker'], period="1y", progress=False)['Adj Close']
            vol = hist_vol.pct_change().std() * np.sqrt(252)
            riesgo = "Bajo 🟢" if vol < 0.2 else "Medio 🟡" if vol < 0.4 else "Alto 🔴"
            tickers_graf.append(item['Ticker'])
        except:
            riesgo = "N/D"

        res.append({
            "Instrumento": item['Nombre'],
            "Ticker": item['Ticker'],
            "Precio Cierre": f"${item['Precio']:,.2f}",
            "Tasa Mensual (%)": f"{item['Tasa']*100:.2f}%",
            "Riesgo": riesgo,
            "Valor en 10 años": f"${valor_10_anos:,.2f}"
        })

    # Mostrar Tabla
    st.subheader("📊 Resumen de Proyecciones")
    df_mostrar = pd.DataFrame(res)
    st.table(df_mostrar)

    # Mostrar Gráfico
    if tickers_graf:
        st.subheader("📈 Evolución últimos 12 meses")
        try:
            data = yf.download(tickers_graf, period="1y", progress=False)['Adj Close']
            # Normalizar para que todos empiecen en 100
            data_norm = (data / data.iloc[0]) * 100
            fig = px.line(data_norm)
            st.plotly_chart(fig, use_container_width=True)
        except:
            st.warning("No se pudo generar el gráfico comparativo.")

    # Exportar
    csv = df_mostrar.to_csv(index=False).encode('utf-8')
    st.download_button("📥 Descargar Reporte", csv, "cartera.csv", "text/csv")

else:
    st.info("La lista está vacía. Usá la barra lateral para agregar activos.")
