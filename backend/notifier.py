from config import settings

def send_guard_alert(plate: str, snapshot_path: str, timestamp: str) -> None:
    """Send WhatsApp/SMS alert to guard. Prints to stdout if Twilio not configured."""
    if not settings.twilio_account_sid.get_secret_value():
        print(f"[ALERT] Unknown plate: {plate} | Time: {timestamp} | Snapshot: {snapshot_path}")
        return

    from twilio.rest import Client
    client = Client(settings.twilio_account_sid.get_secret_value(), settings.twilio_auth_token.get_secret_value())
    client.messages.create(
        from_=f"whatsapp:{settings.twilio_from_number.get_secret_value()}",
        to=f"whatsapp:{settings.guard_phone_number}",
        body=f"Unknown vehicle at gate\nPlate: {plate}\nTime: {timestamp}",
    )
