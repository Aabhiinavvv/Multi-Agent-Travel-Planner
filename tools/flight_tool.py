import os
import re
import certifi
import airportsdata
import pycountry
import requests

from dotenv import load_dotenv




load_dotenv()


os.environ["SSL_CERT_FILE"] = certifi.where()
os.environ["REQUESTS_CA_BUNDLE"] = certifi.where()


API_KEY = (
    os.getenv("AVIATION_API_KEY")
    or os.getenv("AVIATIONSTACK_API_KEY")
)

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
    "Britain": "GB",
    "England": "GB",

    "Canada": "CA",
    "Australia": "AU",

    "UAE": "AE",
    "Dubai": "AE",

    "Singapore": "SG",
    "South Korea": "KR",
    "Korea": "KR",
    "Russia": "RU",
    "Vietnam": "VN",
    "Bangladesh": "BD",
    "India": "IN",
    "Japan": "JP",
    "China": "CN",
    "Malaysia": "MY",
    "Indonesia": "ID",
    "Netherlands": "NL",
    "Nepal": "NP",
    "Thailand": "TH",
    "Qatar": "QA",
    "Saudi Arabia": "SA",
    "Turkey": "TR",
    "France": "FR",
    "Brazil": "BR",
    "New Zealand": "NZ",
    "Germany": "DE",
    "Italy": "IT",
}



CITY_MAIN_AIRPORT = {
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
    "Vijayawada": "VGA",
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
    "Finland": "HEL",
}


def clean_text(text: str) -> str:
    """
    Clean text by:
    1. Converting to lowercase
    2. Removing special characters
    3. Removing extra spaces
    4. Removing common travel-related words
    """

    text = str(text).lower().strip()

    # Remove special characters
    text = re.sub(r"[^a-zA-Z0-9\s]", "", text)

    # Replace multiple spaces with one
    text = re.sub(r"\s+", " ", text)

    stop_words = {
        "flights",
        "flight",
        "airline",
        "airlines",
        "airport",
        "airports",
        "ticket",
        "tickets",
        "fare",
        "fares",
        "price",
        "prices",
        "cost",
        "costs",
        "travel",
        "travelling",
        "trip",
        "trips",
        "journey",
        "journeys",
        "hotel",
        "hotels",
        "accommodation",
        "stay",
        "stays",
        "booking",
        "bookings",
        "reservation",
        "reservations",
        "tourism",
        "tourist",
        "tourists",
        "vacation",
        "vacations",
        "holiday",
        "holidays",
        "info",
        "information",
        "details",
        "detail",
        "guide",
        "guides",
        "advice",
        "advices",
        "recommendation",
        "recommendations",
        "suggestion",
        "suggestions",
        "review",
        "reviews",
        "rating",
        "ratings",
        "feedback",
        "feedbacks",
        "experience",
        "experiences",
    }

    words = [
        word
        for word in text.split()
        if word not in stop_words
    ]

    return " ".join(words).strip()




def country_name_to_code(text: str):
    """
    Convert country name/alias into ISO Alpha-2 country code.

    Examples:
        India -> IN
        USA -> US
        Bangladesh -> BD
        Japan -> JP
    """

    text = clean_text(text)

    if not text:
        return None

    # Check custom aliases
    for alias, code in COUNTRY_ALIASES.items():
        if clean_text(alias) == text:
            return code

    # Try pycountry
    try:
        country = pycountry.countries.lookup(text)
        return country.alpha2

    except LookupError:
        pass

    return None




def airport_country_matches(
    airport: dict,
    country_code: str
) -> bool:

    country_code = str(country_code).upper().strip()

    airport_country = str(
        airport.get("country_code")
        or airport.get("country")
        or ""
    ).strip()

    # Direct country-code comparison
    if airport_country.upper() == country_code:
        return True

    # If airport contains country name instead of country code
    country = pycountry.countries.get(
        alpha_2=country_code
    )

    return bool(
        country
        and airport_country.casefold() == country.name.casefold()
    )



def get_best_airport_for_country(country_code: str):
    """
    Find the best/main airport for a country.
    """

    country_code = str(country_code).upper().strip()

  

    preferred = None

    for country_name, airport_code in COUNTRY_MAIN_AIRPORTS.items():

        if country_name_to_code(country_name) == country_code:
            preferred = airport_code
            break

    if preferred and preferred in AIRPORTS:
        return preferred


    candidates = []

    for iata, airport in AIRPORTS.items():

        if not iata:
            continue

        if not airport_country_matches(
            airport,
            country_code
        ):
            continue

        name = str(
            airport.get("name", "")
        ).lower()

        score = 0

        if "international" in name:
            score += 50

        if "intl" in name:
            score += 40

        if "capital" in name:
            score += 20

        if "city" in name:
            score += 5

        if score > 0:
            candidates.append((score, iata))

    # No candidate found
    if not candidates:
        return None

    # Highest score first
    candidates.sort(reverse=True)

    return candidates[0][1]




def resolve_location_to_iata(location: str):
    """
    Convert country/city/airport/IATA into IATA code.

    Examples:
        Bangladesh -> DAC
        Japan      -> HND
        Dhaka      -> DAC
        Tokyo      -> HND
        DAC        -> DAC
    """

    if not location:
        return None

    raw_location = str(location).strip()

    if not raw_location:
        return None



    if re.fullmatch(
        r"[A-Z]{3}",
        raw_location.upper()
    ):

        code = raw_location.upper()

        if code in AIRPORTS:
            return code

   

    location_clean = clean_text(raw_location)

    if not location_clean:
        return None



    for city, iata in CITY_MAIN_AIRPORT.items():

        if clean_text(city) == location_clean:

            if iata in AIRPORTS:
                return iata



    country_code = country_name_to_code(
        location_clean
    )

    if country_code:

        airport = get_best_airport_for_country(
            country_code
        )

        if airport:
            return airport


    city_matches = []

    for iata, airport in AIRPORTS.items():

        if not iata:
            continue

        city = str(
            airport.get("city", "")
        ).lower().strip()

        name = str(
            airport.get("name", "")
        ).lower().strip()

        score = 0

        # Exact city match
        if city == location_clean:
            score += 100

        # Partial city match
        elif location_clean in city:
            score += 70

        # Location appears in airport name
        if location_clean in name:
            score += 50

        # International airport bonus
        if "international" in name:
            score += 10

        if score > 0:
            city_matches.append(
                (score, iata)
            )



    if city_matches:

        city_matches.sort(reverse=True)

        return city_matches[0][1]

    return None




def find_location_mentions(query: str):
    """
    Find country/city names mentioned inside a natural-language query.
    """

    q = str(query).lower()

    mentions = []

    

    for alias in COUNTRY_ALIASES:

        pattern = rf"\b{re.escape(alias.lower())}\b"

        if re.search(pattern, q):
            mentions.append(alias)

    

    for country in pycountry.countries:

        name = country.name.lower()

        pattern = rf"\b{re.escape(name)}\b"

        if re.search(pattern, q):
            mentions.append(country.name)

    

    for city in CITY_MAIN_AIRPORT:

        pattern = rf"\b{re.escape(city.lower())}\b"

        if re.search(pattern, q):
            mentions.append(city)

    

    unique_mentions = []

    for item in mentions:

        if item not in unique_mentions:
            unique_mentions.append(item)

    return unique_mentions



def parse_route(query: str):
    """
    Extract departure and arrival IATA codes
    from a natural language query.

    Examples:

        "flights from Delhi to Mumbai"
            -> DEL, BOM

        "flights from DAC to DEL"
            -> DAC, DEL

        "flights to Tokyo"
            -> None, HND
    """

    q = str(query).strip()
    q_lower = q.lower()

    if not q:
        return None, None

    

    global_keywords = [
        "all country",
        "all countries",
        "global flights",
        "global flight",
        "all flights",
        "all flight",
        "worldwide flights",
        "worldwide flight",
    ]

    if any(
        keyword in q_lower
        for keyword in global_keywords
    ):
        return None, None



    codes = re.findall(
        r"\b[A-Z]{3}\b",
        q
    )

    valid_codes = [
        code.upper()
        for code in codes
        if code.upper() in AIRPORTS
    ]

    if len(valid_codes) >= 2:

        return (
            valid_codes[0],
            valid_codes[1]
        )

 

    match = re.search(
        r"\bfrom\s+(.+?)\s+to\s+(.+?)(?:"
        r"\s+(?:on|for|under|including|with|in|at)\b"
        r"|[.!?]"
        r"|$)",
        q_lower,
    )

    if match:

        origin_text = match.group(1).strip()
        dest_text = match.group(2).strip()

        dep_iata = resolve_location_to_iata(
            origin_text
        )

        arr_iata = resolve_location_to_iata(
            dest_text
        )

        return dep_iata, arr_iata

    

    match = re.search(
        r"\bto\s+(.+?)(?:[.!?]|$)",
        q_lower,
    )

    if match:

        dest_text = match.group(1).strip()

        arr_iata = resolve_location_to_iata(
            dest_text
        )

        return None, arr_iata

    
    mentions = find_location_mentions(q)

    if len(mentions) >= 2:

        dep_iata = resolve_location_to_iata(
            mentions[0]
        )

        arr_iata = resolve_location_to_iata(
            mentions[1]
        )

        return dep_iata, arr_iata

   

    if len(mentions) == 1:

        arr_iata = resolve_location_to_iata(
            mentions[0]
        )

        return (
            DEFAULT_ORIGIN_IATA,
            arr_iata
        )

    return None, None



def format_flight(flight: dict):
    """
    Convert raw AviationStack flight data
    into readable text.
    """

    airline_data = flight.get("airline", {}) or {}
    flight_data = flight.get("flight", {}) or {}

    airline = (
        airline_data.get("name")
        or "Unknown airline"
    )

    flight_number = (
        flight_data.get("iata")
        or "Unknown flight number"
    )

    status = (
        flight.get("flight_status")
        or "Unknown"
    )

    dep = flight.get("departure", {}) or {}
    arr = flight.get("arrival", {}) or {}

    

    dep_airport = (
        dep.get("airport")
        or "Unknown departure airport"
    )

    dep_iata = (
        dep.get("iata")
        or "Unknown"
    )

    dep_terminal = (
        dep.get("terminal")
        or "N/A"
    )

    dep_gate = (
        dep.get("gate")
        or "N/A"
    )

    dep_scheduled = (
        dep.get("scheduled")
        or "Unknown"
    )

    dep_delayed = dep.get("delayed")

    if dep_delayed:
        dep_delayed_text = (
            f"{dep_delayed} minutes"
        )
    else:
        dep_delayed_text = "On time"

    
    arr_airport = (
        arr.get("airport")
        or "Unknown arrival airport"
    )

    arr_iata = (
        arr.get("iata")
        or "Unknown"
    )

    arr_terminal = (
        arr.get("terminal")
        or "N/A"
    )

    arr_gate = (
        arr.get("gate")
        or "N/A"
    )

    arr_scheduled = (
        arr.get("scheduled")
        or "Unknown"
    )

    arr_delayed = arr.get("delayed")

    if arr_delayed:
        arr_delayed_text = (
            f"{arr_delayed} minutes"
        )
    else:
        arr_delayed_text = "On time"

    
    return f"""
Airline: {airline}
Flight: {flight_number}
Status: {status}

Departure:
    Airport: {dep_airport} ({dep_iata})
    Terminal: {dep_terminal}
    Gate: {dep_gate}
    Scheduled: {dep_scheduled}
    Delay: {dep_delayed_text}

Arrival:
    Airport: {arr_airport} ({arr_iata})
    Terminal: {arr_terminal}
    Gate: {arr_gate}
    Scheduled: {arr_scheduled}
    Delay: {arr_delayed_text}
""".strip()



def search_flights(
    query: str,
    limit: int = 10
):
    """
    Search live flights using AviationStack.
    """

    

    if not API_KEY:

        return (
            "Flight API Error: AviationStack API key is missing.\n\n"
            "Add one of these to your .env file:\n"
            "AVIATION_API_KEY=your_api_key_here\n"
            "or\n"
            "AVIATIONSTACK_API_KEY=your_api_key_here"
        )

    

    dep_iata, arr_iata = parse_route(query)

    

    params = {
        "access_key": API_KEY,
        "limit": min(limit, 100),
    }

    if dep_iata:
        params["dep_iata"] = dep_iata

    if arr_iata:
        params["arr_iata"] = arr_iata

    
    try:

        response = requests.get(
            BASE_URL,
            params=params,
            timeout=30
        )

        response.raise_for_status()

        data = response.json()

    except requests.exceptions.RequestException as e:

        return (
            f"Flight API request failed: {e}"
        )

    except ValueError:

        return (
            "Flight API returned invalid JSON."
        )

    

    if "error" in data:

        error = data["error"]

        return (
            "Flight API Error:\n"
            f"Code: {error.get('code', 'unknown')}\n"
            f"Message: "
            f"{error.get('message', 'unknown error')}"
        )

    # --------------------------------------------------------
    # Get flight data
    # --------------------------------------------------------

    flight_data = data.get(
        "data",
        []
    )

    if not flight_data:

        route_text = ""

        if dep_iata and arr_iata:

            route_text = (
                f" for route "
                f"{dep_iata} to {arr_iata}"
            )

        elif dep_iata:

            route_text = (
                f" from {dep_iata}"
            )

        elif arr_iata:

            route_text = (
                f" to {arr_iata}"
            )

        return (
            f"No live flight data found{route_text}.\n\n"
            "Note: AviationStack provides live/status "
            "flight data, not ticket prices. "
            "For actual fare prices, use a flight-pricing "
            "API such as Amadeus."
        )

    

    route_info = "Global live flights"

    if dep_iata and arr_iata:

        route_info = (
            f"Live flights from "
            f"{dep_iata} to {arr_iata}"
        )

    elif dep_iata:

        route_info = (
            f"Live flights from {dep_iata}"
        )

    elif arr_iata:

        route_info = (
            f"Live flights to {arr_iata}"
        )

    
    formatted_flights = [
        format_flight(flight)
        for flight in flight_data[:limit]
    ]

    return (
        f"{route_info}\n\n"
        + "\n\n---\n\n".join(
            formatted_flights
        )

        
    )


                


            








    



    

    