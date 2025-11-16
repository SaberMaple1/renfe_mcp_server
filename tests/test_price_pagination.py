"""
Test script for price checking pagination functionality.
"""

from price_checker import check_prices
from datetime import datetime, timedelta

def test_price_pagination():
    """Test price pagination with Madrid to Barcelona."""
    print("Testing price pagination functionality...")
    print("=" * 60)

    origin = "Madrid"
    destination = "Barcelona"

    # Use tomorrow's date
    tomorrow = (datetime.now() + timedelta(days=1)).strftime("%Y-%m-%d")

    print(f"\nChecking prices from {origin} to {destination} on {tomorrow}")
    print("This may take a few seconds as it scrapes the Renfe website...")
    print("-" * 60)

    try:
        # Test Page 1
        print("\n[TEST 1] Page 1, 5 trains per page:")
        print("-" * 60)
        results_page1 = check_prices(origin, destination, tomorrow, page=1, per_page=5)

        if results_page1:
            print(f"[SUCCESS] Got {len(results_page1)} trains on page 1")
            for i, train in enumerate(results_page1, 1):
                availability = "[AVAILABLE]" if train["available"] else "[SOLD OUT]"
                price_str = f"{train['price']:.2f} EUR" if train["available"] else "N/A"
                print(f"  {i}. {train['train_type']} - {train['departure_time']} - {price_str} {availability}")
        else:
            print("[WARNING] No results on page 1")

        # Test Page 2
        print("\n[TEST 2] Page 2, 5 trains per page:")
        print("-" * 60)
        results_page2 = check_prices(origin, destination, tomorrow, page=2, per_page=5)

        if results_page2:
            print(f"[SUCCESS] Got {len(results_page2)} trains on page 2")
            for i, train in enumerate(results_page2, 1):
                availability = "[AVAILABLE]" if train["available"] else "[SOLD OUT]"
                price_str = f"{train['price']:.2f} EUR" if train["available"] else "N/A"
                print(f"  {i}. {train['train_type']} - {train['departure_time']} - {price_str} {availability}")
        else:
            print("[WARNING] No results on page 2")

        # Verify trains are different between pages
        if results_page1 and results_page2:
            page1_times = [t['departure_time'] for t in results_page1]
            page2_times = [t['departure_time'] for t in results_page2]

            if set(page1_times) & set(page2_times):
                print("\n[ERROR] Some trains appear on both pages!")
            else:
                print("\n[SUCCESS] Pagination working correctly - different trains on each page!")

        print("\n[SUCCESS] Price pagination testing completed!")

    except Exception as e:
        print(f"\n[ERROR] Error occurred: {type(e).__name__}: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_price_pagination()
