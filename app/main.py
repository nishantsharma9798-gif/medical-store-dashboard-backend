from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from app.core.config import settings
from app.services.scheduler import start_scheduler
from app.api.v1 import auth, medicines, inventory, suppliers, orders, invoices, alerts, reports


@asynccontextmanager
async def lifespan(app: FastAPI):
    start_scheduler()
    yield


app = FastAPI(title="Medical Store API", version="1.0.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.frontend_origin],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(medicines.router)
app.include_router(inventory.router)
app.include_router(suppliers.router)
app.include_router(orders.router)
app.include_router(invoices.router)
app.include_router(alerts.router)
app.include_router(reports.router)


@app.get("/health")
def health_check():
    return {"status": "ok"}
