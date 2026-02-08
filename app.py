import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go
import feedparser
import urllib.parse
import numpy as np
from deep_translator import GoogleTranslator

# --- 1. DİL SÖZLÜĞÜ (Aynı Kalıyor) ---
TEXTS = {
    'tr': {
        'title': "KoçFin Neon",
        'sidebar_title': "KoçFin Terminal",
        'lang_select': "Dil / Language",
        'symbol_input': "Varlık Sembolü",
        'period_input': "Zaman Aralığı",
        'layers': "🎨 Grafik Katmanları",
        'layer_sma': "SMA (Ortalamalar)",
        'layer_bollinger': "Bollinger Bantları",
        'layer_signals': "AI Sinyalleri",
        'developer_title': "👨‍💻 Geliştirici: Emirhan",
        'developer_desc': "'Geleceğin Finans Arayüzü' Vizyonuyla Tasarlanmıştır.",
        'loading': "Siber Uzaydan Veriler Çekiliyor...",
        'error_data': "Veri bulunamadı veya sembol hatalı.",
        'error_sys': "Sistem Hatası:",
        'tab_tech': "📊 Teknik Evren",
        'tab_fund': "🏢 Şirket Çekirdeği",
        'tab_news': "📰 Haber Akışı",
        'rsi_label': "RSI (Momentum)",
        'rsi_overbought': "Aşırı Alım 🔥",
        'rsi_oversold': "Aşırı Satım 🧊",
        'rsi_neutral': "Nötr 😐",
        'stoch_label': "Stokastik",
        'stoch_sell': "Satış Bölgesi 🔻",
        'stoch_buy': "Alış Bölgesi 🚀",
        'stoch_wait': "Bekle ✋",
        'bb_label': "Bollinger Durumu",
        'bb_expensive': "Pahalı ⚠️",
        'bb_cheap': "Ucuz 🟢",
        'bb_normal': "Normal Bant 👌",
        'trend_label': "Ana Trend",
        'trend_up': "Yükseliş 🐂",
        'trend_down': "Düşüş 🐻",
        'pe_ratio': "F/K Oranı",
        'market_cap': "Piyasa Değeri",
        'sector': "Sektör",
        'profile_title': "🏢 Şirket Profili",
        'no_data': "Veri Yok",
        'buy_signal': "AL",
        'sell_signal': "SAT"
    },
    'en': {
        'title': "KocFin Neon",
        'sidebar_title': "KocFin Terminal",
        'lang_select': "Language / Dil",
        'symbol_input': "Asset Symbol",
        'period_input': "Time Period",
        'layers': "🎨 Chart Layers",
        'layer_sma': "SMA (Moving Averages)",
        'layer_bollinger': "Bollinger Bands",
        'layer_signals': "AI Signals",
        'developer_title': "👨‍💻 Developer: Emirhan",
        'developer_desc': "Designed with the vision of 'Future Finance Interface'.",
        'loading': "Pulling Data from Cyberspace...",
        'error_data': "Data not found or invalid symbol.",
        'error_sys': "System Error:",
        'tab_tech': "📊 Technical Universe",
        'tab_fund': "🏢 Company Core",
        'tab_news': "📰 News Flow",
        'rsi_label': "RSI (Momentum)",
        'rsi_overbought': "Overbought 🔥",
        'rsi_oversold': "Oversold 🧊",
        'rsi_neutral': "Neutral 😐",
        'stoch_label': "Stochastic",
        'stoch_sell': "Sell Zone 🔻",
        'stoch_buy': "Buy Zone 🚀",
        'stoch_wait': "Wait ✋",
        'bb_label': "Bollinger Status",
        'bb_expensive': "Expensive ⚠️",
        'bb_cheap': "Cheap 🟢",
        'bb_normal': "Normal Band 👌",
        'trend_label': "Main Trend",
        'trend_up': "Bullish 🐂",
        'trend_down': "Bearish 🐻",
        'pe_ratio': "P/E Ratio",
        'market_cap': "Market Cap",
        'sector': "Sector",
        'profile_title': "🏢 Company Profile",
        'no_data': "No Data",
        'buy_signal': "BUY",
        'sell_signal': "SELL"
    }
}

# --- 2. AYARLAR & CYBERPUNK TASARIM (CSS BÜYÜSÜ) ---
st.set_page_config(page_title="KoçFin Neon", layout="wide", page_icon="⚡")

st.markdown("""
<style>
    /* Google Font: Fütüristik bir font seçelim */
    @import url('https://fonts.googleapis.com/css2?family=Rajdhani:wght@400;600;700&display=swap');
    
    /* GENEL ATMOSFER (Karanlık Mod) */
    .stApp {
        background-color: #0a0e17; /* Derin Uzay Siyahı */
        font-family: 'Rajdhani', sans-serif;
    }
    
    /* SIDEBAR TASARIMI */
    [data-testid="stSidebar"] {
        background-color: #111927; /* Sidebar daha koyu */
        border-right: 1px solid #1f2937;
    }
    [data-testid="stSidebar"] h1, [data-testid="stSidebar"] h2, [data-testid="stSidebar"] h3 {
        color: #FFD700; /* Koç Sarısı/Altını */
        text-shadow: 0 0 10px rgba(255, 215, 0, 0.5); /* Neon Parlama */
    }
    
    /* GLASSMORPHISM KARTLAR (Cam Efekti) */
    .metric-card {
        background: rgba(255, 255, 255, 0.05); /* Şeffaf Beyaz */
        backdrop-filter: blur(10px); /* Buzlu Cam Efekti */
        border-radius: 16px;
        padding: 20px;
        border: 1px solid rgba(255, 255, 255, 0.1); /* İnce parlak kenarlık */
        box-shadow: 0 8px 32px 0 rgba(0, 0, 0, 0.37);
        text-align: center;
        transition: transform 0.3s, border 0.3s;
    }
    .metric-card:hover {
        transform: translateY(-5px);
        border: 1px solid rgba(255, 215, 0, 0.5); /* Hover'da sarı parlama */
    }
    
    /* METİNLER VE RENKLER */
    .metric-value { 
        font-size: 32px; 
        font-weight: 700; 
        color: #ffffff; 
        letter-spacing: 1px;
    }
    .metric-label { 
        font-size: 14px; 
        color: #a0aec0; /* Mat Gri */
        text-transform: uppercase; 
        letter-spacing: 2px; 
        margin-bottom: 8px;
    }
    
    /* Neon Renk Sınıfları */
    .neon-green { color: #00ff7f; text-shadow: 0 0 12px rgba(0, 255, 127, 0.6); }
    .neon-red { color: #ff4757; text-shadow: 0 0 12px rgba(255, 71, 87, 0.6); }
    .neon-blue { color: #00d2d3; text-shadow: 0 0 12px rgba(0, 210, 211, 0.6); }
    .neon-gold { color: #FFD700; text-shadow: 0 0 12px rgba(255, 215, 0, 0.6); }

    /* TAB (SEKME) TASARIMI */
    .stTabs [data-baseweb="tab-list"] button {
        background-color: transparent;
        color: #a0aec0;
        border-radius: 8px;
        border: 1px solid transparent;
        transition: all 0.3s;
    }
    .stTabs [data-baseweb="tab-list"] button[aria-selected="true"] {
        background-color: rgba(255, 215, 0, 0.1) !important;
        color: #FFD700 !important;
        border: 1px solid #FFD700 !important;
        box-shadow: 0 0 15px rgba(255, 215, 0, 0.3);
    }

    /* BİLGİ KUTUSU VE HABERLER */
    .info-box, .news-card {
        background: rgba(255, 255, 255, 0.03);
        border: 1px solid rgba(255, 255, 255, 0.1);
        color: #e2e8f0;
        padding: 20px;
        border-radius: 12px;
    }
    .news-card:hover {
        border-left: 4px solid #FFD700;
        background: rgba(255, 255, 255, 0.07);
    }
    a { color: #FFD700 !important; text-decoration: none; }

</style>
""", unsafe_allow_html=True)

# --- 3. FONKSİYONLAR (Aynı Kalıyor) ---
@st.cache_data
def metni_cevir(text, target_lang):
    if not text: return ""
    if target_lang == 'en': return text
    try:
        return GoogleTranslator(source='auto', target='tr').translate(text)
    except:
        return text

def get_company_info(symbol):
    try:
        ticker = yf.Ticker(symbol)
        return ticker.info
    except:
        return None

def duzelt_bolunme_hatasi(df, sembol_adi):
    if not sembol_adi.endswith(".IS"): return df
    df = df.copy()
    df['Degisim'] = df['Close'].pct_change()
    anormal_dusisler = df[df['Degisim'] < -0.15]
    if not anormal_dusisler.empty:
        for tarih in anormal_dusisler.index:
            fiyat_once = df.loc[:tarih]['Close'].iloc[-2]
            fiyat_sonra = df.loc[tarih]['Close']
            katsayi = fiyat_once / fiyat_sonra
            mask = df.index < tarih
            df.loc[mask, ['Open', 'High', 'Low', 'Close']] /= katsayi
    return df

def get_smart_news(ticker_symbol, lang_code):
    query = ticker_symbol
    try:
        ticker = yf.Ticker(ticker_symbol)
        info = ticker.info
        raw_name = info.get('shortName') or info.get('longName')
        if raw_name:
            query = raw_name.replace("Inc.", "").replace("Corp.", "").replace("A.S.", "").strip()
        encoded_query = urllib.parse.quote(f"{query} finance")
        if lang_code == 'tr':
            url = f"https://news.google.com/rss/search?q={encoded_query}+when:7d&hl=tr&gl=TR&ceid=TR:tr"
        else:
            url = f"https://news.google.com/rss/search?q={encoded_query}+when:7d&hl=en-US&gl=US&ceid=US:en"
        feed = feedparser.parse(url)
        return feed.entries[:6], query if len(feed.entries) > 0 else ([], query)
    except:
        return [], ticker_symbol

def teknik_indikatorleri_hesapla(df):
    delta = df['Close'].diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
    rs = gain / loss
    df['RSI'] = 100 - (100 / (1 + rs))
    df['SMA_20'] = df['Close'].rolling(window=20).mean()
    df['SMA_50'] = df['Close'].rolling(window=50).mean()
    std = df['Close'].rolling(window=20).std()
    df['Bollinger_Upper'] = df['SMA_20'] + (std * 2)
    df['Bollinger_Lower'] = df['SMA_20'] - (std * 2)
    exp1 = df['Close'].ewm(span=12, adjust=False).mean()
    exp2 = df['Close'].ewm(span=26, adjust=False).mean()
    df['MACD'] = exp1 - exp2
    df['Signal_Line'] = df['MACD'].ewm(span=9, adjust=False).mean()
    low_14 = df['Low'].rolling(window=14).min()
    high_14 = df['High'].rolling(window=14).max()
    df['Stoch_K'] = 100 * ((df['Close'] - low_14) / (high_14 - low_14))
    return df

def al_sat_sinyalleri_yakala(df, lang_texts):
    sinyaller = []
    for i in range(1, len(df)):
        sma_al = df['SMA_20'].iloc[i] > df['SMA_50'].iloc[i] and df['SMA_20'].iloc[i-1] < df['SMA_50'].iloc[i-1]
        sma_sat = df['SMA_20'].iloc[i] < df['SMA_50'].iloc[i] and df['SMA_20'].iloc[i-1] > df['SMA_50'].iloc[i-1]
        tarih = df.index[i]
        fiyat = df['Close'].iloc[i]
        if sma_al: sinyaller.append((tarih, fiyat, lang_texts['buy_signal']))
        elif sma_sat: sinyaller.append((tarih, fiyat, lang_texts['sell_signal']))
    return sinyaller

# --- 4. ANA UYGULAMA (YENİ TASARIMLA) ---

dil_secimi = st.sidebar.radio("🌐 Language / Dil", ["Türkçe", "English"])
lang = 'tr' if dil_secimi == "Türkçe" else 'en'
t = TEXTS[lang]

st.sidebar.markdown(f"### ⚡ {t['sidebar_title']}")
sembol = st.sidebar.text_input(t['symbol_input'], "THYAO.IS")
periyot = st.sidebar.select_slider(t['period_input'], options=["3mo", "6mo", "1y", "2y", "5y"], value="1y")

st.sidebar.markdown(f"### {t['layers']}")
goster_sma = st.sidebar.checkbox(t['layer_sma'], value=True)
goster_bollinger = st.sidebar.checkbox(t['layer_bollinger'], value=True)
goster_sinyaller = st.sidebar.checkbox(t['layer_signals'], value=True)

st.sidebar.markdown("---")
st.sidebar.info(f"{t['developer_title']}\n\n{t['developer_desc']}")

if sembol:
    try:
        with st.spinner(t['loading']):
            df = yf.download(sembol, period=periyot, auto_adjust=False)
            sirket_bilgisi = get_company_info(sembol)
            haberler, sirket_adi = get_smart_news(sembol, lang)

        if df.empty:
            st.error(t['error_data'])
        else:
            if isinstance(df.columns, pd.MultiIndex): df.columns = df.columns.get_level_values(0)
            df = duzelt_bolunme_hatasi(df, sembol)
            df = teknik_indikatorleri_hesapla(df)
            
            current_price = df['Close'].iloc[-1]
            prev_price = df['Close'].iloc[0]
            delta = ((current_price - prev_price) / prev_price) * 100
            
            # Ana Başlık için Neon Efektler
            neon_class = "neon-green" if delta > 0 else "neon-red"
            icon = "▲" if delta > 0 else "▼"
            
            st.markdown(f"<h2 style='color:#FFD700; text-shadow: 0 0 10px rgba(255,215,0,0.3);'>{sirket_adi}</h2>", unsafe_allow_html=True)
            st.markdown(f"<h1 class='{neon_class}' style='font-size:50px; font-weight:bold; margin-top:-20px'>{current_price:.2f} <span style='font-size:24px'>{icon} %{delta:.2f}</span></h1>", unsafe_allow_html=True)

            tab1, tab2, tab3 = st.tabs([t['tab_tech'], t['tab_fund'], t['tab_news']])

            with tab1:
                c1, c2, c3, c4 = st.columns(4)
                
                # RSI
                rsi_val = df['RSI'].iloc[-1]
                rsi_durum = t['rsi_neutral']
                rsi_color = "neon-blue"
                if rsi_val > 70: rsi_durum = t['rsi_overbought']; rsi_color = "neon-red"
                elif rsi_val < 30: rsi_durum = t['rsi_oversold']; rsi_color = "neon-green"
                c1.markdown(f"<div class='metric-card'><div class='metric-label'>{t['rsi_label']}</div><div class='metric-value {rsi_color}'>{rsi_val:.0f}</div><div style='font-size:12px; color:#a0aec0; margin-top:5px'>{rsi_durum}</div></div>", unsafe_allow_html=True)
                
                # Stokastik
                stoch_k = df['Stoch_K'].iloc[-1]
                stoch_durum = t['stoch_wait']
                stoch_color = "neon-blue"
                if stoch_k > 80: stoch_durum = t['stoch_sell']; stoch_color = "neon-red"
                elif stoch_k < 20: stoch_durum = t['stoch_buy']; stoch_color = "neon-green"
                c2.markdown(f"<div class='metric-card'><div class='metric-label'>{t['stoch_label']}</div><div class='metric-value {stoch_color}'>{stoch_k:.0f}</div><div style='font-size:12px; color:#a0aec0; margin-top:5px'>{stoch_durum}</div></div>", unsafe_allow_html=True)
                
                # Bollinger
                fiyat = df['Close'].iloc[-1]
                bb_upper = df['Bollinger_Upper'].iloc[-1]
                bb_durum = t['bb_normal']
                bb_color = "neon-blue"
                if fiyat > bb_upper: bb_durum = t['bb_expensive']; bb_color = "neon-red"
                c3.markdown(f"<div class='metric-card'><div class='metric-label'>{t['bb_label']}</div><div class='metric-value {bb_color}'>{fiyat:.2f}</div><div style='font-size:12px; color:#a0aec0; margin-top:5px'>{bb_durum}</div></div>", unsafe_allow_html=True)
                
                # Trend
                macd = df['MACD'].iloc[-1]
                signal = df['Signal_Line'].iloc[-1]
                macd_durum = t['trend_up'] if macd > signal else t['trend_down']
                macd_color = "neon-green" if macd > signal else "neon-red"
                c4.markdown(f"<div class='metric-card'><div class='metric-label'>{t['trend_label']}</div><div class='metric-value {macd_color}' style='font-size:24px'>{macd_durum}</div></div>", unsafe_allow_html=True)

                st.markdown("###")
                
                # GRAFİK (KARANLIK MODA UYGUN)
                fig = go.Figure()
                # Mumları Karanlık Moda Uyarlayalım
                fig.add_trace(go.Candlestick(x=df.index, open=df['Open'], high=df['High'], low=df['Low'], close=df['Close'],
                                             name='Fiyat', increasing_line_color='#00ff7f', decreasing_line_color='#ff4757'))
                
                if goster_bollinger:
                    fig.add_trace(go.Scatter(x=df.index, y=df['Bollinger_Upper'], line=dict(color='rgba(0, 210, 211, 0.3)', width=1), name='Upper', showlegend=False))
                    fig.add_trace(go.Scatter(x=df.index, y=df['Bollinger_Lower'], line=dict(color='rgba(0, 210, 211, 0.3)', width=1), fill='tonexty', fillcolor='rgba(0, 210, 211, 0.05)', name='Lower', showlegend=False))
                
                if goster_sma:
                    fig.add_trace(go.Scatter(x=df.index, y=df['SMA_20'], line=dict(color='#FFD700', width=1.5), name='SMA 20 (Altın)'))
                    fig.add_trace(go.Scatter(x=df.index, y=df['SMA_50'], line=dict(color='#00d2d3', width=1.5), name='SMA 50 (Siyan)'))

                if goster_sinyaller:
                    sinyaller = al_sat_sinyalleri_yakala(df, t)
                    for tarih, fiyat, tip in sinyaller:
                        color = '#00ff7f' if tip == t['buy_signal'] else '#ff4757'
                        ay_val = 40 if tip == t['buy_signal'] else -40
                        fig.add_annotation(x=tarih, y=fiyat, text=tip, showarrow=True, arrowhead=2, arrowcolor=color, ay=ay_val, bgcolor=color, font=dict(color="#0a0e17", size=10))

                # Grafik Arka Planını Şeffaf ve Karanlık Yapma
                fig.update_layout(height=600, xaxis_rangeslider_visible=False, 
                                  paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(255,255,255,0.02)', 
                                  margin=dict(l=0,r=0,t=30,b=0),
                                  font=dict(color='#a0aec0'),
                                  xaxis=dict(showgrid=True, gridcolor='rgba(255,255,255,0.05)'),
                                  yaxis=dict(showgrid=True, gridcolor='rgba(255,255,255,0.05)')
                                  )
                st.plotly_chart(fig, use_container_width=True)

            with tab2:
                if sirket_bilgisi:
                    c1, c2, c3 = st.columns(3)
                    fk = sirket_bilgisi.get('trailingPE', 'N/A')
                    fk_val = f"{fk:.2f}" if isinstance(fk, (int, float)) else t['no_data']
                    c1.markdown(f"<div class='metric-card'><div class='metric-label'>{t['pe_ratio']}</div><div class='metric-value neon-gold'>{fk_val}</div></div>", unsafe_allow_html=True)
                    
                    mcap = sirket_bilgisi.get('marketCap', 0)
                    if mcap > 1_000_000_000: mcap_str = f"{mcap/1_000_000_000:.1f} Mr"
                    else: mcap_str = f"{mcap/1_000_000:.1f} Mn"
                    c2.markdown(f"<div class='metric-card'><div class='metric-label'>{t['market_cap']}</div><div class='metric-value neon-blue'>{mcap_str}</div></div>", unsafe_allow_html=True)
                    
                    raw_sektor = sirket_bilgisi.get('sector', 'Bilinmiyor')
                    sektor_tr = metni_cevir(raw_sektor, lang)
                    c3.markdown(f"<div class='metric-card'><div class='metric-label'>{t['sector']}</div><div class='metric-value' style='font-size:20px'>{sektor_tr}</div></div>", unsafe_allow_html=True)
                    
                    raw_ozet = sirket_bilgisi.get('longBusinessSummary', t['no_data'])
                    ozet_tr = metni_cevir(raw_ozet[:800], lang)
                    st.markdown("###")
                    st.markdown(f"<div class='info-box'><h4 style='color:#FFD700'>{t['profile_title']}</h4><p>{ozet_tr}...</p></div>", unsafe_allow_html=True)
                else:
                    st.warning(t['error_data'])

            with tab3:
                for haber in haberler:
                    st.markdown(f"<div class='news-card'><a href='{haber.link}' target='_blank' style='font-size:16px; font-weight:bold'>{haber.title}</a><div style='font-size:12px; color:#a0aec0; margin-top:8px'>🗓️ {haber.published[:16]}</div></div>", unsafe_allow_html=True)

    except Exception as e:
        st.error(f"{t['error_sys']} {e}")