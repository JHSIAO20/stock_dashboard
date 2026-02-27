import streamlit as st
import pandas as pd
import yfinance as yf
from modules.stock_data import *
from modules.chart import *

# 設置頁面
st.set_page_config(page_title="美股決策終端", layout="wide")

# 樣式定義：強勢=紅，弱勢/觀望=綠
st.markdown("""
<style>
    .metric-card { background: #161b22; padding: 12px; border-radius: 10px; border: 1px solid #30363d; text-align: center; }
    .metric-label { color: #8b949e; font-size: 0.85rem; margin-bottom: 5px; }
    .metric-value { color: #ffffff; font-size: 1.1rem; font-weight: bold; }
    .decision-signal { font-size: 1.3rem; font-weight: bold; padding: 12px; border-radius: 8px; text-align: center; }
    .bull { background-color: #4d0000; color: #ff4d4d; border: 1px solid #ff4d4d; }
    .bear { background-color: #002d11; color: #00e64d; border: 1px solid #00e64d; }
    .watch-box { background-color: #0d1117; border: 1px solid #00e64d; padding: 15px; border-radius: 10px; margin-top: 10px; }
    .watch-ticker { color: #00e64d; font-weight: bold; font-size: 1.2rem; margin: 0; }
    .stat-label { color: #8b949e; font-size: 0.9rem; }
    .stat-value { color: #ffffff; font-weight: bold; }
    .news-box { padding: 10px; border-bottom: 1px solid #30363d; }
</style>
""", unsafe_allow_html=True)

# --- 側邊欄 ---
with st.sidebar:
    st.title("🇺🇸 操作中心")
    if st.button("🔥 抓取今日美股熱搜榜", use_container_width=True):
        trending = get_trending_stocks()
        st.session_state.ticker_input = ", ".join(trending)
        st.success("已更新熱搜名單")

    ticker_input = st.text_input("觀察代碼", st.session_state.get('ticker_input', "NVDA, TSLA"))
    run_btn = st.button("🚀 執行深度分析", type="primary", use_container_width=True)

watch_list_summary = []

if ticker_input:
    tickers = [t.strip().upper() for t in ticker_input.split(",") if t.strip()]
    
    # SPY 基準
    spy = yf.Ticker("SPY").history(period="1y")
    spy_perf = (spy['Close'].iloc[-1] / spy['Close'].iloc[0]) - 1

    for ticker in tickers:
        with st.spinner(f"分析中 {ticker}..."):
            info = get_stock_info(ticker)
            hist = get_price_history(ticker)
            fins = get_financials(ticker)
            news_list = get_news(ticker)
            
        if "error" in info or hist.empty: continue

        # 判定邏輯
        rs_score = (hist['Close'].iloc[-1] / hist['Close'].iloc[0]) - 1 - spy_perf
        h52, l52 = info.get('52w_high', 0), info.get('52w_low', 0)
        pos = ((info['price'] - l52) / (h52 - l52)) if (h52 - l52) != 0 else 0
        is_bull = (hist['Close'].iloc[-1] > hist['MA60'].iloc[-1]) and (rs_score > 0) and (pos > 0.3)
        
        if not is_bull:
            watch_list_summary.append({
                "代碼": ticker,
                "原因": "跌破60日線" if hist['Close'].iloc[-1] < hist['MA60'].iloc[-1] else "弱於大盤" if rs_score < 0 else "位階過低"
            })

        # --- 個股渲染 ---
        st.header(f"📈 {ticker} | {info['name']}")
        
        # 第一排指標
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("即時股價", f"${info['price']}", f"52週位階: {pos*100:.1f}%")
        c2.metric("相對強度 (vs SPY)", f"{rs_score*100:+.1f}%")
        c3.metric("市值", info['market_cap'])
        with c4:
            if is_bull: st.markdown('<div class="decision-signal bull">🎯 強勢：建議持有</div>', unsafe_allow_html=True)
            else: st.markdown('<div class="decision-signal bear">⚠️ 弱勢：建議觀望</div>', unsafe_allow_html=True)

        # --- 在 app.py 渲染預測區塊 ---
        pred = get_prediction(hist, info)
        st.write("🔮 **AI 趨勢展望觀測站**")
        p1, p2, p3 = st.columns(3)
        with p1:
            st.markdown(f'<div class="metric-card"><div class="metric-label">短期 (5D)</div><div class="metric-value">{pred["short"][0]}</div><div style="font-size:0.8rem;color:#8b949e;">{pred["short"][1]}</div></div>', unsafe_allow_html=True)
        with p2:
            st.markdown(f'<div class="metric-card"><div class="metric-label">中期 (Q)</div><div class="metric-value">{pred["mid"][0]}</div><div style="font-size:0.8rem;color:#8b949e;">{pred["mid"][1]}</div></div>', unsafe_allow_html=True)
        with p3:
            st.markdown(f'<div class="metric-card"><div class="metric-label">長期 (1Y)</div><div class="metric-value">{pred["long"][0]}</div><div style="font-size:0.8rem;color:#8b949e;">{pred["long"][1]}</div></div>', unsafe_allow_html=True)

        # 第二排：昨日交易數據
        st.write(f"🗓️ **昨日交易數據回顧 ({ticker})**")
        y1, y2, y3, y4, y5 = st.columns(5)
        y1.markdown(f'<div class="metric-card"><div class="metric-label">昨日開盤</div><div class="metric-value">${info["prev_open"]:.2f}</div></div>', unsafe_allow_html=True)
        y2.markdown(f'<div class="metric-card"><div class="metric-label">昨日最高</div><div class="metric-value">${info["prev_high"]:.2f}</div></div>', unsafe_allow_html=True)
        y3.markdown(f'<div class="metric-card"><div class="metric-label">昨日最低</div><div class="metric-value">${info["prev_low"]:.2f}</div></div>', unsafe_allow_html=True)
        y4.markdown(f'<div class="metric-card"><div class="metric-label">昨日收盤</div><div class="metric-value">${info["prev_close"]:.2f}</div></div>', unsafe_allow_html=True)
        
        chg = info["prev_change"]
        color = "#ff4d4d" if chg >= 0 else "#00e64d" # 紅漲綠跌
        y5.markdown(f'<div class="metric-card"><div class="metric-label">昨日漲跌</div><div class="metric-value" style="color:{color};">{chg:+.2f}%</div></div>', unsafe_allow_html=True)

        # 第三排：圖表
        col_l, col_r = st.columns([2, 1])
        with col_l:
            st.plotly_chart(build_kline_chart(hist, ticker), use_container_width=True)
            st.subheader("📰 市場情報")
            for news in news_list[:5]:
                st.markdown(f'<div class="news-box">🔗 <a href="{news["link"]}" target="_blank" style="color:#58a6ff;text-decoration:none;">{news["title"]}</a></div>', unsafe_allow_html=True)
        
        with col_r:
            st.subheader("📋 財務摘要")
            stats = [("PE", f"{info['pe']:.1f}"), ("ROE", info['roe']), ("法人持股", info['inst_pct']), ("空單比率", f"{info['short_ratio']:.2f}")]
            for l, v in stats:
                st.markdown(f'<div style="display:flex;justify-content:space-between;padding:8px 0;border-bottom:1px solid #30363d;"><span class="stat-label">{l}</span><span class="stat-value">{v}</span></div>', unsafe_allow_html=True)
            st.plotly_chart(build_financial_comparison(fins), use_container_width=True)
        st.divider()

    # --- 觀望清單 ---
    st.subheader("🍏 弱勢警示：建議觀望/減碼清單")
    if watch_list_summary:
        cols = st.columns(min(len(watch_list_summary), 5))
        for i, item in enumerate(watch_list_summary):
            with cols[i % 5]:
                st.markdown(f'<div class="watch-box"><p class="watch-ticker">{item["代碼"]}</p><p style="color:#8b949e;font-size:0.9rem;">原因：{item["原因"]}</p></div>', unsafe_allow_html=True)
    else:
        st.success("✅ 目前清單中皆為強勢股")
