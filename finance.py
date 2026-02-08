import yfinance as yf
import pandas as pd
import feedparser
import urllib.parse
import numpy as np

# --- 1. AKILLI VERİ DÜZELTİCİ (THE SANITIZER) ---
def akilli_veri_duzeltici(df):
    """
    Bu fonksiyon, Yahoo Finance'in atladığı 'Bedelli Sermaye Artırımı'
    gibi olayları matematiksel olarak tespit eder ve düzeltir.
    
    Mantık: BIST'te bir hisse bir günde %20 düşemez (Devre kesici %10).
    Eğer %20+ düşüş varsa, bu bir bölünmedir.
    """
    df = df.copy()
    
    # Kapanış fiyatlarındaki günlük değişimi hesapla
    df['Degisim'] = df['Close'].pct_change()
    
    # %20'den (0.20) büyük düşüşleri 'Anomali' olarak işaretle
    anomaliler = df[df['Degisim'] < -0.20]
    
    if not anomaliler.empty:
        for tarih in anomaliler.index:
            # Bölünme öncesi son fiyat (Dün)
            fiyat_once = df['Close'].shift(1).loc[tarih]
            # Bölünme sonrası ilk fiyat (Bugün)
            fiyat_sonra = df['Close'].loc[tarih]
            
            # Eğer veri hatası değilse (bölünme katsayısı hesapla)
            if fiyat_sonra > 0:
                bolunme_katsayisi = fiyat_once / fiyat_sonra
                
                # Sadece mantıklı bölünmeleri düzelt (Örn: 1.5 kat ile 100 kat arası)
                if 1.2 < bolunme_katsayisi < 100:
                    # O tarihten önceki tüm verileri (Open, High, Low, Close) katsayıya böl
                    mask = df.index < tarih
                    cols = ['Open', 'High', 'Low', 'Close']
                    df.loc[mask, cols] = df.loc[mask, cols] / bolunme_katsayisi
    
    # Geçici kolonları temizle
    if 'Degisim' in df.columns:
        df.drop(columns=['Degisim'], inplace=True)
        
    return df

# --- 2. ŞİRKET BİLGİSİ ---
def get_company_info(symbol):
    try:
        ticker = yf.Ticker(symbol)
        return ticker.info
    except:
        return None

# --- 3. GÜVENLİ HABER VE BAŞLIK ÇEKİCİ ---
def get_smart_news(ticker_symbol, lang_code):
    query = ticker_symbol
    haberler = []
    # Varsayılan başlık sembolün kendisi olsun (Büyük harfle)
    baslik = ticker_symbol.upper() 
    
    try:
        ticker = yf.Ticker(ticker_symbol)
        info = ticker.info
        
        # İsmi almaya çalış, alamazsan sembolü kullan
        raw_name = info.get('shortName') or info.get('longName')
        if raw_name:
            # Gereksiz uzantıları temizle
            clean_name = raw_name.replace("Inc.", "").replace("Corp.", "").replace("A.S.", "").replace("Tic.", "").replace("San.", "").strip()
            baslik = clean_name
            query = clean_name
            
        encoded_query = urllib.parse.quote(f"{query} finance")
        
        if lang_code == 'tr':
            url = f"https://news.google.com/rss/search?q={encoded_query}+when:7d&hl=tr&gl=TR&ceid=TR:tr"
        else:
            url = f"https://news.google.com/rss/search?q={encoded_query}+when:7d&hl=en-US&gl=US&ceid=US:en"
            
        feed = feedparser.parse(url)
        if feed.entries:
            haberler = feed.entries[:6]
            
    except Exception as e:
        print(f"Haber Hatası: {e}")
        # Hata olsa bile elimizde en azından bir başlık (sembol) var.
        
    # KRİTİK: Asla tuple içinde tuple döndürme. Net ol.
    return haberler, baslik

# --- 4. TEKNİK İNDİKATÖRLER ---
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

# --- 5. PUANLAMA MOTORU ---
def hesapla_teknik_skor(df, t):
    base_score = 50
    score = base_score
    rapor = []
    son = df.iloc[-1]
    
    # 1. RSI (Momentum)
    # RSI > 70 ise puan düşer, < 30 ise puan artar.
    rsi_katkisi = (50 - son['RSI']) * 0.5 # Katsayıyı biraz yumuşattık
    score += rsi_katkisi
    
    if son['RSI'] < 30: 
        # TUPLE OLARAK DÖNÜYORUZ: (Mesaj, Durum)
        rapor.append({"msg": t['rpt_rsi_low'].format(son['RSI']), "durum": "pozitif"})
    elif son['RSI'] > 70: 
        rapor.append({"msg": t['rpt_rsi_high'].format(son['RSI']), "durum": "negatif"})
    elif rsi_katkisi > 0: 
        rapor.append({"msg": t['rpt_rsi_pos'], "durum": "pozitif"})
    else: 
        rapor.append({"msg": t['rpt_rsi_neg'], "durum": "negatif"})

    # 2. BOLLINGER (%B Konumu)
    ust_bant = son['Bollinger_Upper']
    alt_bant = son['Bollinger_Lower']
    fiyat = son['Close']
    
    # %B Hesaplama: Fiyat bantların neresinde? (0=Alt, 1=Üst)
    if (ust_bant - alt_bant) != 0:
        b_percent = (fiyat - alt_bant) / (ust_bant - alt_bant)
        # 0.5'ten sapmaya göre puan
        bb_katkisi = (0.5 - b_percent) * 30 
        score += bb_katkisi
        
        if b_percent < 0:
            rapor.append({"msg": t['rpt_bb_low'], "durum": "pozitif"})
        elif b_percent > 1:
            rapor.append({"msg": t['rpt_bb_high'], "durum": "negatif"})
        else:
            # Bant içindeyse nötr mesaj eklemeye gerek yok, kalabalık etmesin
            pass

    # 3. TREND (SMA)
    sma50 = son['SMA_50']
    sma_fark_yuzde = (fiyat - sma50) / sma50
    sma_katkisi = sma_fark_yuzde * 100 * 1.5
    sma_katkisi = max(-20, min(20, sma_katkisi)) # Max etkiyi sınırla
    score += sma_katkisi
    
    if son['SMA_20'] > son['SMA_50']:
        score += 5
        rapor.append({"msg": t['rpt_golden_cross'], "durum": "pozitif"})
    
    if sma_fark_yuzde > 0.15: # %15'ten fazla primliyse risk artar
        rapor.append({"msg": f"Fiyat Ortalamalardan Çok Uzaklaşmış (%{sma_fark_yuzde*100:.1f}) - Düzeltme Riski", "durum": "negatif"})
    elif sma_fark_yuzde > 0: 
        rapor.append({"msg": t['rpt_sma_pos'].format(sma_fark_yuzde*100), "durum": "pozitif"})
    else: 
        rapor.append({"msg": t['rpt_sma_neg'].format(abs(sma_fark_yuzde*100)), "durum": "negatif"})

    # 4. MACD
    macd_hist = son['MACD'] - son['Signal_Line']
    if macd_hist > 0:
        score += 10
        rapor.append({"msg": t['rpt_macd_buy'], "durum": "pozitif"})
    else:
        score -= 10
        rapor.append({"msg": t['rpt_macd_sell'], "durum": "negatif"})

    final_score = max(0, min(100, score))
    
    return final_score, rapor 