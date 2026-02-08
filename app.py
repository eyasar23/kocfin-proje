import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go
import feedparser
import urllib.parse

# --- 1. AYARLAR & TASARIM (Minimalist & Derin) ---
st.set_page_config(page_title="KoçFin Pro", layout="wide", page_icon="🏛️")

st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;600&display=swap');
    html, body, [class*="css"] { font-family: 'Inter', sans-serif; color: #2c3e50; }
    .stApp { background-color: #f8f9fa; } /* Çok açık gri (Business White) */
    
    /* Sekme Tasarımı */
    .stTabs [data-baseweb="tab-list"] { gap: 20px; }
    .stTabs [data-baseweb="tab"] {
        height: 50px;
        white-space: pre-wrap;
        background-color: #fff;
        border-radius: 10px;
        color: #636e72;
        box-shadow: 0 2px 5px rgba(0,0,0,0.05);
    }
    .stTabs [aria-selected="true"] {
        background-color: #2c3e50;
        color: #fff;
    }

    /* Kart Tasarımları */
    .metric-card {
        background-color: #ffffff;
        border-radius: 12px;
        padding: 20px;
        border: 1px solid #e9ecef;
        box-shadow: 0 4px 15px rgba(0,0,0,0.03);
        text-align: center;
    }
    .metric-value { font-size: 26px; font-weight: 700; color: #2d3436; }
    .metric-label { font-size: 12px; color: #b2bec3; text-transform: uppercase; letter-spacing: 1px; }
    
    /* Temel Analiz Kutusu */
    .info-box {
        background-color: #fff;
        padding: 20px;
        border-radius: 10px;
        border-left: 5px solid #0984e3;
        margin-bottom: 20px;
        box-shadow: 0 2px 10px rgba(0,0,0,0.03);
    }
    
    /* Renkler */
    .up { color: #00b894; }
    .down { color: #d63031; }

</style>
""", unsafe_allow_html=True)

# --- 2. GÜÇLENDİRİLMİŞ FONKSİYONLAR ---

def get_company_info(symbol):
    """Şirketin temel verilerini (F/K, Piyasa Değeri, Açıklama) çeker."""
    try:
        ticker = yf.Ticker(symbol)
        info = ticker.info
        return info
    except:
        return None

def duzelt_bolunme_hatasi(df, sembol_adi):
    """BIST hisselerindeki bölünme hatalarını tespit eder ve düzeltir."""
    if not sembol_adi.endswith(".IS"): return df
    df = df.copy()
    df['Degisim'] = df['Close'].pct_change()
    anormal_dusisler = df[df['Degisim'] < -0.15] # %15 altı düşüşleri yakala
    if not anormal_dusisler.empty:
        for tarih in anormal_dusisler.index:
            fiyat_once = df.loc[:tarih]['Close'].iloc[-2]
            fiyat_sonra = df.loc[tarih]['Close']
            katsayi = fiyat_once / fiyat_sonra
            mask = df.index < tarih
            df.loc[mask, ['Open', 'High', 'Low', 'Close']] /= katsayi
    return df

def get_smart_news(ticker_symbol):
    # (Eski haber fonksiyonumuz aynen kalıyor, gayet iyi çalışıyor)
    query = ticker_symbol
    try:
        ticker = yf.Ticker(ticker_symbol)
        info = ticker.info
        raw_name = info.get('shortName') or info.get('longName')
        if raw_name:
            query = raw_name.replace("Inc.", "").replace("Corp.", "").replace("A.S.", "").strip()
        encoded_query = urllib.parse.quote(f"{query} finance")
        url = f"https://news.google.com/rss/search?q={encoded_query}+when:7d&hl=tr&gl=TR&ceid=TR:tr"
        feed = feedparser.parse(url)
        return feed.entries[:6], query if len(feed.entries) > 0 else ([], query)
    except:
        return [], ticker_symbol

def hesapla_rsi(data, window=14):
    delta = data.diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=window).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=window).mean()
    rs = gain / loss
    return 100 - (100 / (1 + rs))

# --- 3. ANA UYGULAMA MİMARİSİ ---

st.sidebar.markdown("### 🏛️ KoçFin Terminal")
sembol = st.sidebar.text_input("Varlık Sembolü", "THYAO.IS")
periyot = st.sidebar.select_slider("Zaman Aralığı", options=["1mo", "3mo", "6mo", "1y", "2y", "5y"], value="1y")

# Geliştirici İmzası
st.sidebar.markdown("---")
st.sidebar.info("👨‍💻 **Geliştirici:** Emirhan\n\nKoç Üniversitesi vizyonuyla, veri demokrasisi için tasarlanmıştır.")

if sembol:
    try:
        # Verileri Paralel Çekiyoruz (Daha Hızlı)
        with st.spinner('Piyasa ve Şirket İstihbaratı Toplanıyor...'):
            df = yf.download(sembol, period=periyot, auto_adjust=False)
            sirket_bilgisi = get_company_info(sembol)
            haberler, sirket_adi = get_smart_news(sembol)

        if df.empty:
            st.error("Veri bulunamadı.")
        else:
            # Veri İşleme
            if isinstance(df.columns, pd.MultiIndex): df.columns = df.columns.get_level_values(0)
            df = duzelt_bolunme_hatasi(df, sembol)
            
            # İndikatörler
            df['SMA_20'] = df['Close'].rolling(window=20).mean()
            df['SMA_50'] = df['Close'].rolling(window=50).mean()
            df['RSI'] = hesapla_rsi(df['Close'])
            
            # Başlık
            current_price = df['Close'].iloc[-1]
            prev_price = df['Close'].iloc[0] # Dönem başı
            delta = ((current_price - prev_price) / prev_price) * 100
            color_class = "up" if delta > 0 else "down"
            icon = "▲" if delta > 0 else "▼"
            
            st.markdown(f"## {sirket_adi} ({sembol.upper()})")
            st.markdown(f"<h3 class='{color_class}'>{current_price:.2f} {icon} %{delta:.2f} <span style='font-size:16px; color:#b2bec3'>({periyot})</span></h3>", unsafe_allow_html=True)

            # --- SEKMELİ YAPI (DERİN MİMARİ) ---
            tab1, tab2, tab3 = st.tabs(["📊 Teknik Analiz", "🏢 Şirket Profili (Temel)", "📰 Haber Merkezi"])

            # --- TAB 1: TEKNİK ANALİZ ---
            with tab1:
                col1, col2, col3 = st.columns(3)
                col1.markdown(f"<div class='metric-card'><div class='metric-label'>RSI (Güç)</div><div class='metric-value'>{df['RSI'].iloc[-1]:.0f}</div></div>", unsafe_allow_html=True)
                
                # Trend Sinyali Logic
                sma20, sma50 = df['SMA_20'].iloc[-1], df['SMA_50'].iloc[-1]
                trend = "YÜKSELİŞ 🐂" if sma20 > sma50 else "DÜŞÜŞ 🐻"
                col2.markdown(f"<div class='metric-card'><div class='metric-label'>Trend Durumu</div><div class='metric-value' style='font-size:22px'>{trend}</div></div>", unsafe_allow_html=True)
                
                col3.markdown(f"<div class='metric-card'><div class='metric-label'>Dönem Zirvesi</div><div class='metric-value'>{df['High'].max():.2f}</div></div>", unsafe_allow_html=True)

                st.markdown("###")
                fig = go.Figure()
                fig.add_trace(go.Candlestick(x=df.index, open=df['Open'], high=df['High'], low=df['Low'], close=df['Close'], name='Fiyat'))
                fig.add_trace(go.Scatter(x=df.index, y=df['SMA_20'], line=dict(color='#0984e3', width=2), name='SMA 20'))
                fig.add_trace(go.Scatter(x=df.index, y=df['SMA_50'], line=dict(color='#d63031', width=2), name='SMA 50'))
                fig.update_layout(height=500, xaxis_rangeslider_visible=False, template="plotly_white", margin=dict(l=0,r=0,t=0,b=0))
                st.plotly_chart(fig, use_container_width=True)

            # --- TAB 2: TEMEL ANALİZ (YENİ MODÜL) ---
            with tab2:
                if sirket_bilgisi:
                    c1, c2, c3 = st.columns(3)
                    
                    # F/K Oranı (Değerleme)
                    fk = sirket_bilgisi.get('trailingPE', 'N/A')
                    fk_val = f"{fk:.2f}" if isinstance(fk, (int, float)) else "Veri Yok"
                    c1.markdown(f"<div class='metric-card'><div class='metric-label'>F/K Oranı</div><div class='metric-value'>{fk_val}</div><div style='font-size:10px; color:#aaa'>Düşük = Ucuz Olabilir</div></div>", unsafe_allow_html=True)
                    
                    # Piyasa Değeri
                    mcap = sirket_bilgisi.get('marketCap', 0)
                    if mcap > 1_000_000_000: mcap_str = f"{mcap/1_000_000_000:.1f} Mr"
                    elif mcap > 1_000_000: mcap_str = f"{mcap/1_000_000:.1f} Mn"
                    else: mcap_str = "N/A"
                    c2.markdown(f"<div class='metric-card'><div class='metric-label'>Piyasa Değeri</div><div class='metric-value'>{mcap_str}</div></div>", unsafe_allow_html=True)
                    
                    # Sektör
                    sektor = sirket_bilgisi.get('sector', 'Bilinmiyor')
                    c3.markdown(f"<div class='metric-card'><div class='metric-label'>Sektör</div><div class='metric-value' style='font-size:18px'>{sektor}</div></div>", unsafe_allow_html=True)
                    
                    st.markdown("###")
                    st.markdown(f"""
                    <div class='info-box'>
                        <h4>🏢 Şirket Hakkında</h4>
                        <p>{sirket_bilgisi.get('longBusinessSummary', 'Açıklama bulunamadı.')[:500]}...</p>
                        <hr>
                        <small>📍 Merkez: {sirket_bilgisi.get('city', '-')} | 🌐 Web: <a href="{sirket_bilgisi.get('website', '#')}">{sirket_bilgisi.get('website', 'Yok')}</a></small>
                    </div>
                    """, unsafe_allow_html=True)
                else:
                    st.warning("Temel analiz verilerine ulaşılamadı.")

            # --- TAB 3: HABER MERKEZİ ---
            with tab3:
                for haber in haberler:
                    st.markdown(f"""
                    <div style='padding:15px; background:#fff; border-radius:10px; margin-bottom:10px; border-left:4px solid #fdcb6e; box-shadow:0 2px 5px rgba(0,0,0,0.05)'>
                        <a href="{haber.link}" target="_blank" style='text-decoration:none; color:#2d3436; font-weight:bold; font-size:16px'>{haber.title}</a>
                        <div style='font-size:12px; color:#b2bec3; margin-top:5px'>🗓️ {haber.published[:16]}</div>
                    </div>
                    """, unsafe_allow_html=True)

    except Exception as e:
        st.error(f"Sistem Hatası: {e}")