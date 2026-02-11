import yfinance as yf
import pandas as pd
import feedparser
import urllib.parse
import numpy as np

def akilli_veri_duzeltici(df):
    
    df = df.copy()
    df['Degisim'] = df['Close'].pct_change()
        
    anomaliler = df[df['Degisim'] < -0.40]
    
    if not anomaliler.empty:
        for tarih in anomaliler.index:
            fiyat_once = df['Close'].shift(1).loc[tarih]
            fiyat_sonra = df['Close'].loc[tarih]
            
            if fiyat_sonra > 0:
                bolunme_katsayisi = fiyat_once / fiyat_sonra
                
                
                en_yakin_tam_sayi = round(bolunme_katsayisi)
                hata_payi = abs(bolunme_katsayisi - en_yakin_tam_sayi)
                
                
                if hata_payi < 0.15 and en_yakin_tam_sayi >= 2:
                    mask = df.index < tarih
                    cols = ['Open', 'High', 'Low', 'Close']
                    
                    df.loc[mask, cols] = df.loc[mask, cols] / en_yakin_tam_sayi
                    
    if 'Degisim' in df.columns:
        df.drop(columns=['Degisim'], inplace=True)
    return df

def get_company_info(symbol):
    try:
        ticker = yf.Ticker(symbol)
        return ticker.info
    except:
        return None

def get_smart_news(ticker_symbol, lang_code):
    query = ticker_symbol
    haberler = []
    baslik = ticker_symbol.upper()
    try:
        ticker = yf.Ticker(ticker_symbol)
        info = ticker.info
        raw_name = info.get('shortName') or info.get('longName')
        if raw_name:
            baslik = raw_name.replace("Inc.", "").replace("Corp.", "").replace("A.S.", "").strip()
            query = baslik
        encoded_query = urllib.parse.quote(f"{query} finance")
        if lang_code == 'tr':
            url = f"https://news.google.com/rss/search?q={encoded_query}+when:7d&hl=tr&gl=TR&ceid=TR:tr"
        else:
            url = f"https://news.google.com/rss/search?q={encoded_query}+when:7d&hl=en-US&gl=US&ceid=US:en"
        feed = feedparser.parse(url)
        if feed.entries:
            haberler = feed.entries[:6]
    except:
        pass
    return haberler, baslik

def teknik_indikatorleri_hesapla(df):
   
    delta = df['Close'].diff()
    up = delta.clip(lower=0)
    down = -1 * delta.clip(upper=0)
    
   
    ma_up = up.ewm(com=13, adjust=False).mean()
    ma_down = down.ewm(com=13, adjust=False).mean()
    
    rs = ma_up / ma_down
    df['RSI'] = 100 - (100 / (1 + rs))
    
    df['SMA_20'] = df['Close'].rolling(window=20).mean()
    df['SMA_50'] = df['Close'].rolling(window=50).mean()
    df['EMA_100'] = df['Close'].ewm(span=100, adjust=False).mean()
    
    std = df['Close'].rolling(window=20).std()
    df['Bollinger_Upper'] = df['SMA_20'] + (std * 2)
    df['Bollinger_Lower'] = df['SMA_20'] - (std * 2)
    
    exp1 = df['Close'].ewm(span=12, adjust=False).mean()
    exp2 = df['Close'].ewm(span=26, adjust=False).mean()
    df['MACD'] = exp1 - exp2
    df['Signal_Line'] = df['MACD'].ewm(span=9, adjust=False).mean()
    
    low_14 = df['Low'].rolling(window=14).min()
    high_14 = df['High'].rolling(window=14).max()
    
    
    df['Stoch_K'] = 100 * ((df['Close'] - low_14) / ((high_14 - low_14) + 1e-9))
    
    return df

def al_sat_sinyalleri_yakala(df, lang_texts):
    sinyaller = []
    son_sinyal_turu = None 
    son_sinyal_zamani = 0  
    
    for i in range(1, len(df)):
        tarih = df.index[i]
        fiyat = df['Close'].iloc[i]
        rsi = df['RSI'].iloc[i]
       
        rsi_prev = df['RSI'].iloc[i-1] if i > 0 else 50 
        sinyal_tipi = None
        
        if rsi < 25 and rsi_prev >= 25:
            sinyal_tipi = lang_texts.get('dip_buy', '💎')
        elif rsi > 75 and rsi_prev <= 75:
            sinyal_tipi = lang_texts.get('peak_sell', '⛔')
        elif df['SMA_20'].iloc[i] > df['SMA_50'].iloc[i] and df['SMA_20'].iloc[i-1] < df['SMA_50'].iloc[i-1]:
            sinyal_tipi = lang_texts['buy_signal']
        elif df['SMA_20'].iloc[i] < df['SMA_50'].iloc[i] and df['SMA_20'].iloc[i-1] > df['SMA_50'].iloc[i-1]:
            sinyal_tipi = lang_texts['sell_signal']
            
        if sinyal_tipi:
            if (sinyal_tipi != son_sinyal_turu) or (i - son_sinyal_zamani > 15):
                sinyaller.append((tarih, fiyat, sinyal_tipi))
                son_sinyal_turu = sinyal_tipi
                son_sinyal_zamani = i
                
    return sinyaller

def hesapla_teknik_skor(df, t):
    base_score = 50.0
    score = base_score
    rapor = []
    
    if df.empty:
        return 0, []

    son = df.iloc[-1]
    
    
    rsi_val = son.get('RSI', 50)
    rsi_farki = 50 - rsi_val
    score += rsi_farki
    
    if rsi_val < 30:
        rapor.append({"msg": t['rpt_rsi_low'].format(rsi_val), "durum": "pozitif"})
    elif rsi_val > 70:
        rapor.append({"msg": t['rpt_rsi_high'].format(rsi_val), "durum": "negatif"})

    
    ust_bant = son.get('Bollinger_Upper', 0)
    alt_bant = son.get('Bollinger_Lower', 0)
    fiyat = son['Close']
    
    if fiyat < alt_bant:
        score += 15
        rapor.append({"msg": t['rpt_bb_low'], "durum": "pozitif"})
    elif fiyat > ust_bant:
        score -= 15
        rapor.append({"msg": t['rpt_bb_high'], "durum": "negatif"})

    
    if 'EMA_100' in son and fiyat > son['EMA_100']:
        score += 10
        rapor.append({"msg": t['rpt_ema_pos'], "durum": "pozitif"})
    else:
        score -= 10
        rapor.append({"msg": t['rpt_ema_neg'], "durum": "negatif"})

    if 'MACD' in son and 'Signal_Line' in son:
        macd_hist = son['MACD'] - son['Signal_Line']
        if macd_hist > 0:
            score += 5
            rapor.append({"msg": t['rpt_macd_buy'], "durum": "pozitif"})
        else:
            score -= 5
            rapor.append({"msg": t['rpt_macd_sell'], "durum": "negatif"})

    final_score = max(0, min(100, score))
    return final_score, rapor    