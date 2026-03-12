from app.extensions import db
from app.models import Hotel


SEED_HOTELS = [
    {"name": "Harbor Crown", "city": "Mumbai", "address": "Colaba Causeway", "price_min": 3500, "price_max": 6200, "rating": 4.5, "distance_km": 1.2, "map_link": "https://maps.google.com/?q=Harbor+Crown+Mumbai"},
    {"name": "Marine Bay Stay", "city": "Mumbai", "address": "Marine Drive", "price_min": 2600, "price_max": 4700, "rating": 4.1, "distance_km": 0.9, "map_link": "https://maps.google.com/?q=Marine+Bay+Stay+Mumbai"},
    {"name": "Delhi Grand Plaza", "city": "Delhi", "address": "Connaught Place", "price_min": 3200, "price_max": 5800, "rating": 4.3, "distance_km": 1.4, "map_link": "https://maps.google.com/?q=Delhi+Grand+Plaza"},
    {"name": "Capital Courtyard", "city": "Delhi", "address": "Karol Bagh", "price_min": 2100, "price_max": 3900, "rating": 4.0, "distance_km": 2.8, "map_link": "https://maps.google.com/?q=Capital+Courtyard+Delhi"},
    {"name": "Goa Palm Retreat", "city": "Goa", "address": "Calangute", "price_min": 4200, "price_max": 9000, "rating": 4.6, "distance_km": 1.1, "map_link": "https://maps.google.com/?q=Goa+Palm+Retreat"},
    {"name": "Sunset Sands", "city": "Goa", "address": "Baga Beach Road", "price_min": 2900, "price_max": 5400, "rating": 4.2, "distance_km": 0.6, "map_link": "https://maps.google.com/?q=Sunset+Sands+Goa"},
    {"name": "Pink City Haveli", "city": "Jaipur", "address": "MI Road", "price_min": 2400, "price_max": 5100, "rating": 4.2, "distance_km": 1.9, "map_link": "https://maps.google.com/?q=Pink+City+Haveli+Jaipur"},
    {"name": "Royal Amber Inn", "city": "Jaipur", "address": "Amer Fort Road", "price_min": 2800, "price_max": 6200, "rating": 4.4, "distance_km": 2.2, "map_link": "https://maps.google.com/?q=Royal+Amber+Inn+Jaipur"},
    {"name": "Himalaya Heights", "city": "Manali", "address": "Old Manali", "price_min": 3100, "price_max": 5600, "rating": 4.3, "distance_km": 1.7, "map_link": "https://maps.google.com/?q=Himalaya+Heights+Manali"},
    {"name": "Snowline Lodge", "city": "Manali", "address": "Mall Road", "price_min": 2200, "price_max": 4300, "rating": 4.0, "distance_km": 1.0, "map_link": "https://maps.google.com/?q=Snowline+Lodge+Manali"},
    {"name": "Hudson Arc", "city": "New York", "address": "Manhattan", "price_min": 14000, "price_max": 28000, "rating": 4.7, "distance_km": 1.5, "map_link": "https://maps.google.com/?q=Hudson+Arc+New+York"},
    {"name": "Central Park Suites", "city": "New York", "address": "Upper West Side", "price_min": 12000, "price_max": 24000, "rating": 4.4, "distance_km": 2.1, "map_link": "https://maps.google.com/?q=Central+Park+Suites"},
    {"name": "Seine View Hotel", "city": "Paris", "address": "7th Arrondissement", "price_min": 15000, "price_max": 31000, "rating": 4.8, "distance_km": 1.2, "map_link": "https://maps.google.com/?q=Seine+View+Hotel+Paris"},
    {"name": "Louvre Urban", "city": "Paris", "address": "Rue de Rivoli", "price_min": 12500, "price_max": 26000, "rating": 4.5, "distance_km": 0.9, "map_link": "https://maps.google.com/?q=Louvre+Urban+Paris"},
    {"name": "Shibuya Peak", "city": "Tokyo", "address": "Shibuya", "price_min": 13000, "price_max": 27500, "rating": 4.6, "distance_km": 1.4, "map_link": "https://maps.google.com/?q=Shibuya+Peak+Tokyo"},
    {"name": "Asakusa Zen Stay", "city": "Tokyo", "address": "Asakusa", "price_min": 9800, "price_max": 21000, "rating": 4.3, "distance_km": 1.8, "map_link": "https://maps.google.com/?q=Asakusa+Zen+Stay"},
    {"name": "Ubud Valley Resort", "city": "Bali", "address": "Ubud", "price_min": 10500, "price_max": 23000, "rating": 4.7, "distance_km": 2.0, "map_link": "https://maps.google.com/?q=Ubud+Valley+Resort"},
    {"name": "Kuta Breeze", "city": "Bali", "address": "Kuta", "price_min": 7800, "price_max": 16000, "rating": 4.2, "distance_km": 0.7, "map_link": "https://maps.google.com/?q=Kuta+Breeze+Bali"},
    {"name": "Marina Palm Hotel", "city": "Dubai", "address": "Dubai Marina", "price_min": 11800, "price_max": 25500, "rating": 4.6, "distance_km": 1.3, "map_link": "https://maps.google.com/?q=Marina+Palm+Hotel+Dubai"},
    {"name": "Creekside Modern", "city": "Dubai", "address": "Dubai Creek", "price_min": 9300, "price_max": 18000, "rating": 4.2, "distance_km": 2.4, "map_link": "https://maps.google.com/?q=Creekside+Modern+Dubai"},
]


def seed_hotels():
    if Hotel.query.count() > 0:
        return

    for row in SEED_HOTELS:
        db.session.add(Hotel(**row))

    db.session.commit()
