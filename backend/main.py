from fastapi import FastAPI
from routers import analyze

app = FastAPI(title="LegoCV Backend")

app.include_router(analyze.router, prefix="")

@app.get('/health')
def health():
    return {"status": "ok"}

if __name__ == '__main__':
    import uvicorn
    uvicorn.run(app, host='0.0.0.0', port=8000)
