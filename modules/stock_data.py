import yfinance as yf
import pandas as pd
import requests
import feedparser

def get_trending_stocks():
    """爬取 Yahoo Finance 熱門活躍股榜單"""
    try:
        headers = {'User-Agent': 'Mozilla/5.0'}
        url = "https://finance.yahoo.com/most-active"
        response = requests.get(url, headers=headers)
        tables = pd.read_html(response.text)
        return tables[0]['Symbol'].tolist()[:10]
    except:
        return ["NVDA", "TSLA", "AAPL", "AMD", "MSFT"]

def get_stock_info(ticker):
    try:
        t = yf.Ticker(ticker)
        info = t.info
        
        # 抓取最近 5 天資料確保能取到最新的完整交易日
        hist = t.history(period="5d")
        
        prev_data = {
            "prev_open": 0, "prev_close": 0, 
            "prev_high": 0, "prev_low": 0, "prev_change": 0
        }
        
        if len(hist) >= 2:
            # 判斷最後一筆是否為今天(可能尚未收盤)，取最後一筆「已收盤」的資料
            # 如果目前是台灣 2/27 晚上，最後一筆會是 2/26 的完整數據
            last_session = hist.iloc[-1] 
            
            prev_data["prev_open"] = last_session['Open']
            prev_data["prev_close"] = last_session['Close']
            prev_data["prev_high"] = last_session['High']
            prev_data["prev_low"] = last_session['Low']
            
            # 計算該交易日的內在漲跌幅 (收盤 vs 開盤)
            if last_session['Open'] != 0:
                prev_data["prev_change"] = (last_session['Close'] - last_session['Open']) / last_session['Open'] * 100

        result = {
            "name": info.get("longName", ticker),
            "price": info.get("currentPrice", 0),
            "market_cap": f"{info.get('marketCap', 0)/1e11:.2f} 兆" if info.get('marketCap', 0) > 1e12 else f"{info.get('marketCap', 0)/1e8:.2f} 億",
            "pe": info.get("trailingPE", 0),
            "roe": f"{info.get('returnOnEquity', 0)*100:.1f}%",
            "inst_pct": f"{info.get('heldPercentInstitutions', 0)*100:.1f}%",
            "short_ratio": info.get("shortRatio", 0),
            "52w_high": info.get("fiftyTwoWeekHigh", 0),
            "52w_low": info.get("fiftyTwoWeekLow", 0),
            "volatility": info.get("beta", "N/A")
        }
        result.update(prev_data)
        return result
    except:
        return {"error": True}

# get_price_history, get_financials 等維持原樣...

def get_price_history(ticker: str):
    try:
        df = yf.Ticker(ticker).history(period="2y")
        if not df.empty:
            df['MA5'] = df['Close'].rolling(5).mean()
            df['MA20'] = df['Close'].rolling(20).mean()
            df['MA60'] = df['Close'].rolling(60).mean()
            df['MA120'] = df['Close'].rolling(120).mean()
        return df
    except: return pd.DataFrame()

def get_financials(ticker):
    try:
        df = yf.Ticker(ticker).quarterly_financials
        if df is not None and not df.empty:
            for label in ["Total Revenue", "Operating Revenue", "Revenue"]:
                if label in df.index: return {"rev": df.loc[label].iloc[:8][::-1]}
        return {"rev": pd.Series()}
    except: return {"rev": pd.Series()}

def get_news(ticker):
    try:
        feed = feedparser.parse(f"https://news.google.com/rss/search?q={ticker}+stock&hl=zh-TW&gl=TW&ceid=TW:zh-Hant")
        return [{"title": e.title, "link": e.link} for e in feed.entries[:6]]
    except: return []

def get_trending_stocks():
    """爬取 Yahoo Finance 熱門活躍股榜單"""
    try:
        # 模擬瀏覽器標頭
        headers = {'User-Agent': 'Mozilla/5.0'}
        url = "https://finance.yahoo.com/most-active"
        response = requests.get(url, headers=headers)
        # 使用 pandas 直接讀取網頁中的表格
        tables = pd.read_html(response.text)
        df = tables[0]
        # 取前 10 名熱門股代碼
        return df['Symbol'].tolist()[:10]
    except Exception as e:
        print(f"爬取熱搜失敗: {e}")
        return ["NVDA", "TSLA", "AAPL", "AMD", "MSFT"] # 失敗時的保底清單
    
def get_prediction(df, info):
    if df.empty: return {}
    
    last_close = df['Close'].iloc[-1]
    ma5 = df['MA5'].iloc[-1]
    ma20 = df['MA20'].iloc[-1]
    ma60 = df['MA60'].iloc[-1]
    
    # 1. 短期預測：多空動能
    short_term = "🟢 看多" if last_close > ma5 else "🔴 看空"
    short_reason = "股價位於週線之上，動能強勁" if last_close > ma5 else "短期跌破週線，震盪加劇"
    
    # 2. 中期預測：趨勢方向
    mid_term = "🟢 看多" if ma20 > ma60 else "🔴 看空"
    mid_reason = "月線高於季線，處於上升通道" if ma20 > ma60 else "空頭排列，壓力重重"
    
    # 3. 長期預測：價值位階
    h52 = info.get('52w_high', 1)
    l52 = info.get('52w_low', 0)
    pos = (last_close - l52) / (h52 - l52) if (h52 - l52) != 0 else 0.5
    long_term = "🟡 中性" if 0.3 < pos < 0.7 else ("🟢 看多" if pos < 0.3 else "🔴 警戒")
    long_reason = "超跌區間，具長線投資價值" if pos < 0.3 else ("高檔過熱，需防回檔" if pos > 0.7 else "處於歷史合理評價區間")
    
    return {
        "short": (short_term, short_reason),
        "mid": (mid_term, mid_reason),
        "long": (long_term, long_reason)
    }
