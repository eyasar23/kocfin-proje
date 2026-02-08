from deep_translator import GoogleTranslator
import streamlit as st

# --- ÇEVİRİ MOTORU ---
@st.cache_data
def metni_cevir(text, target_lang):
    if not text: return ""
    if target_lang == 'en': return text
    try:
        return GoogleTranslator(source='auto', target='tr').translate(text)
    except:
        return text

# --- DİL SÖZLÜĞÜ (TEXTS) ---
TEXTS = {
    'tr': {
        'title': "KoçFin Pro",
        'sidebar_title': "KoçFin Terminal",
        'lang_select': "Dil / Language",
        'symbol_input': "Varlık Sembolü",
        'period_input': "Zaman Aralığı",
        'layers': "🎨 Grafik Katmanları",
        'layer_sma': "SMA (Ortalamalar)",
        'layer_bollinger': "Bollinger Bantları",
        'layer_signals': "AI Sinyalleri",
        'developer_title': "👨‍💻 Geliştirici: Emirhan",
        'developer_desc': "'Premium Dark' Vizyonuyla Tasarlanmıştır.",
        'loading': "Piyasa Verileri İşleniyor...",
        'error_data': "Veri bulunamadı veya sembol hatalı.",
        'error_sys': "Sistem Hatası:",
        'tab_tech': "📊 Teknik Analiz",
        'tab_fund': "🏢 Temel Veriler",
        'tab_news': "📰 Haberler",
        'rsi_label': "RSI Gücü",
        'rsi_overbought': "Aşırı Alım",
        'rsi_oversold': "Aşırı Satım",
        'rsi_neutral': "Nötr",
        'stoch_label': "Stokastik",
        'stoch_sell': "Satış Bölgesi",
        'stoch_buy': "Alış Bölgesi",
        'stoch_wait': "Bekle",
        'bb_label': "Bollinger",
        'bb_expensive': "Pahalı",
        'bb_cheap': "Ucuz",
        'bb_normal': "Normal",
        'trend_label': "Trend",
        'trend_up': "Yükseliş",
        'trend_down': "Düşüş",
        'pe_ratio': "F/K Oranı",
        'market_cap': "Piyasa Değeri",
        'sector': "Sektör",
        'profile_title': "🏢 Şirket Profili",
        'no_data': "Veri Yok",
        'buy_signal': "AL",
        'sell_signal': "SAT"
    },
    'en': {
        'title': "KocFin Pro",
        'sidebar_title': "KocFin Terminal",
        'lang_select': "Language / Dil",
        'symbol_input': "Asset Symbol",
        'period_input': "Time Period",
        'layers': "🎨 Chart Layers",
        'layer_sma': "SMA (Moving Averages)",
        'layer_bollinger': "Bollinger Bands",
        'layer_signals': "AI Signals",
        'developer_title': "👨‍💻 Developer: Emirhan",
        'developer_desc': "Designed with 'Premium Dark' Vision.",
        'loading': "Processing Market Data...",
        'error_data': "Data not found or invalid symbol.",
        'error_sys': "System Error:",
        'tab_tech': "📊 Technical Analysis",
        'tab_fund': "🏢 Fundamentals",
        'tab_news': "📰 News",
        'rsi_label': "RSI Power",
        'rsi_overbought': "Overbought",
        'rsi_oversold': "Oversold",
        'rsi_neutral': "Neutral",
        'stoch_label': "Stochastic",
        'stoch_sell': "Sell Zone",
        'stoch_buy': "Buy Zone",
        'stoch_wait': "Wait",
        'bb_label': "Bollinger",
        'bb_expensive': "Expensive",
        'bb_cheap': "Cheap",
        'bb_normal': "Normal",
        'trend_label': "Trend",
        'trend_up': "Bullish",
        'trend_down': "Bearish",
        'pe_ratio': "P/E Ratio",
        'market_cap': "Market Cap",
        'sector': "Sector",
        'profile_title': "🏢 Company Profile",
        'no_data': "No Data",
        'buy_signal': "BUY",
        'sell_signal': "SELL"
    }
} 