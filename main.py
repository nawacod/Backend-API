from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from engine import run_backtest
import yfinance as yf
import re

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class NLPRequest(BaseModel):
    prompt: str

def fetch_real_data(strAsset: str):
    """Fetches real historical candlestick data from Yahoo Finance"""
    
    dictTickers = {"MNQ": "QQQ", "MGC": "GLD", "EUR/USD": "EURUSD=X"}
    strSymbol = dictTickers.get(strAsset, "QQQ")
    
    print(f"Pulling live data for {strSymbol} from Yahoo Finance...")
    try:
        objTicker = yf.Ticker(strSymbol)
        dfMarket = objTicker.history(period="1y")
        
        if dfMarket.empty:
            print(f"WARNING: Yahoo Finance returned empty data for {strSymbol}.")
            return []
            
        dfMarket = dfMarket.dropna()
        
        lstData = []
        for index, row in dfMarket.iterrows():
            lstData.append({
                "time": index.strftime("%Y-%m-%d"),
                "open": float(row['Open']),
                "high": float(row['High']),
                "low": float(row['Low']),
                "close": float(row['Close'])
            })
        return lstData
    except Exception as e:
        print(f"Yahoo Finance Connection Error: {e}")
        return []

@app.post("/api/run-backtest")
def api_run_backtest(objReq: NLPRequest):
    strPrompt = objReq.prompt
    print(f"Received Strategy Prompt: {strPrompt}")
    
   
    objTpMatch = re.search(r'([0-9.]+)%\s*take', strPrompt, re.IGNORECASE)
    objSlMatch = re.search(r'([0-9.]+)%\s*stop', strPrompt, re.IGNORECASE)
    
    fTakeProfit = float(objTpMatch.group(1)) / 100 if objTpMatch else 0.05
    fStopLoss = float(objSlMatch.group(1)) / 100 if objSlMatch else 0.02
    strAsset = "MNQ" 
    
    
    lstMarketData = fetch_real_data(strAsset)
    
    # SAFETY NET: If Yahoo Finance fails, gracefully return 0 instead of crashing
    if len(lstMarketData) < 20:
        return {
            "status": "success", 
            "ai_interpretation": {
                "asset": strAsset,
                "take_profit": f"{round(fTakeProfit * 100, 2)}%",
                "stop_loss": f"{round(fStopLoss * 100, 2)}%"
            },
            "data": {"win_rate": 0, "total_trades": 0, "return_pct": 0}
        }
    
    # 2. Run the strategy math
    dictResults = run_backtest(
        data=lstMarketData, 
        take_profit_pct=fTakeProfit, 
        stop_loss_pct=fStopLoss
    )
    
    # 3. Send it all back to React
    return {
        "status": "success", 
        "ai_interpretation": {
            "asset": strAsset,
            "take_profit": f"{round(fTakeProfit * 100, 2)}%",
            "stop_loss": f"{round(fStopLoss * 100, 2)}%"
        },
        "data": dictResults
    }