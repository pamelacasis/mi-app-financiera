import streamlit as st
import pandas as pd
import yfinance as yf
import plotly.express as px
import numpy as np

st.set_page_config(page_title="Planificador de Cartera Pro", layout="wide")

st.title("💰 Planificador de Inversión y Cartera")

# --- ESTADO DE LA APP ---
if 'cartera' not in st.session_state:
    st.session_state.cartera = []

# --- SIDEBAR: CONFIGURACIÓN GENERAL ---
st.sidebar.header("1. Configuración Global")
monto_total = st.sidebar.number_input("Monto Total a Invertir ($)", min_value=0.0, value=10000.0, step=100.0)
plazo_anos = st.sidebar.slider("Plazo de la inversión (Años)", min_value=1, max_value=40, value=10)

st.sidebar.markdown("---")
st.sidebar.header("2. Agregar Instrumentos")
ticker_input = st.sidebar.text_input("Ticker (Ej: AAPL, AL30.BA, SPY):").upper()
porcentaje = st.sidebar.slider("% de la cartera para este activo", 0, 100, 10)

if st.sidebar.button("Añadir a la Cartera"):
    if ticker_input:
        try:
            with st.spinner('Cargando datos...'):
                t = yf.Ticker(ticker_input)
                hist = t.history(period="1y")
                if not hist.empty:
                    # Rendimiento anualizado
                    rend_anual = (hist['Close'].iloc[-1] / hist['Close'].iloc[0]) - 1
                    tasa_mensual = (1 + rend_anual)**(1/12) - 1
                    
                    st.session_state.cartera.append({
                        "Ticker": ticker_input,
                        "Nombre": t.info.get('longName', ticker_input),
                        "Porcentaje": porcentaje,
                        "Precio": hist['Close'].iloc[-1],
                        "Tasa Mensual": tasa_mensual
                    })
                else:
                    st.sidebar.error("No se encontraron datos.")
        except Exception as e:
            st.sidebar.error(f"Error: {e}")

if st.sidebar.button("Limpiar Cartera"):
    st.session_state.cartera = []
    st.rerun()

# --- PANEL PRINCIPAL ---
if st.session_state.cartera:
    df_base = pd.DataFrame(st.session_state.cartera)
    
    # Validar suma de porcentajes
    suma_pct = df_base['Porcentaje'].sum()
    if suma_pct > 100:
        st.warning(f"⚠️ ¡Atención! Tus porcentajes suman {suma_pct}%. Deberían sumar 100%.")
    
    res = []
    tickers_para_grafico = []

    for _, row in df_base.iterrows():
        # Dinero asignado a este activo
        monto_asignado = monto_total * (row['Porcentaje'] / 100)
        
        # Interés Compuesto: Vf = P * (1 + r)^n
        meses = plazo_anos * 12
        valor_final = monto_asignado * (1 + row['Tasa Mensual'])**meses
        
        # Volatilidad para Riesgo
        try:
            h_vol = yf.download(row['Ticker'], period="1y", progress=False)['Adj Close']
            vol = h_vol.pct_change().std() * np.sqrt(252)
            riesgo = "Bajo 🟢" if vol < 0.2 else "Medio 🟡" if vol < 0.4 else "Alto 🔴"
            tickers_para_grafico.append(row['Ticker'])
        except:
            riesgo = "N/D"

        res.append({
            "Instrumento": row['Nombre'],
            "Ticker": row['Ticker'],
            "Asignación (%)": f"{row['Porcentaje']}%",
            "Monto Inicial": f"${monto_asignado:,.2f}",
            "Rend. Mensual": f"{row['Tasa Mensual']*100:.2f}%",
            "Riesgo": riesgo,
            "Valor Final Estimado": valor_final
        })

    # Mostrar Tabla
    st.subheader(f"📊 Análisis de Cartera a {plazo_anos} años")
    df_res = pd.DataFrame(res)
    
    # Formatear valor final para la tabla
    df_tabla = df_res.copy()
    df_tabla['Valor Final Estimado'] = df_tabla['Valor Final Estimado'].apply(lambda x: f"${x:,.2f}")
    st.table(df_tabla)

    # Métricas de Resumen
    total_final_cartera = df_res['Valor Final Estimado'].sum()
    ganancia_neta = total_final_cartera - monto_total
    
    c1, c2, c3 = st.columns(3)
    c1.metric("Inversión Inicial", f"${monto_total:,.2f}")
    c2.metric(f"Valor Total en {plazo_anos} años", f"${total_final_cartera:,.2f}")
    c3.metric("Ganancia Estimada", f"${ganancia_neta:,.2f}", delta=f"{((total_final_cartera/monto_total)-1)*100:.1f}%")

    # Gráficos
    col_g1, col_g2 = st.columns(2)
    
    with col_g1:
        st.subheader("📈 Evolución de Precios (12m)")
        if tickers_para_grafico:
            data = yf.download(tickers_para_grafico, period="1y", progress=False)['Adj Close']
            data_norm = (data / data.iloc[0]) * 100
            fig_line = px.line(data_norm, labels={'value': 'Rendimiento %', 'Date': 'Fecha'})
            st.plotly_chart(fig_line, use_container_width=True)

    with col_g2:
        st.subheader("🍕 Distribución de Cartera")
        fig_pie = px.pie(df_res, values='Asignación (%)', names='Ticker', hole=0.3)
        st.plotly_chart(fig_pie, use_container_width=True)

    # Exportar
    csv = df_res.to_csv(index=False).encode('utf-8')
    st.download_button("📥 Descargar Plan de Inversión", csv, "mi_plan.csv", "text/csv")

else:
    st.info("Configurá tu monto total y empezá a agregar instrumentos desde la barra lateral.")
