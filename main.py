from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager

from datetime import datetime
import json
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import logging
import traceback

# ===================== CONFIG =====================

# Email settings
EMAIL_ADDRESS = 'michalozarek2000@gmail.com'
EMAIL_PASSWORD = 'vhgu vcci kdnb brem'  # Use app password if using Gmail 2FA
TO_EMAIL = 'michalozarek2000@gmail.com

PRICE_THRESHOLD = 50
currency = '£'

urls = [
    'https://www.ryanair.com/gb/en/trip/flights/select?adults=1&dateOut=2026-08-06&originIata=EDI&destinationIata=KRK',
    'https://www.ryanair.com/gb/en/trip/flights/select?adults=1&dateOut=2026-08-07&originIata=EDI&destinationIata=KRK',
    'https://www.ryanair.com/gb/en/trip/flights/select?adults=1&dateOut=2026-08-05&originIata=EDI&destinationIata=WMI',
    'https://www.ryanair.com/gb/en/trip/flights/select?adults=1&dateOut=2026-08-06&originIata=EDI&destinationIata=WMI',
    'https://www.ryanair.com/gb/en/trip/flights/select?adults=1&dateOut=2026-08-05&originIata=EDI&destinationIata=WRO',
    'https://www.ryanair.com/gb/en/trip/flights/select?adults=1&dateOut=2026-08-06&originIata=EDI&destinationIata=WRO',
    'https://www.ryanair.com/gb/en/trip/flights/select?adults=1&dateOut=2026-08-05&originIata=GLA&destinationIata=WRO',
    'https://www.ryanair.com/gb/en/trip/flights/select?adults=1&dateOut=2026-08-07&originIata=GLA&destinationIata=WMI',
    'https://www.ryanair.com/gb/en/trip/flights/select?adults=1&dateOut=2026-08-05&originIata=GLA&destinationIata=KRK'
]

logging.basicConfig(level=logging.INFO)


# ===================== EMAIL =====================

def send_email(flights):
    subject = f"✈️ {len(flights)} cheap flights under {currency}{PRICE_THRESHOLD} found!"
    body = "Flights:\n\n"

    for f in flights:
        body += f"""
🛫 {f['origin']} → 🛬 {f['destination']}
📅 {f['departureDate']}
⏰ {f['departureTime']} → {f['arrivalTime']}
💸 {currency}{f['price']}
🔗 {f['url']}
-------------------------
"""

    msg = MIMEMultipart()
    msg['From'] = EMAIL_ADDRESS
    msg['To'] = TO_EMAIL
    msg['Subject'] = subject
    msg.attach(MIMEText(body, 'plain'))

    try:
        with smtplib.SMTP_SSL('smtp.gmail.com', 465) as server:
            server.login(EMAIL_ADDRESS, EMAIL_PASSWORD)
            server.send_message(msg)
            logging.info("📧 Email sent")
    except Exception as e:
        logging.error(f"Email failed: {e}")


# ===================== SCRAPER =====================

def fetch_flights():
    chrome_options = Options()
    chrome_options.add_argument("--headless=new")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--window-size=1920,1080")

    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=chrome_options)

    all_flights = []

    for url in urls:
        try:
            logging.info(f"Checking {url}")
            driver.get(url)

            WebDriverWait(driver, 20).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, ".flight-card"))
            )

            day = driver.find_element(By.CSS_SELECTOR, 'span.date-item__day-of-month--selected').text
            month = driver.find_element(By.CSS_SELECTOR, 'span.date-item__month--selected').text
            departureDate = f"{day} {month}"

            flights_script = """
            let flights = [];
            document.querySelectorAll('.flight-card').forEach(card => {
                let origin = card.querySelector('[data-ref="flight-segment.departure"] .flight-info__city')?.innerText;
                let destination = card.querySelector('[data-ref="flight-segment.arrival"] .flight-info__city')?.innerText;
                let dep = card.querySelector('[data-ref="flight-segment.departure"] .flight-info__hour')?.innerText;
                let arr = card.querySelector('[data-ref="flight-segment.arrival"] .flight-info__hour')?.innerText;
                let priceText = card.querySelector('flights-price-simple')?.innerText;

                let price = null;
                if (priceText) {
                    let clean = priceText.replace(/[^0-9.,]/g, '').replace(',', '.');
                    price = parseFloat(clean);
                }

                flights.push({
                    origin: origin || "N/A",
                    destination: destination || "N/A",
                    departureTime: dep || "N/A",
                    arrivalTime: arr || "N/A",
                    price: price,
                    departureDate: arguments[0],
                    url: arguments[1]
                });
            });
            return JSON.stringify(flights);
            """

            result = driver.execute_script(flights_script, departureDate, url)
            all_flights.extend(json.loads(result))

        except Exception as e:
            logging.error(f"Error on {url}: {e}")

    driver.quit()
    return all_flights


# ===================== MAIN =====================

if __name__ == "__main__":
    logging.info("🔁 Running flight check")

    try:
        flights = fetch_flights()

        matching = [
            f for f in flights
            if isinstance(f['price'], (int, float)) and f['price'] < PRICE_THRESHOLD
        ]

        if matching:
            logging.info(f"{len(matching)} matches found")
            send_email(matching)
        else:
            logging.info("No cheap flights found")

    except Exception:
        logging.error("Unexpected error:")
        traceback.print_exc()
