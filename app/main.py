from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.routes import ingest_routes, refine_routes, export_routes, status_routes


app = FastAPI(title="AI Video Edit Backend")

# CORS Configuration - Allow all origins
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins
    allow_credentials=True,
    allow_methods=["*"],  # Allow all methods (GET, POST, PUT, DELETE, etc.)
    allow_headers=["*"],  # Allow all headers
)

# AI Chat Edit endpoint (Flow 2)
app.include_router(refine_routes.router, prefix="/api/edit", tags=["edit"])

# Legacy routes
app.include_router(ingest_routes.router, prefix="/ingest", tags=["ingest"])
app.include_router(export_routes.router, prefix="/export", tags=["export"])
app.include_router(status_routes.router, prefix="/status", tags=["system"])



@app.get("/health")
def health():
    return {"status": "ok"}
