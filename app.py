import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go
import finance as fn  # <-- Bak, kendi yazdığımız modülü çağırıyoruz!
import utils as ut    # <-- Metinleri ve çeviriyi buradan alıyoruz!

# --- 1. AYARLAR & TASARIM ---
st.set_page_config(page_title="KoçFin Pro", layout="wide", page_icon="📈")

st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;600;700&display=swap');
    .stApp { background-color: #131722; font-family: 'Inter', sans-serif; }
    [data-testid="stSidebar"] { background-color: #1e222d; border-right: 1px solid #2a2e39; }
    .metric-card { background-color: #2a2e39; border-radius: 12px; padding: 20px; border: 1px solid #363a45; box-shadow: 0 4px 6px rgba(0,0,0,0.3); text-align: center; transition: transform 0.2s; }
    .metric-card:hover { transform: translateY(-3px); border: 1px solid #787b86; }
    .metric-value { font-size: 28px; font-weight: 700; color: #ECEFF1; }
    .metric-label { font-size: 13px; color: #B2B5BE; font-weight: 600; text-transform: uppercase; margin-bottom: 8px; }
    .color-up { color: #00E396; } 
    .color-down { color: #FF4560; }
    .color-neutral { color: #008FFB; }
    .color-gold { color: #FEB019; }
    .news-card { background-color: #1e222d; padding: 15px; border-radius: 10px; border-left: 4px solid #FEB019; margin-bottom: 10px; }
    a { color: #ECEFF1 !important; text-decoration: none; }
    a:hover { color: #FEB019 !important; }
    .stTabs [data-baseweb="tab-list"] button { color: #B2B5BE; }
    .stTabs [data-baseweb="tab-list"] button[aria-selected="true"] { background-color: #2a2e39 !important; color: #00E396 !important; border-bottom: 2px solid #00E396 !important; }
</style>
""", unsafe_allow_html=True)

# --- 2. SIDEBAR VE DİL SEÇİMİ ---
dil_secimi = st.sidebar.radio("🌐 Language / Dil", ["Türkçe", "English"])
lang = 'tr' if dil_secimi == "Türkçe" else 'en'
t = ut.TEXTS[lang] # Metinleri utils.py'den çekiyoruz

st.sidebar.markdown(f"### 📈 {t['sidebar_title']}")
sembol = st.sidebar.text_input(t['symbol_input'], "THYAO.IS")
periyot = st.sidebar.select_slider(t['period_input'], options=["3mo", "6mo", "1y", "2y", "5y"], value="1y")

st.sidebar.markdown(f"### {t['layers']}")
goster_sma = st.sidebar.checkbox(t['layer_sma'], value=True)
goster_bollinger = st.sidebar.checkbox(t['layer_bollinger'], value=True)
goster_sinyaller = st.sidebar.checkbox(t['layer_signals'], value=True)

st.sidebar.markdown("---")
st.sidebar.info(f"{t['developer_title']}\n\n{t['developer_desc']}")

# --- 3. ANA UYGULAMA MANTIĞI ---
if sembol:
    try:
        with st.spinner(t['loading']):
            # finance.py içindeki fonksiyonları kullanıyoruz (fn.get_...)
            df = yf.download(sembol, period=periyot, auto_adjust=False)
            sirket_bilgisi = fn.get_company_info(sembol)
            haberler, sirket_adi = fn.get_smart_news(sembol, lang)

        if df.empty:
            st.error(t['error_data'])
        else:
            if isinstance(df.columns, pd.MultiIndex): df.columns = df.columns.get_level_values(0)
            
            # Hesaplamalar finance.py'den geliyor
            df = fn.duzelt_bolunme_hatasi(df, sembol)
            df = fn.teknik_indikatorleri_hesapla(df)
            
            current_price = df['Close'].iloc[-1]
            prev_price = df['Close'].iloc[0]
            delta = ((current_price - prev_price) / prev_price) * 100
            
            color_class = "color-up" if delta > 0 else "color-down"
            icon = "▲" if delta > 0 else "▼"
            
            st.markdown(f"<h2 style='color:#B2B5BE;'>{sirket_adi}</h2>", unsafe_allow_html=True)
            st.markdown(f"<h1 class='{color_class}' style='font-size:42px; font-weight:bold; margin-top:-15px'>{current_price:.2f} <span style='font-size:22px; color:#ECEFF1'>{icon} %{delta:.2f}</span></h1>", unsafe_allow_html=True)

            tab1, tab2, tab3 = st.tabs([t['tab_tech'], t['tab_fund'], t['tab_news']])

            with tab1:
                c1, c2, c3, c4 = st.columns(4)
                
                # RSI
                rsi_val = df['RSI'].iloc[-1]
                rsi_color = "color-neutral"
                rsi_msg = t['rsi_neutral']
                if rsi_val > 70: rsi_msg = t['rsi_overbought']; rsi_color = "color-down"
                elif rsi_val < 30: rsi_msg = t['rsi_oversold']; rsi_color = "color-up"
                c1.markdown(f"<div class='metric-card'><div class='metric-label'>{t['rsi_label']}</div><div class='metric-value {rsi_color}'>{rsi_val:.0f}</div><div style='font-size:12px; color:#B2B5BE; margin-top:5px'>{rsi_msg}</div></div>", unsafe_allow_html=True)
                
                # Stokastik
                stoch_k = df['Stoch_K'].iloc[-1]
                stoch_color = "color-neutral"
                stoch_msg = t['stoch_wait']
                if stoch_k > 80: stoch_msg = t['stoch_sell']; stoch_color = "color-down"
                elif stoch_k < 20: stoch_msg = t['stoch_buy']; stoch_color = "color-up"
                c2.markdown(f"<div class='metric-card'><div class='metric-label'>{t['stoch_label']}</div><div class='metric-value {stoch_color}'>{stoch_k:.0f}</div><div style='font-size:12px; color:#B2B5BE; margin-top:5px'>{stoch_msg}</div></div>", unsafe_allow_html=True)
                
                # Bollinger
                fiyat = df['Close'].iloc[-1]
                bb_upper = df['Bollinger_Upper'].iloc[-1]
                bb_lower = df['Bollinger_Lower'].iloc[-1]
                bb_msg = t['bb_normal']
                bb_color = "color-neutral"
                if fiyat > bb_upper: bb_msg = t['bb_expensive']; bb_color = "color-down"
                elif fiyat < bb_lower: bb_msg = t['bb_cheap']; bb_color = "color-up"
                c3.markdown(f"<div class='metric-card'><div class='metric-label'>{t['bb_label']}</div><div class='metric-value {bb_color}'>{fiyat:.2f}</div><div style='font-size:12px; color:#B2B5BE; margin-top:5px'>{bb_msg}</div></div>", unsafe_allow_html=True)
                
                # Trend
                macd = df['MACD'].iloc[-1]
                signal = df['Signal_Line'].iloc[-1]
                trend_msg = t['trend_up'] if macd > signal else t['trend_down']
                trend_color = "color-up" if macd > signal else "color-down"
                c4.markdown(f"<div class='metric-card'><div class='metric-label'>{t['trend_label']}</div><div class='metric-value {trend_color}' style='font-size:24px'>{trend_msg}</div></div>", unsafe_allow_html=True)

                st.markdown("###")
                
                fig = go.Figure()
                fig.add_trace(go.Candlestick(x=df.index, open=df['Open'], high=df['High'], low=df['Low'], close=df['Close'], name='Fiyat', increasing_line_color='#00E396', decreasing_line_color='#FF4560', showlegend=False))
                
                if goster_bollinger:
                    fig.add_trace(go.Scatter(x=df.index, y=df['Bollinger_Upper'], line=dict(color='rgba(0, 143, 251, 0.3)', width=1), name='Üst Bant', showlegend=False))
                    fig.add_trace(go.Scatter(x=df.index, y=df['Bollinger_Lower'], line=dict(color='rgba(0, 143, 251, 0.3)', width=1), fill='tonexty', fillcolor='rgba(0, 143, 251, 0.05)', name='Alt Bant', showlegend=False))
                
                if goster_sma:
                    fig.add_trace(go.Scatter(x=df.index, y=df['SMA_20'], line=dict(color='#FEB019', width=1.5), name='SMA 20'))
                    fig.add_trace(go.Scatter(x=df.index, y=df['SMA_50'], line=dict(color='#008FFB', width=1.5), name='SMA 50'))

                if goster_sinyaller:
                    sinyaller = fn.al_sat_sinyalleri_yakala(df, t) # finance.py'den çağırıyoruz
                    for tarih, fiyat, tip in sinyaller:
                        color = '#00E396' if tip == t['buy_signal'] else '#FF4560'
                        ay_val = 25 if tip == t['buy_signal'] else -25
                        fig.add_annotation(x=tarih, y=fiyat, text=tip, showarrow=True, arrowhead=2, arrowcolor=color, ay=ay_val, bgcolor=color, font=dict(color="#ffffff", size=9))

                fig.update_layout(height=550, dragmode='pan', hovermode='x unified', paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(255,255,255,0.02)', margin=dict(l=5, r=5, t=10, b=10), legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1, font=dict(color='#B2B5BE')), xaxis=dict(showgrid=True, gridcolor='#2a2e39', rangeslider=dict(visible=False)), yaxis=dict(showgrid=True, gridcolor='#2a2e39', side='right'), font=dict(color='#B2B5BE'))
                config = {'displayModeBar': True, 'displaylogo': False, 'modeBarButtonsToRemove': ['select2d', 'lasso2d', 'autoScale2d']}
                st.plotly_chart(fig, use_container_width=True, config=config)

            with tab2:
                if sirket_bilgisi:
                    c1, c2, c3 = st.columns(3)
                    fk = sirket_bilgisi.get('trailingPE', 'N/A')
                    fk_val = f"{fk:.2f}" if isinstance(fk, (int, float)) else t['no_data']
                    c1.markdown(f"<div class='metric-card'><div class='metric-label'>{t['pe_ratio']}</div><div class='metric-value color-gold'>{fk_val}</div></div>", unsafe_allow_html=True)
                    
                    mcap = sirket_bilgisi.get('marketCap', 0)
                    if mcap > 1_000_000_000: mcap_str = f"{mcap/1_000_000_000:.1f} Mr"
                    else: mcap_str = f"{mcap/1_000_000:.1f} Mn"
                    c2.markdown(f"<div class='metric-card'><div class='metric-label'>{t['market_cap']}</div><div class='metric-value color-neutral'>{mcap_str}</div></div>", unsafe_allow_html=True)
                    
                    raw_sektor = sirket_bilgisi.get('sector', 'Bilinmiyor')
                    sektor_tr = ut.metni_cevir(raw_sektor, lang) # utils.py'den çağırıyoruz
                    c3.markdown(f"<div class='metric-card'><div class='metric-label'>{t['sector']}</div><div class='metric-value' style='font-size:20px; color:#ECEFF1'>{sektor_tr}</div></div>", unsafe_allow_html=True)
                    
                    raw_ozet = sirket_bilgisi.get('longBusinessSummary', t['no_data'])
                    ozet_tr = ut.metni_cevir(raw_ozet[:800], lang)
                    st.markdown("###")
                    st.markdown(f"<div style='background:#1e222d; padding:20px; border-radius:10px; border:1px solid #363a45; color:#ECEFF1;'><h4 style='color:#FEB019'>{t['profile_title']}</h4><p>{ozet_tr}...</p></div>", unsafe_allow_html=True)
                else:
                    st.warning(t['error_data'])

            with tab3:
                for haber in haberler:
                    st.markdown(f"<div class='news-card'><a href='{haber.link}' target='_blank' style='font-size:16px; font-weight:600'>{haber.title}</a><div style='font-size:12px; color:#B2B5BE; margin-top:8px'>🗓️ {haber.published[:16]}</div></div>", unsafe_allow_html=True)

    except Exception as e:
        st.error(f"{t['error_sys']} {e}")