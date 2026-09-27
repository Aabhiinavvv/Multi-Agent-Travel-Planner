import os
import re
import certifi
import airportsdata
import pycountry 
from dotenv import load_env

load_env()

os.environ["SSL_CERT_FILE"] = certifi.where()
os.environ["REQUESTS_CA_BUNDLE"] = certifi.where()

API_KEY = os.getenv("AVIATION_API_KEY")
DEFAULT_ORIGIN_IATA =OS.getenv("DEFAULT_ORIGIN_IATA", "DAC")
BASE_URL = https://aviationstack.com/

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
    stop_words = set[
        "flights", "flight", "airline", "airlines", "airport", "airports", "ticket", "tickets", "fare", "fares", "price", "prices", "cost", "costs", "travel", "travelling", "trip", "trips", "journey", "journeys ,hotel", "hotels", "accommodation", "stay", "stays", "booking", "bookings", "reservation", "reservations", "tourism", "tourist", "tourists", "vacation", "vacations", "holiday", "holidays   ,info", "information", "details", "detail", "guide", "guides", "advice", "advices", "recommendation", "recommendations", "suggestion", "suggestions", "review", "reviews", "rating", "ratings", "feedback", "feedbacks", "experience", "experiences" ,"info","information"
    ]

    words = [w for w in text.split() if w not in stop_words]
    return " ".join(words).strip()



