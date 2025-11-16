"""Test the new custom RenfeScraper with live API."""

from datetime import datetime, timedelta
from renfe_scraper import RenfeScraper, find_station

def test_custom_scraper():
    """Test the custom scraper implementation."""
    print("Testing Custom RenfeScraper")
    print("=" * 50)

    # Find stations
    print("\n[1] Finding stations...")
    madrid = find_station("Madrid")
    barcelona = find_station("Barcelona")

    if not madrid or not barcelona:
        print("[ERROR] Could not find stations")
        return

    print(f"Origin: {madrid.name} ({madrid.code})")
    print(f"Destination: {barcelona.name} ({barcelona.code})")

    # Use tomorrow's date
    tomorrow = datetime.now() + timedelta(days=1)
    print(f"\nDate: {tomorrow.strftime('%Y-%m-%d')}")

    # Create scraper and get trains
    print("\n[2] Creating scraper and fetching trains...")
    try:
        scraper = RenfeScraper(
            origin=madrid,
            destination=barcelona,
            departure_date=tomorrow
        )

        trains = scraper.get_trains()

        print(f"\n[SUCCESS] Found {len(trains)} trains")
        print("\n[3] First 5 trains:")
        print("-" * 80)

        for i, train in enumerate(trains[:5], 1):
            status = "[AVAILABLE]" if train.available else "[SOLD OUT]"
            print(f"\n{i}. {train.train_type} {status}")
            print(f"   {train.origin} -> {train.destination}")
            print(f"   Departure: {train.departure_time.strftime('%H:%M')}")
            print(f"   Arrival: {train.arrival_time.strftime('%H:%M')}")
            print(f"   Duration: {train.duration_minutes} minutes")
            print(f"   Price: {train.price:.2f} EUR")

        # Test to_dict() conversion
        print("\n[4] Testing to_dict() conversion:")
        if trains:
            dict_result = trains[0].to_dict()
            print(f"   Type: {dict_result['train_type']}")
            print(f"   Departure: {dict_result['departure_time']}")
            print(f"   Price: {dict_result['price']}")

        print("\n[SUCCESS] Custom scraper test completed!")

    except Exception as e:
        print(f"\n[ERROR] {type(e).__name__}: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_custom_scraper()
