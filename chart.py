import plotly.graph_objects as go
from plotly.subplots import make_subplots

def build_kline_chart(df, ticker):
    if df.empty: return go.Figure()
    fig = make_subplots(rows=2, cols=1, shared_xaxes=True, vertical_spacing=0.05, 
                        row_heights=[0.7, 0.3],
                        subplot_titles=("K線與均線 (5/20/60/120 MA)", "成交量"))
    
    # K線：紅漲綠跌
    fig.add_trace(go.Candlestick(x=df.index, open=df['Open'], high=df['High'], low=df['Low'], close=df['Close'],
        increasing_line_color='#FF3232', decreasing_line_color='#00AB5E', name='K線'), row=1, col=1)
    
    # 均線
    ma_cfg = {'MA5':'#FFD700', 'MA20':'#FF1493', 'MA60':'#BF55EC', 'MA120':'#00BFFF'}
    for ma, color in ma_cfg.items():
        if ma in df.columns:
            fig.add_trace(go.Scatter(x=df.index, y=df[ma], line=dict(color=color, width=1.5), name=ma), row=1, col=1)

    # 成交量：紅漲綠跌
    colors = ['#FF3232' if c >= o else '#00AB5E' for c, o in zip(df['Close'], df['Open'])]
    fig.add_trace(go.Bar(x=df.index, y=df['Volume'], marker_color=colors, name='成交量'), row=2, col=1)
    
    fig.update_layout(template="plotly_dark", height=600, xaxis_rangeslider_visible=False, margin=dict(t=50, b=50))
    return fig

def build_financial_comparison(fins):
    rev = fins.get("rev")
    if rev is None or (hasattr(rev, 'empty') and rev.empty): return go.Figure()
    rev = rev.dropna()
    fig = go.Figure(go.Bar(x=rev.index.astype(str), y=rev.values, text=[f"{v/1e8:.1f}億" for v in rev.values], 
                    textposition='outside', marker_color='#1f77b4'))
    fig.update_layout(template="plotly_dark", height=400, title="季度營收趨勢 (單位:億)", yaxis=dict(showticklabels=False))
    return fig