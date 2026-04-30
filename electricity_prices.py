# electricity_prices.py
#
# Average retail electricity prices by country
# Source: WorldPopulationReview / GlobalPetrolPrices
# Prices are suitable for comparative analysis only
#
# Base currency: USD per kWh
# Converted currency: GBP per kWh (static FX)

USD_TO_GBP = 0.79  # Static conversion, update manually if needed

ELECTRICITY_PRICE_USD_PER_KWH =  {
    "Bermuda": 0.47,
    "Ireland": 0.44,
    "Italy": 0.42,
    "Cayman Islands": 0.41,
    "Liechtenstein": 0.41,
    "Germany": 0.40,
    "Belgium": 0.40,
    "United Kingdom": 0.40,
    "Switzerland": 0.36,
    "Denmark": 0.36,
    "Czechia": 0.35,
    "Bahamas": 0.35,
    "Austria": 0.34,
    "Cyprus": 0.34,
    "Cape Verde": 0.33,
    "Barbados": 0.31,
    "Guatemala": 0.29,
    "Netherlands": 0.29,
    "Estonia": 0.29,
    "Jamaica": 0.28,
    "Latvia": 0.28,
    "France": 0.28,
    "Lithuania": 0.27,
    "Australia": 0.26,
    "Luxembourg": 0.25,
    "Uruguay": 0.25,
    "El Salvador": 0.25,
    "Greece": 0.25,
    "Spain": 0.25,
    "Honduras": 0.24,
    "Portugal": 0.23,
    "Singapore": 0.23,
    "Sweden": 0.23,
    "Poland": 0.23,
    "Japan": 0.23,
    "Slovenia": 0.23,
    "Kenya": 0.22,
    "Mali": 0.22,
    "Belize": 0.22,
    "Chile": 0.21,
    "Aruba": 0.21,
    "Slovakia": 0.21,
    "New Zealand": 0.21,
    "Gabon": 0.20,
    "Philippines": 0.20,
    "Colombia": 0.20,
    "Rwanda": 0.20,
    "South Africa": 0.19,
    "Peru": 0.19,
    "Romania": 0.19,
    "Hong Kong": 0.19,
    "United States": 0.18,
    "Finland": 0.18,
    "Israel": 0.18,
    "Panama": 0.17,
    "Iceland": 0.17,
    "Uganda": 0.17,
    "Croatia": 0.17,
    "Moldova": 0.17,
    "Costa Rica": 0.17,
    "Brazil": 0.16,
    "Norway": 0.15,
    "Bulgaria": 0.15,
    "Malta": 0.15,
    "Namibia": 0.14,
    "Mauritius": 0.13,
    "Ghana": 0.13,
    "Madagascar": 0.13,
    "Thailand": 0.13,
    "Serbia": 0.13,
    "South Korea": 0.13,
    "Canada": 0.12,
    "Sri Lanka": 0.12,
    "Morocco": 0.12,
    "Albania": 0.12,
    "Dominican Republic": 0.12,
    "Armenia": 0.11,
    "Hungary": 0.11,
    "Mexico": 0.11,
    "Bosnia and Herzegovina": 0.10,
    "Taiwan": 0.10,
    "Ecuador": 0.10,
    "Indonesia": 0.09,
    "Tanzania": 0.09,
    "Jordan": 0.09,
    "Cameroon": 0.08,
    "Ukraine": 0.08,
    "United Arab Emirates": 0.08,
    "Vietnam": 0.08,
    "India": 0.08,
    "China": 0.08,
    "Argentina": 0.08,
    "Turkey": 0.07,
    "Georgia": 0.07,
    "Pakistan": 0.07,
    "Russia": 0.07,
    "Bangladesh": 0.06,
    "Kazakhstan": 0.06,
    "Saudi Arabia": 0.05,
    "Malaysia": 0.05,
    "Azerbaijan": 0.05,
    "Nepal": 0.04,
    "Algeria": 0.04,
    "Kuwait": 0.04,
    "Nigeria": 0.04,
    "Qatar": 0.03,
    "Oman": 0.03,
    "Egypt": 0.02,
}


DEFAULT_ELECTRICITY_PRICE_USD = 0.20  # global-average fallback


def get_electricity_price_gbp(country: str) -> dict:
    """
    Return electricity price for a country in GBP per kWh.

    Returns a dict including metadata for transparency.
    """
    usd = ELECTRICITY_PRICE_USD_PER_KWH.get(
        country, DEFAULT_ELECTRICITY_PRICE_USD
    )
    gbp = round(usd * USD_TO_GBP, 3)

    return {
        "price_gbp_per_kwh": gbp,
        "price_usd_per_kwh": usd,
        "currency": "GBP",
        "fx_rate_usd_to_gbp": USD_TO_GBP,
        "source": "WorldPopulationReview / GlobalPetrolPrices",
        "fallback_used": country not in ELECTRICITY_PRICE_USD_PER_KWH,
    }
