import json, os, sys, urllib.request, urllib.parse
from datetime import datetime

EVENT_URL = "https://kiz-shop.com/events/k-i-z-nur-fuer-frauen-2027-stadthalle?tab=resale"
TELEGRAM_BOT_TOKEN = os.environ["TELEGRAM_BOT_TOKEN"]
TELEGRAM_CHAT_ID = os.environ["TELEGRAM_CHAT_ID"]
STATE_FILE = "kiz_resale_state.json"

NO_TICKETS_MARKERS = ["keine tickets", "keine artikel", "derzeit keine", "aktuell keine", "no tickets", "not available"]

def send_telegram_message(text):
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    data = urllib.parse.urlencode({"chat_id": TELEGRAM_CHAT_ID, "text": text}).encode()
    try:
        urllib.request.urlopen(urllib.request.Request(url, data=data), timeout=15).read()
    except Exception as e:
        print(f"[FEHLER] Telegram: {e}", file=sys.stderr)

def load_state():
    if os.path.exists(STATE_FILE):
        with open(STATE_FILE) as f:
            return json.load(f)
    return {"tickets_available": False}

def save_state(state):
    with open(STATE_FILE, "w") as f:
        json.dump(state, f)

def check_resale_page():
    from playwright.sync_api import sync_playwright
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        page.goto(EVENT_URL, wait_until="networkidle", timeout=30000)
        page.wait_for_timeout(3000)
        body_text = page.inner_text("body").lower()
        browser.close()
    no_tickets = any(m in body_text for m in NO_TICKETS_MARKERS)
    return not no_tickets

def main():
    state = load_state()
    try:
        tickets_available = check_resale_page()
    except Exception as e:
        print(f"[{datetime.now()}] Fehler: {e}", file=sys.stderr)
        return
    was_available = state.get("tickets_available", False)
    print(f"[{datetime.now()}] Tickets verfügbar: {tickets_available}")
    if tickets_available and not was_available:
        send_telegram_message(f"🎫 KIZ Resale-Tickets aufgetaucht!\n\n{EVENT_URL}\n\nSchnell schauen, bevor sie weg sind.")
        print("Telegram-Benachrichtigung gesendet.")
    state["tickets_available"] = tickets_available
    state["last_checked"] = datetime.now().isoformat()
    save_state(state)

if __name__ == "__main__":
    main()
