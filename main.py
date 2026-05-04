from playwright.sync_api import sync_playwright
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
TO_EMAIL = 'michalozarek2000@gmail.com'

PRICE_THRESHOLD = 70
currency = '£'

urls = [
    'https://www.ryanair.com/gb/en/trip/flights/select?adults=1&teens=0&children=0&infants=0&dateOut=2026-08-06&dateIn=&discount=0&isReturn=false&promoCode=&originIata=EDI&destinationIata=KRK&tpAdults=1&tpTeens=0&tpChildren=0&tpInfants=0&tpStartDate=2026-08-06&tpEndDate=&tpDiscount=0&tpPromoCode=&tpOriginIata=EDI&tpDestinationIata=KRK',
    'https://www.ryanair.com/gb/en/trip/flights/select?adults=1&teens=0&children=0&infants=0&dateOut=2026-08-07&dateIn=&discount=0&isReturn=false&promoCode=&originIata=EDI&destinationIata=KRK&tpAdults=1&tpTeens=0&tpChildren=0&tpInfants=0&tpStartDate=2026-08-07&tpEndDate=&tpDiscount=0&tpPromoCode=&tpOriginIata=EDI&tpDestinationIata=KRK',
    'https://www.ryanair.com/gb/en/trip/flights/select?adults=1&teens=0&children=0&infants=0&dateOut=2026-08-05&dateIn=&discount=0&isReturn=false&promoCode=&originIata=EDI&destinationIata=WMI&tpAdults=1&tpTeens=0&tpChildren=0&tpInfants=0&tpStartDate=2026-08-05&tpEndDate=&tpDiscount=0&tpPromoCode=&tpOriginIata=EDI&tpDestinationIata=WMI',
    'https://www.ryanair.com/gb/en/trip/flights/select?adults=1&teens=0&children=0&infants=0&dateOut=2026-08-06&dateIn=&discount=0&isReturn=false&promoCode=&originIata=EDI&destinationIata=WMI&tpAdults=1&tpTeens=0&tpChildren=0&tpInfants=0&tpStartDate=2026-08-06&tpEndDate=&tpDiscount=0&tpPromoCode=&tpOriginIata=EDI&tpDestinationIata=WMI',
    'https://www.ryanair.com/gb/en/trip/flights/select?adults=1&teens=0&children=0&infants=0&dateOut=2026-08-05&dateIn=&discount=0&isReturn=false&promoCode=&originIata=EDI&destinationIata=WRO&tpAdults=1&tpTeens=0&tpChildren=0&tpInfants=0&tpStartDate=2026-08-05&tpEndDate=&tpDiscount=0&tpPromoCode=&tpOriginIata=EDI&tpDestinationIata=WRO',
    'https://www.ryanair.com/gb/en/trip/flights/select?adults=1&teens=0&children=0&infants=0&dateOut=2026-08-06&dateIn=&discount=0&isReturn=false&promoCode=&originIata=EDI&destinationIata=WRO&tpAdults=1&tpTeens=0&tpChildren=0&tpInfants=0&tpStartDate=2026-08-06&tpEndDate=&tpDiscount=0&tpPromoCode=&tpOriginIata=EDI&tpDestinationIata=WRO',
    'https://www.ryanair.com/gb/en/trip/flights/select?adults=1&teens=0&children=0&infants=0&dateOut=2026-08-05&dateIn=&discount=0&isReturn=false&promoCode=&originIata=GLA&destinationIata=WRO&tpAdults=1&tpTeens=0&tpChildren=0&tpInfants=0&tpStartDate=2026-08-05&tpEndDate=&tpDiscount=0&tpPromoCode=&tpOriginIata=GLA&tpDestinationIata=WRO',
    'https://www.ryanair.com/gb/en/trip/flights/select?adults=1&teens=0&children=0&infants=0&dateOut=2026-08-07&dateIn=&discount=0&isReturn=false&promoCode=&originIata=GLA&destinationIata=WMI&tpAdults=1&tpTeens=0&tpChildren=0&tpInfants=0&tpStartDate=2026-08-07&tpEndDate=&tpDiscount=0&tpPromoCode=&tpOriginIata=GLA&tpDestinationIata=WMI',
    'https://www.ryanair.com/gb/en/trip/flights/select?adults=1&teens=0&children=0&infants=0&dateOut=2026-08-05&dateIn=&discount=0&isReturn=false&promoCode=&originIata=GLA&destinationIata=KRK&tpAdults=1&tpTeens=0&tpChildren=0&tpInfants=0&tpStartDate=2026-08-05&tpEndDate=&tpDiscount=0&tpPromoCode=&tpOriginIata=GLA&tpDestinationIata=KRK'
]

logging.basicConfig(level=logging.INFO)

# ===================== EMAIL =====================

def send_email(flights):
    subject = f"{len(flights)} cheap flights under {currency}{PRICE_THRESHOLD}"
    body = ""

    for f in flights:
        body += f"""
{f['origin']} → {f['destination']}
{f['departureDate']}
{f['departureTime']} → {f['arrivalTime']}
{currency}{f['price']}
{f['url']}
---------------------
"""

    msg = MIMEMultipart()
    msg['From'] = EMAIL_ADDRESS
    msg['To'] = TO_EMAIL
    msg['Subject'] = subject
    msg.attach(MIMEText(body, 'plain'))

    with smtplib.SMTP_SSL('smtp.gmail.com', 465) as server:
        server.login(EMAIL_ADDRESS, EMAIL_PASSWORD)
        server.send_message(msg)

# ===================== SCRAPER =====================

def fetch_flights():
    all_flights = []

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()

        for url in urls:
            try:
                logging.info(f"Checking {url}")
                page.goto(url, timeout=60000)

                page.wait_for_selector(".flight-card", timeout=20000)

                departureDate = page.evaluate("""
                    () => {
                        let day = document.querySelector('.date-item__day-of-month--selected')?.innerText;
                        let month = document.querySelector('.date-item__month--selected')?.innerText;
                        return day && month ? `${day} ${month}` : "N/A";
                    }
                """)

                flights = page.evaluate("""
                () => {
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
                        });
                    });
                    return flights;
                }
                """)

                for f in flights:
                    f["url"] = url
                    f["departureDate"] = departureDate

                all_flights.extend(flights)

            except Exception as e:
                logging.error(f"Error on {url}: {e}")

        browser.close()

    return all_flights

# ===================== MAIN =====================

if __name__ == "__main__":
    logging.info("Running flight check")

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
        traceback.print_exc()
