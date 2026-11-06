import re

COMMON_LOCATIONS = {
    "nagpur",
    "vadodara",
    "mumbai",
    "delhi",
    "ahmedabad",
    "surat",
    "pune",
    "bengaluru",
    "bangalore",
    "chennai",
    "hyderabad",
    "kolkata",
    "jaipur",
    "indore",
    "kanpur",
    "ludhiana",
    "rajkot",
    "morbi",
    "ghaziabad",
    "noida",
    "gurgaon",
    "gurugram",
    "faridabad",
    "nashik",
    "bhopal",
    "patna",
    "coimbatore",
    "lucknow",
    "raipur",
    "gwalior",
    "agra",
    "chandigarh",
    "jabalpur",
    "varanasi",
    "dubai",
}

IGNORE_WORDS = {
    "urgent",
    "chahiye",
    "bhaiya",
    "sir",
    "please",
    "plz",
    "fast",
    "asap",
    "price",
    "rate",
    "quote",
    "sample",
    "order",
    "best",
    "send",
    "bhejo",
    "needed",
    "required",
    "bags",
    "boxes",
    "cartons",
    "pcs",
    "plant",
    "warehouse",
}

def extract_category(text: str) -> str:
    t = text.lower()

    if any(k in t for k in ["film", "shrink", "stretch", "wrap"]):
        return "film"
    
    if "bopp" in t or "bop bag" in t or "bop" in t:
        return "bopp_bag"
    
    if any(k in t for k in ["fibc", "jumbo", "bulk bag"]):
        return "fibc"
    
    if any(k in t for k in ["woven", "cement bag", "ad star", "adstar"]):
        return "woven_sack"
    
    if "mono" in t:
        return "mono_carton"
    
    if any(k in t for k in ["corrugated", "corugated", "carton", "box"]):
        return "corrugated_box"
    
    if "pouch" in t:
        return "pouch"

    return "corrugated_box"

def normalize_indian_numbers(text: str) -> str:

    t = text.lower()

    t = re.sub(r"(\d+),(\d+)", r"\1\2", t)
    t = re.sub(r"(\d+),(\d+)", r"\1\2", t)

    def k_replace(match):
        num = float(match.group(1))
        return str(int(num * 1000))

    t = re.sub(r"(\d+(?:\.\d+)?)\s*k\b", k_replace, t)

    def hazar_replace(match):
        num = float(match.group(1))
        return str(int(num * 1000))

    t = re.sub(r"(\d+(?:\.\d+)?)\s*(?:hazaar|hazar)\b", hazar_replace, t)

    def lakh_replace(match):
        num = float(match.group(1))
        return str(int(num * 100000))

    t = re.sub(r"(\d+(?:\.\d+)?)\s*(?:lakh|lac|lacs)\b", lakh_replace, t)

    return t

def extract_quantity_and_unit(text: str) -> tuple:

    cleaned = normalize_indian_numbers(text)

    cleaned = re.sub(r"\d+(?:\.\d+)?\s*(?:kg|ton|mt)?\s*(?:capacity|cap)\b", "", cleaned)

    cleaned = re.sub(r"\b\d+(?:\.\d+)?\s*kg\b(?=.*?\b(?:bag|bags|sack|sacks)\b)", "", cleaned)

    cleaned = re.sub(r"\b\d+\s*gsm\b", "", cleaned)

    cleaned = re.sub(r"\b\d+\s*(?:mic|micron|microns)\b", "", cleaned)

    unit_pattern = (r"(\d+(?:\.\d+)?)\s*(pcs|pieces|nos|kg|kgs|ton|tonne|tonnes|mt)\b")

    match = re.search(unit_pattern, cleaned)

    if match:
        val = float(match.group(1))
        raw_unit = match.group(2)

        if raw_unit in ["ton", "tonne", "tonnes", "mt"]:
            unit = "mt"
        elif raw_unit in ["kg", "kgs"]:
            unit = "kg"
        else:
            unit = "pcs"

        quantity = int(val) if val.is_integer() else val
        return quantity, unit

    bare_pattern = r"\b(\d+(?:\.\d+)?)\b"
    bare_match = re.search(bare_pattern, cleaned)

    if bare_match:
        val = float(bare_match.group(1))
        quantity = int(val) if val.is_integer() else val
        return quantity, "pcs"

    return None, None

def extract_location(text: str) -> str | None:

    clean = text.strip()

    t_lower = clean.lower()
    for city in COMMON_LOCATIONS:
        # Match city as a complete standalone word
        if re.search(rf"\b{city}\b", t_lower):
            return city.capitalize()

    prep_match = re.search(r"\b(?:to|for|in|at|deliver|location)\s+([a-zA-Z]+)", clean, re.IGNORECASE)
    if prep_match:
        candidate = prep_match.group(1).strip()
        if candidate.lower() not in IGNORE_WORDS:
            return candidate.capitalize()

    # Pattern 3: Trailing location at the end after a comma (e.g., "... 65 gsm, Nagpur")
    comma_match = re.search(r",\s*([a-zA-Z]+)\s*$", clean)
    if comma_match:
        candidate = comma_match.group(1).strip()
        if candidate.lower() not in IGNORE_WORDS:
            return candidate.capitalize()

    words = clean.split()
    if words:
        last_word = re.sub(r"[^\w]", "", words[-1])
        if last_word.istitle() and last_word.lower() not in IGNORE_WORDS:
            return last_word

    return None

def extract_gsm_and_micron(text: str) -> tuple:

    t = text.lower()

    gsm_match = re.search(r"(\d+)\s*gsm", t)
    gsm = int(gsm_match.group(1)) if gsm_match else None

    micron_match = re.search(r"(\d+)\s*(?:mic|micron)", t)
    micron = int(micron_match.group(1)) if micron_match else None

    return gsm,micron

def parse_rfq(text: str) -> dict:

    category = extract_category(text)
    gsm, micron = extract_gsm_and_micron(text)
    quantity, unit = extract_quantity_and_unit(text)
    location = extract_location(text)

    return {
        "category": category,
        "quantity": quantity,
        "unit": unit,
        "gsm": gsm,
        "micron": micron,
        "location": location
    }