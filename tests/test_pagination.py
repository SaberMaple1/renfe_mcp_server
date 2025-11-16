"""
Test script for pagination functionality.
"""

from main import load_gtfs_data, search_trains_with_context
from datetime import datetime, timedelta

def test_pagination():
    """Test the pagination feature with Madrid to Barcelona."""
    print("Testing pagination functionality...")
    print("=" * 60)

    # Load GTFS data
    load_gtfs_data()

    origin = "Madrid"
    destination = "Barcelona"

    # Use tomorrow's date
    tomorrow = (datetime.now() + timedelta(days=1)).strftime("%Y-%m-%d")

    print(f"\nSearching trains from {origin} to {destination} on {tomorrow}")
    print("-" * 60)

    # Test Page 1 (first 10 trains)
    print("\n[TEST 1] Page 1, 10 trains per page:")
    print("-" * 60)
    result = search_trains_with_context(origin, destination, tomorrow, page=1, per_page=10)
    print(result)

    # Test Page 2
    print("\n[TEST 2] Page 2, 10 trains per page:")
    print("-" * 60)
    result = search_trains_with_context(origin, destination, tomorrow, page=2, per_page=10)
    print(result)

    # Test with larger page size
    print("\n[TEST 3] Page 1, 5 trains per page:")
    print("-" * 60)
    result = search_trains_with_context(origin, destination, tomorrow, page=1, per_page=5)
    print(result)

    print("\n[SUCCESS] Pagination testing completed!")

if __name__ == "__main__":
    test_pagination()
