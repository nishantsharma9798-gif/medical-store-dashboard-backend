import asyncio

from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger

from app.db.session import SessionLocal
from app.db.models.medicine import Medicine
from app.db.models.client import Client
from app.services.prediction import predict_weekend_demand
from app.services.whatsapp import send_whatsapp

scheduler = BackgroundScheduler()


def run_weekly_prediction_job():
    """Every Friday 10 AM — check predicted weekend demand vs stock, alert staff on WhatsApp."""
    db = SessionLocal()
    try:
        clients = db.query(Client).all()
        for client in clients:
            medicine_ids = [m.id for m in db.query(Medicine.id).filter(Medicine.client_id == client.id)]
            alerts = predict_weekend_demand(db, medicine_ids)
            for alert in alerts:
                # In production, look up the client's staff WhatsApp number(s) here.
                asyncio.run(
                    send_whatsapp(
                        to="<staff_whatsapp_number>",
                        template_name="restock_alert",
                        params={
                            "medicine": alert["medicine_name"],
                            "predicted": alert["predicted_demand"],
                            "stock": alert["current_stock"],
                        },
                    )
                )
    finally:
        db.close()


def start_scheduler():
    if scheduler.running:
        return
    scheduler.add_job(
        run_weekly_prediction_job,
        CronTrigger(day_of_week="fri", hour=10, minute=0),
        id="weekly_prediction",
        replace_existing=True,
    )
    scheduler.start()
