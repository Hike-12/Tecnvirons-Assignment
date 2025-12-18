from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from app.routers import websocket
from dotenv import load_dotenv

load_dotenv()

app = FastAPI(title="Technivirons AI Backend")

app.include_router(websocket.router)

app.mount("/", StaticFiles(directory="static", html=True), name="static")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)
