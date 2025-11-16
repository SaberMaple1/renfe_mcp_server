"""
Quick test script for price checking functionality.
"""

from price_checker import check_prices, format_price_results
from datetime import datetime, timedelta

def test_price_checker():
    """Test the price checker with a simple query."""
    print("Testing price checker integration...")
    print("=" * 60)

    # Test with Madrid to Barcelona
    origin = "Madrid"
    destination = "Barcelona"

    # Use tomorrow's date to ensure trains are available
    tomorrow = (datetime.now() + timedelta(days=1)).strftime("%Y-%m-%d")

    print(f"\nChecking prices from {origin} to {destination} on {tomorrow}")
    print("This may take a few seconds as it scrapes the Renfe website...")
    print("-" * 60)

    try:
        results = check_prices(origin, destination, tomorrow, max_trains=3)

        if results:
            print("\n[SUCCESS] Price checking is working!")
            print("\nResults:")
            # Format without emojis for Windows console
            for i, train in enumerate(results, 1):
                hours = train["duration_minutes"] // 60
                mins = train["duration_minutes"] % 60
                duration_str = f"{hours}h {mins}min"
                availability = "[AVAILABLE]" if train["available"] else "[SOLD OUT]"
                price_str = f"{train['price']:.2f} EUR" if train["available"] else "N/A"

                print(f"\n  {i}. {train['train_type']}")
                print(f"     Departs: {train['departure_time']} | Arrives: {train['arrival_time']}")
                print(f"     Duration: {duration_str}")
                print(f"     Price: {price_str} | {availability}")
        else:
            print("\n[WARNING] No results returned, but no errors occurred.")

    except Exception as e:
        print(f"\n[ERROR] Error occurred: {type(e).__name__}: {str(e)}")
        print("\nThis might be expected if:")
        print("  - The Renfe website is down")
        print("  - There are no trains for this route on this date")
        print("  - Network issues")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_price_checker()
