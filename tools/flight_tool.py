import os
import re
import certifi
import airportsdata
import pycountry
import requests
import unicodedata
from typing import Optional
from dotenv import load_dotenv

load_dotenv()

os.environ["SSL_CERT_FILE"] = certifi.where()
os.environ["REQUESTS_CA_BUNDLE"] = certifi.where()

API_KEY = os.getenv("AVIATIONSTACK_API_KEY")

DEFAULT_ORIGIN_DATA = os.getenv("DEFAULT_ORIGIN_DATA")

BASE_URL = "http://api.aviationstack.com/v1/flights"

AIRPORTS = airportsdata.load("IATA")

COUNTRY_ALIASES = {
    "india": "IN",
    "ind": "IN",
    "bharat": "IN",

    "united states": "US",
    "usa": "US",
    "us": "US",
    "america": "US",

    "united kingdom": "GB",
    "uk": "GB",
    "britain": "GB",
    "england": "GB",

    "canada": "CA",
    "australia": "AU",
    "new zealand": "NZ",

    "france": "FR",
    "germany": "DE",
    "italy": "IT",
    "spain": "ES",
    "portugal": "PT",
    "netherlands": "NL",
    "holland": "NL",
    "belgium": "BE",
    "switzerland": "CH",
    "austria": "AT",
    "ireland": "IE",
    "greece": "GR",

    "japan": "JP",
    "china": "CN",
    "south korea": "KR",
    "korea": "KR",
    "singapore": "SG",
    "thailand": "TH",
    "malaysia": "MY",
    "indonesia": "ID",
    "vietnam": "VN",
    "philippines": "PH",

    "uae": "AE",
    "united arab emirates": "AE",
    "dubai": "AE",

    "saudi arabia": "SA",
    "qatar": "QA",
    "turkey": "TR",
    "egypt": "EG",
    "south africa": "ZA",

    "brazil": "BR",
    "mexico": "MX",
    "argentina": "AR",

    "russia": "RU",
    "ukraine": "UA",
    "poland": "PL",
    "sweden": "SE",
    "norway": "NO",
    "denmark": "DK",
    "finland": "FI",

    # In COUNTRY_ALIASES
    "bangladesh": "BD",
    "bd": "BD",
        
    
}


COUNTRY_MAIN_AIRPORTS = {
    "IN": "DEL",  # Indira Gandhi International Airport, Delhi, India
    "US": "ATL",  # Hartsfield-Jackson Atlanta International Airport, USA
    "GB": "LHR",  # Heathrow Airport, London, UK
    "CA": "YYZ",  # Toronto Pearson International Airport, Canada
    "AU": "SYD",  # Sydney Kingsford Smith Airport, Australia
    "NZ": "AKL",  # Auckland Airport, New Zealand

    "FR": "CDG",  # Charles de Gaulle Airport, Paris, France
    "DE": "FRA",  # Frankfurt Airport, Germany
    "IT": "FCO",  # Leonardo da Vinci–Fiumicino Airport, Rome, Italy
    "ES": "MAD",  # Adolfo Suárez Madrid–Barajas Airport, Spain
    "PT": "LIS",  # Humberto Delgado Airport, Lisbon, Portugal
    "NL": "AMS",  # Amsterdam Schiphol Airport, Netherlands
    "BE": "BRU",  # Brussels Airport, Belgium
    "CH": "ZRH",  # Zurich Airport, Switzerland
    "AT": "VIE",  # Vienna International Airport, Austria
    "IE": "DUB",  # Dublin Airport, Ireland
    "GR": "ATH",  # Athens International Airport, Greece

    "JP": "NRT",  # Narita International Airport, Tokyo, Japan
    "CN": "PEK",  # Beijing Capital International Airport, China
    "KR": "ICN",  # Incheon International Airport, South Korea
    "SG": "SIN",  # Singapore Changi Airport, Singapore
    "TH": "BKK",  # Suvarnabhumi Airport, Bangkok, Thailand
    "MY": "KUL",  # Kuala Lumpur International Airport, Malaysia
    "ID": "CGK",  # Soekarno-Hatta International Airport, Indonesia
    "VN": "SGN",  # Tan Son Nhat International Airport, Vietnam
    "PH": "MNL",  # Ninoy Aquino International Airport, Philippines

    "AE": "DXB",  # Dubai International Airport, UAE
    "SA": "JED",  # King Abdulaziz International Airport, Jeddah, Saudi Arabia
    "QA": "DOH",  # Hamad International Airport, Doha, Qatar
    "TR": "IST",  # Istanbul Airport, Türkiye
    "EG": "CAI",  # Cairo International Airport, Egypt
    "ZA": "JNB",  # O. R. Tambo International Airport, South Africa

    "BR": "GRU",  # São Paulo/Guarulhos International Airport, Brazil
    "MX": "MEX",  # Mexico City International Airport, Mexico
    "AR": "EZE",  # Ministro Pistarini International Airport, Argentina

    "RU": "SVO",  # Sheremetyevo International Airport, Russia
    "UA": "KBP",  # Boryspil International Airport, Ukraine
    "PL": "WAW",  # Warsaw Chopin Airport, Poland
    "SE": "ARN",  # Stockholm Arlanda Airport, Sweden
    "NO": "OSL",  # Oslo Airport, Norway
    "DK": "CPH",  # Copenhagen Airport, Denmark
    "FI": "HEL",  # Helsinki Airport, Finland

    "BD": "DAC",  # Hazrat Shahjalal International Airport, Dhaka
}

CITY_MAIN_AIRPORTS = {
    # India
    "delhi": "DEL",
    "new delhi": "DEL",
    "mumbai": "BOM",
    "bombay": "BOM",
    "bangalore": "BLR",
    "bengaluru": "BLR",
    "hyderabad": "HYD",
    "chennai": "MAA",
    "kolkata": "CCU",
    "calcutta": "CCU",
    "ahmedabad": "AMD",
    "pune": "PNQ",
    "goa": "GOI",
    "kochi": "COK",
    "cochin": "COK",
    "jaipur": "JAI",
    "lucknow": "LKO",
    "varanasi": "VNS",
    "amritsar": "ATQ",
    "chandigarh": "IXC",
    "patna": "PAT",
    "bhubaneswar": "BBI",
    "guwahati": "GAU",
    "indore": "IDR",
    "nagpur": "NAG",
    "surat": "STV",
    "srinagar": "SXR",
    "dehradun": "DED",

    # United States
    "new york": "JFK",
    "los angeles": "LAX",
    "san francisco": "SFO",
    "chicago": "ORD",
    "boston": "BOS",
    "washington": "IAD",
    "miami": "MIA",
    "las vegas": "LAS",
    "seattle": "SEA",
    "atlanta": "ATL",
    "dallas": "DFW",
    "houston": "IAH",
    "orlando": "MCO",

    # United Kingdom
    "london": "LHR",
    "manchester": "MAN",
    "birmingham": "BHX",
    "edinburgh": "EDI",
    "glasgow": "GLA",

    # France
    "paris": "CDG",
    "nice": "NCE",
    "lyon": "LYS",
    "marseille": "MRS",

    # Germany
    "berlin": "BER",
    "frankfurt": "FRA",
    "munich": "MUC",
    "hamburg": "HAM",

    # Italy
    "rome": "FCO",
    "milan": "MXP",
    "venice": "VCE",
    "florence": "FLR",

    # Spain
    "madrid": "MAD",
    "barcelona": "BCN",
    "seville": "SVQ",

    # Netherlands
    "amsterdam": "AMS",
    "rotterdam": "RTM",

    # Switzerland
    "zurich": "ZRH",
    "geneva": "GVA",

    # Austria
    "vienna": "VIE",
    "salzburg": "SZG",

    # Portugal
    "lisbon": "LIS",
    "porto": "OPO",

    # Greece
    "athens": "ATH",
    "thessaloniki": "SKG",

    # Ireland
    "dublin": "DUB",

    # Canada
    "toronto": "YYZ",
    "vancouver": "YVR",
    "montreal": "YUL",
    "calgary": "YYC",

    # Australia
    "sydney": "SYD",
    "melbourne": "MEL",
    "brisbane": "BNE",
    "perth": "PER",

    # New Zealand
    "auckland": "AKL",
    "wellington": "WLG",
    "christchurch": "CHC",

    # Japan
    "tokyo": "NRT",
    "osaka": "KIX",
    "kyoto": "KIX",
    "nagoya": "NGO",

    # China
    "beijing": "PEK",
    "shanghai": "PVG",
    "guangzhou": "CAN",
    "shenzhen": "SZX",

    # South Korea
    "seoul": "ICN",
    "busan": "PUS",

    # Southeast Asia
    "singapore": "SIN",
    "bangkok": "BKK",
    "phuket": "HKT",
    "kuala lumpur": "KUL",
    "jakarta": "CGK",
    "bali": "DPS",
    "ho chi minh city": "SGN",
    "hanoi": "HAN",
    "manila": "MNL",

    # Middle East
    "dubai": "DXB",
    "abu dhabi": "AUH",
    "doha": "DOH",
    "riyadh": "RUH",
    "jeddah": "JED",
    "istanbul": "IST",
    "ankara": "ESB",

    # Egypt & Africa
    "cairo": "CAI",
    "johannesburg": "JNB",
    "cape town": "CPT",
    "nairobi": "NBO",

    # South America
    "sao paulo": "GRU",
    "são paulo": "GRU",
    "rio de janeiro": "GIG",
    "buenos aires": "EZE",

    # Mexico
    "mexico city": "MEX",
    "cancun": "CUN",

    # Russia & Eastern Europe
    "moscow": "SVO",
    "warsaw": "WAW",
    "prague": "PRG",
    "budapest": "BUD",

}

def clean_text(text: str) -> str:
    """
    Clean and normalize user input for city/country matching.

    Steps:
    1. Validate input type.
    2. Normalize Unicode characters.
    3. Convert to lowercase.
    4. Replace unwanted punctuation/symbols with spaces.
    5. Normalize multiple spaces.
    6. Remove leading/trailing whitespace.

    Example:
        "  New   York!!!  " -> "new york"
        " São   Paulo "     -> "são paulo"
        "  INDIA  "         -> "india"
    """

    if not isinstance(text, str):
        raise TypeError("text must be a string")

    # Normalize Unicode representation
    text = unicodedata.normalize("NFKC", text)

    # Convert to lowercase
    text = text.lower()

    # Replace punctuation/special symbols with spaces
    # Keep letters, numbers, and whitespace.
    text = re.sub(r"[^\w\s]", " ", text, flags=re.UNICODE)

    # Replace multiple spaces/tabs/newlines with one space
    text = re.sub(r"\s+", " ", text)

    # Remove leading/trailing whitespace
    text = text.strip()

    return text


def country_name_to_code(text : str):
    text = clean_text(text)

    if text in COUNTRY_ALIASES:
        return COUNTRY_ALIASES[text]

    try:
        country = pycountry.countries.lookup(text)
        return country.alpha_2
    except LookupError:
        pass

    # detect country name inside the longer text

    for country in pycountry.countries:
        country_name = clean_text(country.name)
        if country_name in text:
            return country.alpha_2

    for alias, code in COUNTRY_ALIASES.items():
        if alias in text:
            return code

    return None



def airport_country_matches(airport: dict, country_code: str) -> bool:

    """airport_country_matches() is intended to check whether an airport belongs to a specified country."""

    airport_country = str(airport.get("country", "")).strip()
    country_code = country_code.strip().upper()

    # Case 1: Airport already contains a country code (e.g., IN)
    if airport_country.upper() == country_code:
        return True

    # Case 2: Airport contains a country name (e.g., India)
    try:
        country = pycountry.countries.get(alpha_2=country_code)

        if country and airport_country.casefold() == country.name.casefold():
            return True

    except (LookupError, AttributeError):
        pass

    return False



def get_best_airport_for_country(country_code: str):

    # This function is designed to identify the most suitable airport for a given country code. It first checks if there is a preferred airport for the country in the COUNTRY_MAIN_AIRPORTS dictionary. If a preferred airport exists and is present in the AIRPORTS dataset, it returns that airport's IATA code.

    country_code = country_code.strip().upper()

    preferred = COUNTRY_MAIN_AIRPORTS.get(country_code)

    if preferred and preferred in AIRPORTS:
        return preferred

    candidates = []

    for iata, airport in AIRPORTS.items():
        if not iata:
            continue

        if airport_country_matches(airport, country_code):
            name = str(airport.get("name", "")).lower()
            city = str(airport.get("city", "")).lower()

            score = 0

            if "international" in name:
                score += 50

            if "intl" in name:
                score += 40

            if "capital" in name:
                score += 20

            if city and city in name:
                score += 5

            candidates.append((score, iata))

    if not candidates:
        return None

    candidates.sort(reverse=True)

    return candidates[0][1]





def resolve_location_to_iata(location: str) -> Optional[str]:
    """
    Resolve a city, country, or airport IATA code to an airport IATA code.

    Examples:
        "DEL"   -> "DEL"
        "Delhi" -> "DEL"  (if configured or found in AIRPORTS)
        "India" -> country's preferred airport
        ""      -> None
    """
    if not location or not location.strip():
        return None

    raw_location = location.strip()
    location_clean = clean_text(raw_location)

    if not location_clean:
        return None

    # 1. Direct IATA code lookup
    code = raw_location.upper()

    if re.fullmatch(r"[A-Za-z]{3}", raw_location):
        if code in AIRPORTS:
            return code

    # 2. Preferred airport for a city
    if location_clean in CITY_MAIN_AIRPORTS:
        airport_code = CITY_MAIN_AIRPORTS[location_clean]

        if airport_code in AIRPORTS:
            return airport_code

    # 3. Preferred airport for a country
    country_code = country_name_to_code(location_clean)

    if country_code:
        airport_code = get_best_airport_for_country(country_code)

        if airport_code:
            return airport_code

    # 4. Search airports by city or airport name
    city_matches = []

    for iata, airport in AIRPORTS.items():
        city = clean_text(str(airport.get("city", "")))
        name = clean_text(str(airport.get("name", "")))

        score = 0

        # Exact city match should be strongest
        if city == location_clean:
            score += 100

        # Partial city match
        elif location_clean in city:
            score += 70

        # Airport name match
        if location_clean in name:
            score += 50

        # Prefer international airports when scores otherwise differ
        if "international" in name:
            score += 20

        if score > 0:
            city_matches.append((score, iata))

    if city_matches:
        city_matches.sort(reverse=True)
        return city_matches[0][1]

    return None




def find_location_mentions(query: str):
    """Find known country and city names in the order they appear."""
    q = clean_text(query)
    candidates = set(COUNTRY_ALIASES) | set(CITY_MAIN_AIRPORTS)

    for country in pycountry.countries:
        candidates.add(clean_text(country.name))
        if hasattr(country, "official_name"):
            candidates.add(clean_text(country.official_name))

    matches = []

    for name in candidates:
        if not name:
            continue

        pattern = rf"(?<!\w){re.escape(name)}(?!\w)"
        for match in re.finditer(pattern, q):
            matches.append((match.start(), match.end(), name))

    # Prefer longer names when matches overlap, e.g. "New Delhi" over "Delhi".
    matches.sort(key=lambda item: (item[0], -(item[1] - item[0])))

    results = []
    last_end = -1

    for start, end, name in matches:
        if start < last_end:
            continue
        results.append(name)
        last_end = end

    return results



def parse_route(query: str):
    """
    Return (departure_iata, arrival_iata).

    Examples:
        'flights from Delhi to Tokyo' -> ('DEL', 'NRT')
        'flights to Japan from Bangladesh' -> ('DAC', 'NRT')
        'Plan a 7 days Japan trip from Bangladesh' -> ('DAC', 'NRT')
        'flights from Mumbai' -> ('BOM', None)
        'flights to London' -> (None, 'LHR')
    """
    if not isinstance(query, str):
        return None, None

    q = query.strip()
    q_lower = q.lower()

    global_keywords = (
        "all country", "all countries", "global flight",
        "global flights", "all flight", "all flights",
        "worldwide flight", "worldwide flights",
    )

    if any(keyword in q_lower for keyword in global_keywords):
        return None, None

    # Recognize only valid IATA codes.
    codes = [
        code for code in re.findall(r"\b[A-Za-z]{3}\b", q)
        if code.upper() in AIRPORTS
    ]

    if len(codes) >= 2:
        return codes[0].upper(), codes[1].upper()

    # Explicit "from X to Y".
    match = re.search(
        r"\bfrom\s+(.+?)\s+to\s+(.+?)"
        r"(?=\s+(?:on|for|under|including|with|in|at)\b|[.!?]|$)",
        q_lower,
    )

    if match:
        return (
            resolve_location_to_iata(match.group(1)),
            resolve_location_to_iata(match.group(2)),
        )

    # Explicit "to Y from X".
    match = re.search(
        r"\bto\s+(.+?)\s+from\s+(.+?)"
        r"(?=\s+(?:on|for|under|including|with|in|at)\b|[.!?]|$)",
        q_lower,
    )

    if match:
        return (
            resolve_location_to_iata(match.group(2)),
            resolve_location_to_iata(match.group(1)),
        )

    mentions = find_location_mentions(q)

    # Handle queries such as "Japan trip from Bangladesh".
    from_match = re.search(r"\bfrom\s+(.+?)(?:[.!?]|$)", q_lower)

    if from_match:
        origin_text = from_match.group(1)
        dep_iata = resolve_location_to_iata(origin_text)

        if dep_iata:
            other_mentions = [
                place for place in mentions
                if place not in clean_text(origin_text)
            ]

            if other_mentions:
                return dep_iata, resolve_location_to_iata(other_mentions[0])

            return dep_iata, None

    # Handle queries such as "flights to Japan".
    to_match = re.search(r"\bto\s+(.+?)(?:[.!?]|$)", q_lower)

    if to_match:
        arr_iata = resolve_location_to_iata(to_match.group(1))
        if arr_iata:
            return None, arr_iata

    # Fall back to locations mentioned in the query.
    if len(mentions) >= 2:
        return (
            resolve_location_to_iata(mentions[0]),
            resolve_location_to_iata(mentions[1]),
        )

    if len(mentions) == 1:
        destination = resolve_location_to_iata(mentions[0])
        origin = resolve_location_to_iata(DEFAULT_ORIGIN_DATA or "")
        return origin, destination

    return None, None


def format_flight(flight: dict):
    if not isinstance(flight, dict):
      return "Invalid flight record received from API."

    airline_data = flight.get("airline") or {}
    flight_data = flight.get("flight") or {}
    dep = flight.get("departure") or {}
    arr = flight.get("arrival") or {}

    if not isinstance(airline_data, dict):
        airline_data = {}
    if not isinstance(flight_data, dict):
        flight_data = {}
    if not isinstance(dep, dict):
        dep = {}
    if not isinstance(arr, dict):
        arr = {}

    airline = airline_data.get("name") or "Unknown airline"
    flight_number = flight_data.get("iata") or "Unknown flight number"
    status = flight.get("flight_status") or "Unknown"

    dep = flight.get("departure", {}) or {}
    arr = flight.get("arrival", {}) or {}

    dep_airport = dep.get("airport") or "Unknown departure airport"
    dep_iata = dep.get("iata") or "Unknown"
    dep_terminal = dep.get("terminal") or "N/A"
    dep_gate = dep.get("gate") or "N/A"
    dep_scheduled = dep.get("scheduled") or "Unknown"
    dep_delay = dep.get("delay")
    dep_delay_text = f"{dep_delay} minutes" if dep_delay is not None else "N/A"

    arr_airport = arr.get("airport") or "Unknown arrival airport"
    arr_iata = arr.get("iata") or "Unknown"
    arr_terminal = arr.get("terminal") or "N/A"
    arr_gate = arr.get("gate") or "N/A"
    arr_scheduled = arr.get("scheduled") or "Unknown"
    arr_delay = arr.get("delay")
    arr_delay_text = f"{arr_delay} minutes" if arr_delay is not None else "N/A"

    return f"""
Airline: {airline}
Flight: {flight_number}
Status: {status}

Departure:
- Airport: {dep_airport}
- IATA: {dep_iata}
- Terminal: {dep_terminal}
- Gate: {dep_gate}
- Scheduled: {dep_scheduled}
- Delay: {dep_delay_text}

Arrival:
- Airport: {arr_airport}
- IATA: {arr_iata}
- Terminal: {arr_terminal}
- Gate: {arr_gate}
- Scheduled: {arr_scheduled}
- Delay: {arr_delay_text}
""".strip()


def search_flights(query: str, limit: int = 10):

    if isinstance(limit, bool) or not isinstance(limit, int) or limit < 1:
        return "limit must be a positive integer."

    limit = min(limit, 100)
    if not API_KEY:
        return (
            "Flight API error: AVIATIONSTACK_API_KEY is missing.\n"
            "Please add this in your .env file:\n"
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
            timeout=30,
        )
        response.raise_for_status()
        data = response.json()

    except requests.exceptions.RequestException as e:
        return f"Flight API request failed: {e}"

    except ValueError:
        return "Flight API returned invalid JSON."

    if not isinstance(data, dict):
        return "Flight API returned an unexpected response format."

    error = data.get("error")
    if error:
        if not isinstance(error, dict):
            return f"Flight API error: {error}"

        return (
            "Flight API error:\n"
            f"Code: {error.get('code', 'Unknown')}\n"
            f"Message: {error.get('message', 'Unknown error')}"
        )

    flight_data = data.get("data") or []

    if not isinstance(flight_data, list):
        return "Flight API returned an invalid flight-data format."

    if not flight_data:
        route_text = ""

        if dep_iata and arr_iata:
            route_text = f" for route {dep_iata} to {arr_iata}"
        elif dep_iata:
            route_text = f" from {dep_iata}"
        elif arr_iata:
            route_text = f" to {arr_iata}"

        return (
            f"No live flight data found{route_text}.\n\n"
            "Note: AviationStack provides live/status flight data, not ticket prices. "
            "For actual fare prices, use a flight-pricing API such as Amadeus."
        )

    route_info = "Global live flights"

    if dep_iata and arr_iata:
        route_info = f"Live flights from {dep_iata} to {arr_iata}"
    elif dep_iata:
        route_info = f"Live flights from {dep_iata}"
    elif arr_iata:
        route_info = f"Live flights to {arr_iata}"

    formatted_flights = [format_flight(flight) for flight in flight_data[:limit]]

    return f"{route_info}\n\n" + "\n\n---\n\n".join(formatted_flights)


if __name__ == "__main__":
    test_queries = [
        "Plan a 7 days Japan trip from Bangladesh",
        "flights from Delhi to Tokyo",
        "flights to Japan from Bangladesh",
        "flights from Mumbai to London",
        "DAC to NRT",
        "all country flight info",
    ]

    for query in test_queries:
        print(query, "->", parse_route(query))