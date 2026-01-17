from fastapi import FastAPI
from app.routes import ingest_routes, refine_routes, export_routes, status_routes


app = FastAPI(title="AI Video Edit Backend")

app.include_router(ingest_routes.router, prefix="/ingest", tags=["ingest"])
app.include_router(refine_routes.router, prefix="/refine", tags=["refine"])
app.include_router(export_routes.router, prefix="/export", tags=["export"])
app.include_router(status_routes.router, prefix="/status", tags=["system"])



@app.get("/health")
def health():
    return {"status": "ok"}
