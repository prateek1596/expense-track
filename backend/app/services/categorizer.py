RULES = {
    "Food": ["zomato", "swiggy", "restaurant", "cafe", "food"],
    "Transport": ["ola", "uber", "metro", "fuel", "petrol", "diesel"],
    "Shopping": ["amazon", "flipkart", "myntra", "shopping"],
    "Utilities": ["electricity", "water", "gas", "internet", "broadband"],
    "Health": ["pharmacy", "hospital", "clinic", "medicine"],
    "Entertainment": ["netflix", "spotify", "movie", "bookmyshow"],
    "UPI Transfer": ["upi", "gpay", "phonepe", "paytm", "imps", "neft"],
}


def categorize_transaction(merchant: str, description: str) -> str:
    text = f"{merchant} {description}".lower()
    for category, keywords in RULES.items():
        if any(keyword in text for keyword in keywords):
            return category
    return "Other"
