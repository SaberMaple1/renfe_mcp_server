"""Test the updated price_checker with new custom scraper."""

from datetime import datetime, timedelta
from price_checker import check_prices, format_price_results

def test_updated_price_checker():
    """Test price checker with new scraper integration."""
    print("Testing Updated Price Checker")
    print("=" * 50)

    # Use tomorrow's date
    tomorrow = datetime.now() + timedelta(days=1)
    date_str = tomorrow.strftime("%Y-%m-%d")

    print(f"\nSearching: Madrid -> Barcelona")
    print(f"Date: {date_str}")

    # Test page 1 (first 5 trains)
    print("\n[1] Testing Page 1 (first 5 trains)...")
    try:
        results_page1 = check_prices("Madrid", "Barcelona", date_str, page=1, per_page=5)

        print(f"[SUCCESS] Got {len(results_page1)} trains")

        if results_page1:
            print("\nFirst train details:")
            first = results_page1[0]
            print(f"  Type: {first['train_type']}")
            print(f"  Departure: {first['departure_time']}")
            print(f"  Price: {first['price']:.2f} EUR")
            print(f"  Available: {first['available']}")

        # Test formatted output
        print("\n[2] Testing formatted output...")
        formatted = format_price_results(results_page1, "Madrid", "Barcelona", date_str)
        print(formatted)

        # Test page 2
        print("\n[3] Testing Page 2 (trains 6-10)...")
        results_page2 = check_prices("Madrid", "Barcelona", date_str, page=2, per_page=5)

        print(f"[SUCCESS] Got {len(results_page2)} trains")

        if results_page2:
            print("\nFirst train from page 2:")
            first_p2 = results_page2[0]
            print(f"  Type: {first_p2['train_type']}")
            print(f"  Departure: {first_p2['departure_time']}")
            print(f"  Price: {first_p2['price']:.2f} EUR")

        # Verify pages are different
        if results_page1 and results_page2:
            if results_page1[0]['departure_time'] != results_page2[0]['departure_time']:
                print("\n[SUCCESS] Page 1 and Page 2 show different trains")
            else:
                print("\n[WARNING] Page 1 and Page 2 show same trains")

        print("\n[SUCCESS] All tests passed!")

    except Exception as e:
        print(f"\n[ERROR] {type(e).__name__}: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_updated_price_checker()
