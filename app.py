import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go
import feedparser
import urllib.parse
import numpy as np 

# --- 1. AYARLAR & TASARIM ---
st.set_page_config(page_title="KoçFin Serenity", layout="wide", page_icon="☕")

st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Poppins:wght@300;400;600&display=swap');
    html, body, [class*="css"] { font-family: 'Poppins', sans-serif; color: #4a4a4a; }
    .stApp { background-color: #fcfbf4; }
    [data-testid="stSidebar"] { background-color: #f7f1e3; border-right: 1px solid #e1dcd5; }
    .metric-card { background-color: #ffffff; border-radius: 16px; padding: 20px; border: 1px solid #f0eee6; box-shadow: 0 4px 20px rgba(0,0,0,0.03); text-align: center; transition: transform 0.2s ease; }
    .metric-card:hover { transform: translateY(-3px); }
    .metric-value { font-size: 28px; font-weight: 600; color: #2c3e50; }
    .color-up { color: #27ae60; }
    .color-down { color: #c0392b; }
    .color-neutral { color: #d35400; }
    .news-card { background-color: #ffffff; padding: 15px; border-radius: 12px; margin-bottom: 15px; border-left: 5px solid #ffda79; transition: all 0.2s; }
    .news-card:hover { border-left: 5px solid #ffb142; background-color: #faf9f6; }
    a { text-decoration: none !important; color: inherit; }
</style>
""", unsafe_allow_html=True)

# --- 2. SENIOR MÜHENDİSLİK FONKSİYONLARI ---

def duzelt_bolunme_hatasi(df, sembol_adi):
    """
    BU FONKSİYON SADECE BIST (.IS) İÇİN ÇALIŞIR!
    Kripto veya ABD borsasında %20 düşüş normal olabilir, onlara dokunmuyoruz.
    """
    # 1. KONTROL KAPISI: Sembol '.IS' ile bitmiyor mu? O zaman dokunma, geri dön.
    if not sembol_adi.endswith(".IS"):
        return df

    # --- Sadece Türk Hisseleri İçin Burası Çalışır ---
    df = df.copy()
    df['Degisim'] = df['Close'].pct_change()
    
    # BIST'te %15'ten büyük düşüş teknik olarak "Taban" kuralına aykırıdır.
    # Bu yüzden bunu bölünme kabul ediyoruz.
    anormal_dusisler = df[df['Degisim'] < -0.15]
    
    if not anormal_dusisler.empty:
        for tarih in anormal_dusisler.index:
            fiyat_once = df.loc[:tarih]['Close'].iloc[-2]
            fiyat_sonra = df.loc[tarih]['Close']
            bolme_katsayisi = fiyat_once / fiyat_sonra
            
            mask = df.index < tarih
            df.loc[mask, ['Open', 'High', 'Low', 'Close']] /= bolme_katsayisi
            
            print(f"BIST Bölünme Düzeltmesi ({sembol_adi}): {tarih.date()} - Katsayı: {bolme_katsayisi:.2f}")
            
    return df

def get_smart_news(ticker_symbol):
    query = ticker_symbol
    try:
        ticker = yf.Ticker(ticker_symbol)
        info = ticker.info
        raw_name = info.get('shortName') or info.get('longName')
        if raw_name:
            query = raw_name.replace("Inc.", "").replace("Corp.", "").replace("A.S.", "").strip()
        encoded_query = urllib.parse.quote(f"{query} finance")
        url_7d = f"https://news.google.com/rss/search?q={encoded_query}+when:7d&hl=tr&gl=TR&ceid=TR:tr"
        feed = feedparser.parse(url_7d)
        if len(feed.entries) > 0:
            return feed.entries[:6], query, "Son 7 Gün"
        url_gen = f"https://news.google.com/rss/search?q={encoded_query}&hl=tr&gl=TR&ceid=TR:tr"
        feed_gen = feedparser.parse(url_gen)
        return feed_gen.entries[:6], query, "Genel Gündem"
    except:
        return [], ticker_symbol, "Hata"

def hesapla_rsi(data, window=14):
    delta = data.diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=window).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=window).mean()
    rs = gain / loss
    return 100 - (100 / (1 + rs))

def sinyal_uret(df):
    son_rsi = df['RSI'].iloc[-1]
    son_sma20 = df['SMA_20'].iloc[-1]
    son_sma50 = df['SMA_50'].iloc[-1]
    sinyal = "PİYASA SAKİN ☕"
    renk_class = "metric-value" 
    if son_sma20 > son_sma50:
        sinyal = "YÜKSELİŞ TRENDİ 🌿"
        renk_class = "color-up"
    elif son_sma20 < son_sma50:
        sinyal = "DÜŞÜŞ TRENDİ 🍂"
        renk_class = "color-down"
    return sinyal, renk_class

# --- 3. ARAYÜZ ---
st.markdown("<h2 style='text-align: center; color: #2c3e50; font-weight: 600;'>KoçFin <span style='color:#ffb142'>Serenity</span></h2>", unsafe_allow_html=True)
st.markdown("---")

# Sidebar
st.sidebar.markdown("### 🍂 Panel")
sembol = st.sidebar.text_input("Varlık Ara", "KONTR.IS")
periyot = st.sidebar.select_slider("Zaman Dilimi", options=["1mo", "3mo", "6mo", "1y", "2y", "5y"], value="1y")
st.sidebar.info("💡 İpucu: BIST hisseleri için sonuna .IS ekleyin (Örn: GARAN.IS)")
st.sidebar.markdown("---")
st.sidebar.markdown("### 👨‍💻 Geliştirici: Emirhan")
st.sidebar.info("""
Bu proje, **Koç Üniversitesi** vizyonuyla; finansal veriyi demokratikleştirmek ve 
küçük yatırımcıyı 'Bölünme Tuzaklarından' korumak için geliştirilmiştir.
""")
st.sidebar.caption("© 2026 KoçFin Serenity - v1.0")

if sembol:
    try:
        with st.spinner('Piyasa verileri işleniyor...'):
            # Yahoo'dan ham veriyi çek (Auto adjust kapalı, kontrol bizde)
            df = yf.download(sembol, period=periyot, auto_adjust=False) 
            haberler, isim, mod = get_smart_news(sembol)
        
        if df.empty:
            st.warning("Veri bulunamadı.")
        else:
            if isinstance(df.columns, pd.MultiIndex):
                df.columns = df.columns.get_level_values(0)

            # --- AKILLI DÜZELTME MOTORU ---
            # Sembolü de gönderiyoruz ki kontrol etsin (.IS mi diye)
            df = duzelt_bolunme_hatasi(df, sembol)
            # -----------------------------

            df['SMA_20'] = df['Close'].rolling(window=20).mean()
            df['SMA_50'] = df['Close'].rolling(window=50).mean()
            df['RSI'] = hesapla_rsi(df['Close'])
            sinyal_text, sinyal_renk_class = sinyal_uret(df)

            # Metrikler
            son_fiyat = df['Close'].iloc[-1]
            ilk_fiyat = df['Close'].iloc[0]
            degisim = son_fiyat - ilk_fiyat
            yuzde = (degisim / ilk_fiyat) * 100
            
            delta_class = "color-up" if degisim > 0 else "color-down"
            delta_icon = "▲" if degisim > 0 else "▼"

            col1, col2, col3, col4 = st.columns(4)
            with col1:
                st.markdown(f"""
                <div class="metric-card">
                    <div style="font-size:12px; color:#aaa;">Son Fiyat</div>
                    <div class="metric-value">{son_fiyat:.2f}</div>
                    <div class="{delta_class}" style="font-size: 14px; font-weight:bold;">{delta_icon} %{yuzde:.2f}</div>
                </div>
                """, unsafe_allow_html=True)
            with col2:
                st.markdown(f"""
                <div class="metric-card">
                    <div style="font-size:12px; color:#aaa;">RSI</div>
                    <div class="metric-value">{df['RSI'].iloc[-1]:.0f}</div>
                </div>
                """, unsafe_allow_html=True)
            with col3:
                st.markdown(f"""
                <div class="metric-card">
                    <div style="font-size:12px; color:#aaa;">AI Sinyali</div>
                    <div class="{sinyal_renk_class}" style="font-size: 18px; font-weight:600;">{sinyal_text}</div>
                </div>
                """, unsafe_allow_html=True)
            with col4:
                st.markdown(f"""
                <div class="metric-card">
                    <div style="font-size:12px; color:#aaa;">Zirve</div>
                    <div class="metric-value">{df['High'].max():.2f}</div>
                </div>
                """, unsafe_allow_html=True)

            # Grafik
            st.markdown("###") 
            fig = go.Figure()
            fig.add_trace(go.Candlestick(x=df.index, open=df['Open'], high=df['High'], low=df['Low'], close=df['Close'], name='Fiyat', increasing_line_color='#27ae60', decreasing_line_color='#c0392b'))
            fig.add_trace(go.Scatter(x=df.index, y=df['SMA_20'], line=dict(color='#3498db', width=2), name='SMA 20'))
            fig.add_trace(go.Scatter(x=df.index, y=df['SMA_50'], line=dict(color='#e67e22', width=2), name='SMA 50'))
            fig.update_layout(height=500, paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', font=dict(color='#57606f'), xaxis=dict(showgrid=False), yaxis=dict(showgrid=True, gridcolor='#ecf0f1'), margin=dict(l=0, r=0, t=30, b=0), hovermode='x unified')
            st.plotly_chart(fig, use_container_width=True)

            # Haberler
            st.markdown(f"#### 🗞️ {isim} Gündem ({mod})")
            col_news1, col_news2 = st.columns(2)
            for i, haber in enumerate(haberler):
                target_col = col_news1 if i % 2 == 0 else col_news2
                with target_col:
                    st.markdown(f"""
                    <a href="{haber.link}" target="_blank">
                        <div class="news-card">
                            <div style="font-weight:600; color:#2c3e50;">{haber.title}</div>
                            <div style="font-size:11px; color:#aaa; margin-top:5px;">🗓️ {haber.published[:16]}</div>
                        </div>
                    </a>
                    """, unsafe_allow_html=True)
      
    
    except Exception as e:
        st.error(f"Hata: {e}")