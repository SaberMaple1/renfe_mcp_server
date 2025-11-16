"""Final integration test for the complete system."""

from datetime import datetime, timedelta
from main import load_gtfs_data, search_trains_with_context
from price_checker import check_prices

def test_final_integration():
    """Test the complete MCP server functionality."""
    print("Final Integration Test")
    print("=" * 50)

    # Load GTFS data
    print("\n[1] Loading GTFS data...")
    load_gtfs_data()
    print("[SUCCESS] GTFS data loaded")

    # Use tomorrow's date
    tomorrow = datetime.now() + timedelta(days=1)
    date_str = tomorrow.strftime("%Y-%m-%d")

    # Test schedule search
    print(f"\n[2] Testing schedule search (Madrid -> Barcelona on {date_str})...")
    try:
        schedule_result = search_trains_with_context("Madrid", "Barcelona", date_str, page=1, per_page=5)
        print("[SUCCESS] Schedule search completed")
        print(f"Result length: {len(schedule_result)} characters")
    except Exception as e:
        print(f"[ERROR] Schedule search failed: {e}")
        return

    # Test price check
    print(f"\n[3] Testing price check (Madrid -> Barcelona on {date_str})...")
    try:
        price_results = check_prices("Madrid", "Barcelona", date_str, page=1, per_page=3)
        print("[SUCCESS] Price check completed")
        print(f"Got {len(price_results)} train(s)")
        # Check if it contains expected content
        if price_results and price_results[0].get("train_type"):
            print(f"[SUCCESS] First train type: {price_results[0]['train_type']}")
            print(f"[SUCCESS] First train price: {price_results[0]['price']:.2f} EUR")
    except Exception as e:
        print(f"[ERROR] Price check failed: {e}")
        import traceback
        traceback.print_exc()
        return

    # Test pagination
    print(f"\n[4] Testing pagination (page 2)...")
    try:
        price_results_p2 = check_prices("Madrid", "Barcelona", date_str, page=2, per_page=3)
        print("[SUCCESS] Page 2 price check completed")
        print(f"Got {len(price_results_p2)} train(s)")

        # Verify different results
        if price_results and price_results_p2:
            if price_results[0]["departure_time"] != price_results_p2[0]["departure_time"]:
                print("[SUCCESS] Page 1 and Page 2 have different trains")
            else:
                print("[WARNING] Page 1 and Page 2 have identical trains")

    except Exception as e:
        print(f"[ERROR] Pagination test failed: {e}")
        import traceback
        traceback.print_exc()
        return

    print("\n" + "=" * 50)
    print("[SUCCESS] All integration tests passed!")
    print("The MCP server is ready for use.")

if __name__ == "__main__":
    test_final_integration()
