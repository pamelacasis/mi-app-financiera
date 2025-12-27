import streamlit as st
import pandas as pd
import yfinance as yf
import plotly.express as px
import numpy as np

st.set_page_config(page_title="Inversor Inteligente Pro", layout="wide")

st.title("🚀 Buscador de Inversiones Automatizado")
st.markdown("Si el buscador no encuentra el nombre, podés ingresar directamente el Ticker (Ej: AL30.BA, AAPL, GGAL.BA).")

if 'lista_instrumentos' not in st.session_state:
    st.session_state.lista_instrumentos = []

# --- Sidebar ---
st.sidebar.header("🔍 Buscar Instrumento")
query = st.sidebar.text_input("Nombre o Ticker:", "").upper()

if query:
    try:
        # Intentamos obtener datos directamente asumiendo que es un Ticker
        asset = yf.Ticker(query)
        hist = asset.history(period="1y")
        
        if not hist.empty:
            # Si encuentra datos directos, mostramos el botón para agregar
            nombre_mostrar = asset.info.get('longName', query)
            st.sidebar.success(f"Encontrado: {nombre_mostrar}")
            if st.sidebar.button("Añadir a mi Cartera"):
                precio_ayer = hist['Close'].iloc[-1]
                retorno_total = (hist['Close'].iloc[-1] / hist['Close'].iloc[0]) - 1
                tasa_mensual_auto = (1 + retorno_total)**(1/12) - 1
                
                st.session_state.lista_instrumentos.append({
                    "Ticker": query,
                    "Nombre": nombre_mostrar,
                    "Precio Cierre": round(precio_ayer, 2),
                    "Tasa Mensual Hist. (%)": round(tasa_mensual_auto * 100, 2)
                })
                st.rerun()
        else:
            st.sidebar.error("No se encontraron datos. Asegurate de usar el Ticker correcto (Ej: agregá '.BA' para activos argentinos).")
            
            # Ayuda visual para el usuario
            st.sidebar.info("""
            **Tips de búsqueda:**
            * **Bonos/Acciones Arg:** Ticker + .BA (Ej: `AL30.BA`, `YPFD.BA`)
            * **Acciones USA:** Ticker solo (Ej: `AAPL`, `TSLA`, `KO`)
            * **CEDEARs:** Ticker solo o + .BA (Ej: `MSFT`, `MELI.BA`)
            """)

    except Exception as e:
        st.sidebar.error(f"Error: {e}")

if st.sidebar.button("Limpiar Cartera"):
    st.session_state.lista_instrumentos = []
    st.rerun()

# --- Panel Principal ---
if st.session_state.lista_instrumentos:
    df_base = pd.DataFrame(st.session_state.lista_instrumentos)
    
    resultados = []
    tickers_validos = []

    for _, row in df_base.iterrows():
        tasa = row["Tasa Mensual Hist. (%)"] / 100
        valor_proyectado = row["Precio Cierre"] * (1 + tasa)**120
        
        # Riesgo basado en volatilidad
        try:
            data_vol = yf.download(row["Ticker"], period="1y", progress=False)['Adj Close']
            if not data_vol.empty:
                vol = data_vol.pct_change().std() * np.sqrt(252)
                riesgo = "Bajo 🟢" if vol < 0.20 else "Medio 🟡" if vol < 0.45 else "Alto 🔴"
                tickers_validos.append(row["Ticker"])
            else:
                riesgo = "N/D"
        except:
            riesgo = "Error"
        
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
        
        total_hoy = sum([float(r['Precio Actual'].replace('$', '').replace(',', '')) for r in resultados])
        total_proy = sum([float(r['Proyección 10 años'].replace('$', '').replace(',', '')) for r in resultados])
        
        st.metric("Inversión Total Inicial", f"${total_hoy:,.2f}")
        st.metric("Proyección Total a 10 años", f"${total_proy:,.2f}", delta=f"{((total_proy/total_hoy)-1)*100:.2f}%")
        
    with col2:
        st.subheader("📉 Comparativa Histórica")
        if tickers_validos:
            data_graf = yf.download(tickers_validos, period="1y", progress=False)['Adj Close']
            rendimiento = (data_graf / data_graf.iloc[0]) * 100
            fig = px.line(rendimiento, title="Evolución Relativa (Base 100)")
            st.plotly_chart(fig, use_container_width=True)

    csv = pd.DataFrame(resultados).to_csv(index=False).encode('utf-8')
    st.download_button("📥 Descargar Reporte", csv, "cartera.csv", "text/csv")
else:
    st.info("Ingresá un Ticker válido a la izquierda. Ejemplo: 'AL30.BA' para bonos argentinos o 'AAPL' para Apple.")
