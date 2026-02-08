import yfinance as yf
import pandas as pd
import feedparser
import urllib.parse
import numpy as np

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
    # RSI
    delta = df['Close'].diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
    rs = gain / loss
    df['RSI'] = 100 - (100 / (1 + rs))
    
    # SMA
    df['SMA_20'] = df['Close'].rolling(window=20).mean()
    df['SMA_50'] = df['Close'].rolling(window=50).mean()
    
    # BOLLINGER
    std = df['Close'].rolling(window=20).std()
    df['Bollinger_Upper'] = df['SMA_20'] + (std * 2)
    df['Bollinger_Lower'] = df['SMA_20'] - (std * 2)
    
    # MACD
    exp1 = df['Close'].ewm(span=12, adjust=False).mean()
    exp2 = df['Close'].ewm(span=26, adjust=False).mean()
    df['MACD'] = exp1 - exp2
    df['Signal_Line'] = df['MACD'].ewm(span=9, adjust=False).mean()

    # STOKASTİK
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