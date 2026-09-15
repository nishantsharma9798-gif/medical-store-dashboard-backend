import httpx
from app.core.config import settings


async def send_whatsapp(to: str, template_name: str, params: dict) -> None:
    """
    Single wrapper used everywhere the app needs to send a WhatsApp message —
    restock alerts, supplier order requests, invoice shares. Swapping providers
    (AiSensy <-> Gupshup) only requires changing this function.
    """
    if not settings.whatsapp_api_key:
        # Not configured yet — no-op so local dev doesn't crash.
        print(f"[whatsapp:stub] would send '{template_name}' to {to} with {params}")
        return

    async with httpx.AsyncClient() as client:
        await client.post(
            f"{settings.whatsapp_api_base_url}/send",
            headers={"Authorization": f"Bearer {settings.whatsapp_api_key}"},
            json={"to": to, "template": template_name, "params": params},
            timeout=10,
        )


async def handle_incoming_webhook(payload: dict) -> dict:
    """
    Parses an incoming WhatsApp webhook event. Two cases matter for this app:
    1. Supplier replies "confirm"/"reject" to an order request -> update Order status.
    2. Supplier sends an invoice image/PDF -> store as an InvoiceAttachment
       (source=whatsapp, status=pending_review) for staff to review and link.

    Wire this up in api/v1/orders.py's webhook endpoint once the provider's exact
    payload shape is known (AiSensy and Gupshup differ slightly).
    """
    return {"received": True}
