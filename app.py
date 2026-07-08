from fastapi import FastAPI

app = FastAPI()

@app.get("/")
def root():
    return {"message": "ORB desk is alive"}

@app.get("/engine/state")
def engine_state():
    return {
        "universe": ["SPY", "QQQ", "AAPL", "MSFT"],
        "orb_minutes": 30,
        "signals": []
    }
