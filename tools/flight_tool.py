import os
import re
import certifi
import airportsdata
import pycountry 
from dotenv import load_dotenv
load_dotenv()
os.environ["SSL_CERT_FILE"] = certifi.where()
os.environ["REQUESTS_CA_BUNDLE"] = certifi.where()

API_KEY = os.getenv("AVIATION_API_KEY")
DEFAULT_ORIGIN_IATA = os.getenv("DEFAULT_ORIGIN_IATA", "DAC")
BASE_URL = "https://api.aviationstack.com/v1/flights"

AIRPORTS = airportsdata.load("IATA")

COUNTRY_ALIASES = {
    "United States": "US",
    "USA": "US",
    "U.S.A": "US",
    "U.S": "US",

    "United Kingdom": "GB",
    "UK": "GB",
    "U.K": "GB",
    "BRITAIN": "GB",
    "England": "GB",

    "Canada": "CA",
    "Australia": "AU"
,
    "UAE": "AE",
    "DUBAI": "AE",
    "singapore": "SG",
    "south korea": "KR",
    "korea": "KR",
    "russia": "RU",
    "vietnam": "VN",
    "bangladesh": "BD",
    "india": "IN",
    "japan": "JP",
    "china": "CN",
    "malaysia": "MY",
    "indonesia": "ID",
    "netherlands": "NL",
    "nepal": "NP",
    "thailand": "TH",
    "qatar": "QA",
    "saudi arabia": "SA",
    "turkey": "TR",
    "france": "FR",
    "canada": "CA",
    "brazil": "BR",
    "australia": "AU",
    "new zealand": "NZ",
    "germany": "DE",
    "italy": "IT",

 }  # Default to JFK if not set

CITY_MAIN_AIRPORT={
    "Delhi": "DEL",
    "Mumbai": "BOM",
    "Bengaluru": "BLR",
    "Hyderabad": "HYD",
    "Chennai": "MAA",
    "Kolkata": "CCU",
    "Ahmedabad": "AMD",
    "Pune": "PNQ",
    "Kochi": "COK",
    "Jaipur": "JAI",
    "Lucknow": "LKO",
    "Goa": "GOX",
    "Guwahati": "GAU",
    "Thiruvananthapuram": "TRV",
    "Varanasi": "VNS",
    "Amritsar": "ATQ",
    "Chandigarh": "IXC",
    "Srinagar": "SXR",
    "Indore": "IDR",
    "Nagpur": "NAG",
    "Bhubaneswar": "BBI",
    "Patna": "PAT",
    "Ranchi": "IXR",
    "Coimbatore": "CJB",
    "Mangaluru": "IXE",
    "Kozhikode": "CCJ",
    "Dehradun": "DED",
    "Raipur": "RPR",
    "Surat": "STV",
    "Vadodara": "BDQ",
    "Bhopal": "BHO",
    "Agra": "AGR",
    "Madurai": "IXM",
    "Tiruchirappalli": "TRZ",
    "Visakhapatnam": "VTZ",
    "Vijayawada": "VGA"

}

COUNTRY_MAIN_AIRPORTS = {
    "India": "DEL",
    "USA": "ATL",
    "United Kingdom": "LHR",
    "UAE": "DXB",
    "Singapore": "SIN",
    "Thailand": "BKK",
    "France": "CDG",
    "Germany": "FRA",
    "Italy": "FCO",
    "Spain": "MAD",
    "Switzerland": "ZRH",
    "Netherlands": "AMS",
    "Canada": "YYZ",
    "Australia": "SYD",
    "New Zealand": "AKL",
    "Japan": "HND",
    "South Korea": "ICN",
    "China": "PEK",
    "Hong Kong": "HKG",
    "Malaysia": "KUL",
    "Indonesia": "CGK",
    "Vietnam": "SGN",
    "Nepal": "KTM",
    "Sri Lanka": "CMB",
    "Bangladesh": "DAC",
    "Pakistan": "ISB",
    "Qatar": "DOH",
    "Saudi Arabia": "RUH",
    "Turkey": "IST",
    "Russia": "SVO",
    "South Africa": "JNB",
    "Egypt": "CAI",
    "Brazil": "GRU",
    "Mexico": "MEX",
    "Argentina": "EZE",
    "Chile": "SCL",
    "Peru": "LIM",
    "Nigeria": "LOS",
    "Kenya": "NBO",
    "Morocco": "CMN",
    "Israel": "TLV",
    "Greece": "ATH",
    "Portugal": "LIS",
    "Austria": "VIE",
    "Ireland": "DUB",
    "Philippines": "MNL",
    "Poland": "WAW",
    "Sweden": "ARN",
    "Norway": "OSL",
    "Denmark": "CPH",
    "Finland": "HEL"
}


def clean_text (text:str) -> str:
    text = text.lower().strip()
    text = re.sub(r"[^a-zA-Z0-9\s]", "", text)
    text = re.sub(r"\s+", " ", text)
    stop_words = {
        "flights", "flight", "airline", "airlines", "airport", "airports",
        "ticket", "tickets", "fare", "fares", "price", "prices", "cost",
        "costs", "travel", "travelling", "trip", "trips", "journey",
        "journeys", "hotel", "hotels", "accommodation", "stay", "stays",
        "booking", "bookings", "reservation", "reservations", "tourism",
        "tourist", "tourists", "vacation", "vacations", "holiday", "holidays",
        "info", "information", "details", "detail", "guide", "guides",
        "advice", "advices", "recommendation", "recommendations", "suggestion",
        "suggestions", "review", "reviews", "rating", "ratings", "feedback",
        "feedbacks", "experience", "experiences",
    }

    words = [w for w in text.split() if w not in stop_words]
    return " ".join(words).strip()



def country_name_to_code(text: str):
    text = clean_text(text)

    for alias, code in COUNTRY_ALIASES.items():
        if clean_text(alias) == text:
            return code

    try:
        country = pycountry.countries.lookup(text)
        return country.alpha2
    except LookupError:
        pass

    return None

def airport_country_matches(airport: dict , country_code:str) -> bool:
    country_code = country_code.upper().strip()
    airport_country = str(
        airport.get("country_code") or airport.get("country") or ""
    ).strip()

    if airport_country.upper() == country_code:
        return True

    country = pycountry.countries.get(alpha_2=country_code)
    return bool(country and airport_country.casefold() == country.name.casefold())


def get_best_airport_for_country(country_code: str):
    country_code = country_code.upper().strip()
    preferred = next(
        (
            airport_code
            for country_name, airport_code in COUNTRY_MAIN_AIRPORTS.items()
            if country_name_to_code(country_name) == country_code
        ),
        None,
    )

    if preferred and preferred in AIRPORTS:
        return preferred

    candidates = []
    for iata, airport in AIRPORTS.items():
        if iata and airport_country_matches(airport, country_code):
            name = str(airport.get("name", "")).casefold()
            score = 1 if "international" in name else 0
            candidates.append((score, iata))

    return max(
        candidates,
        default=(0, None),
        key=lambda candidate: (candidate[0], candidate[1]),
    )[1]
    




























