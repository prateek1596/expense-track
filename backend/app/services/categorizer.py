RULES = {
    "Food & Dining": [
        "zomato", "swiggy", "ubereats", "restaurant", "cafe", "food", "pizza", "burger",
        "mcdonalds", "dominos", "kfc", "bakery", "diner", "bistro", "pub", "bar",
        "lounge", "buffet", "fast food", "takeaway", "delivery"
    ],
    "Transport": [
        "ola", "uber", "metro", "fuel", "petrol", "diesel", "cng", "parking",
        "toll", "taxi", "bus", "railway", "flight", "airline", "gas station",
        "car rental", "bike rental", "autorickshaw"
    ],
    "Shopping": [
        "amazon", "flipkart", "myntra", "shopping", "mall", "store", "shop",
        "apparel", "clothing", "shoes", "boots", "dress", "fashion",
        "retail", "department store", "supermarket", "grocery", "walmart", "target"
    ],
    "Utilities": [
        "electricity", "water", "gas", "internet", "broadband", "telecom", "mobile",
        "phone bill", "landline", "dth", "cable", "wifi", "electricity board"
    ],
    "Health & Fitness": [
        "pharmacy", "hospital", "clinic", "medicine", "doctor", "dental", "dentist",
        "gym", "fitness", "yoga", "trainer", "healthcare", "health", "medical",
        "lab", "diagnostic", "beauty", "salon", "spa", "wellness"
    ],
    "Entertainment": [
        "netflix", "spotify", "movie", "bookmyshow", "youtube", "prime video", "hulu",
        "cinema", "theatre", "concert", "event", "ticketing", "gaming", "game",
        "streaming", "music", "podcast", "ott", "sports"
    ],
    "Education": [
        "school", "college", "university", "tuition", "course", "coaching",
        "education", "academy", "training", "workshop", "seminar", "books",
        "stationery", "library", "fees", "exam"
    ],
    "Transfer & Payment": [
        "upi", "gpay", "phonepe", "paytm", "imps", "neft", "rtgs", "transfer",
        "fund", "wallet", "bank", "settlement", "remittance", "wire"
    ],
    "Insurance": [
        "insurance", "premium", "policy", "claim", "coverage", "health insurance",
        "car insurance", "life insurance", "term plan"
    ],
    "Rent & Housing": [
        "rent", "landlord", "housing", "lease", "maintenance", "repair",
        "construction", "property", "real estate", "home loan"
    ],
    "Other": []
}


def categorize_transaction(merchant: str, description: str) -> str:
    """
    Categorize a transaction based on merchant name and description.
    
    Args:
        merchant: The merchant/vendor name
        description: Transaction description
    
    Returns:
        The category name for the transaction, defaults to "Other"
    """
    text = f"{merchant} {description}".lower().strip()
    
    # Check each category in order (order matters for overlapping keywords)
    for category, keywords in RULES.items():
        if keywords and any(keyword in text for keyword in keywords):
            return category
    
    return "Other"
