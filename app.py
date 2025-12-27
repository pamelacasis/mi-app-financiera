import streamlit as st
import pandas as pd
import yfinance as yf
import plotly.express as px
import numpy as np

st.set_page_config(page_title="Inversor Inteligente Pro", layout="wide")

st.title("🚀 Buscador de Inversiones Automatizado")
st.markdown("Escribí el nombre de la empresa, bono o CEDEAR y la app encontrará los datos por vos.")

if 'lista_instrumentos' not in st.session_state:
    st.session_state.lista_instrumentos = []

# --- Sidebar ---
st.sidebar.header("🔍 Buscar Instrumento")
query = st.sidebar.text_input("Nombre de la empresa o bono (Ej: Apple, Google, Galicia, Aluar)", "")

if query:
    # Función de búsqueda de tickers basada en el nombre
    try:
        search_results = yf.Search(query, max_results=5).tickers
        if search_results:
            options = {f"{res['symbol']} - {res['shortname']} ({res['exchange']})": res['symbol'] for res in search_results}
            seleccion = st.sidebar.selectbox("Seleccioná el correcto:", options.keys())
            ticker_final = options[seleccion]
            
            if st.sidebar.button("Añadir a mi Cartera"):
                with st.spinner(f'Obteniendo datos de {ticker_final}...'):
                    asset = yf.Ticker(ticker_final)
                    hist = asset.history(period="1y")
                    
                    if not hist.empty:
                        precio_ayer = hist['Close'].iloc[-1]
                        retorno_total = (hist['Close'].iloc[-1] / hist['Close'].iloc[0]) - 1
                        tasa_mensual_auto = (1 + retorno_total)**(1/12) - 1
                        
                        st.session_state.lista_instrumentos.append({
                            "Ticker": ticker_final,
                            "Nombre": seleccion.split(" - ")[1],
                            "Precio Cierre": round(precio_ayer, 2),
                            "Tasa Mensual Hist. (%)": round(tasa_mensual_auto * 100, 2)
                        })
                        st.sidebar.success(f"Agregado: {ticker_final}")
                    else:
                        st.sidebar.error("No hay datos históricos suficientes.")
        else:
            st.sidebar.warning("No se encontraron resultados para ese nombre.")
    except Exception as e:
        st.sidebar.error(f"Error en la búsqueda: {e}")

if st.sidebar.button("Limpiar Cartera"):
    st.session_state.lista_instrumentos = []
    st.rerun()

# --- Panel Principal ---
if st.session_state.lista_instrumentos:
    df_base = pd.DataFrame(st.session_state.lista_instrumentos)
    
    resultados = []
    for _, row in df_base.iterrows():
        tasa = row["Tasa Mensual Hist. (%)"] / 100
        valor_proyectado = row["Precio Cierre"] * (1 + tasa)**120
        
        # Riesgo basado en volatilidad
        data_vol = yf.download(row["Ticker"], period="1y", progress=False)['Adj Close']
        vol = data_vol.pct_change().std() * np.sqrt(252)
        riesgo = "Bajo 🟢" if vol < 0.20 else "Medio 🟡" if vol < 0.45 else "Alto 🔴"
        
        resultados.append({
            "Nombre": row["Nombre"],
            "Ticker": row["Ticker"],
            "Precio Actual": f"${row['Precio Cierre']:,.2f}",
            "Rend. Mensual": f"{row['Tasa Mensual Hist. (%)']}%",
            "Riesgo Est.": riesgo,
            "Proyección 10 años": f"${valor_proyectado:,.2f}"
        })

    col1, col2 = st.columns([1.2, 0.8])
    
    with col1:
        st.subheader("📋 Resumen de la Cartera")
        st.table(pd.DataFrame(resultados))
        
        # Sumatoria Total
        total_hoy = sum([float(r['Precio Actual'].replace('$', '').replace(',', '')) for r in resultados])
        total_proy = sum([float(r['Proyección 10 años'].replace('$', '').replace(',', '')) for r in resultados])
        
        st.metric("Inversión Total Inicial (1 de cada uno)", f"${total_hoy:,.2f}")
        st.metric("Proyección Total a 10 años", f"${total_proy:,.2f}", delta=f"{((total_proy/total_hoy)-1)*100:.2f}%")
        
    with col2:
        st.subheader("📉 Comparativa Histórica")
        tickers = [r['Ticker'] for r in resultados]
        data_graf = yf.download(tickers, period="1y", progress=False)['Adj Close']
        rendimiento = (data_graf / data_graf.iloc[0]) * 100
        fig = px.line(rendimiento, title="Evolución Relativa (Base 100)")
        st.plotly_chart(fig, use_container_width=True)

    csv = pd.DataFrame(resultados).to_csv(index=False).encode('utf-8')
    st.download_button("📥 Descargar Reporte", csv, "cartera.csv", "text/csv")
else:
    st.info("Escribí el nombre de una empresa en el buscador de la izquierda para empezar.")
