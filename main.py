from datetime import datetime
from pathlib import Path
from typing import Any

import pandas as pd
from fastmcp import FastMCP
from dateutil import parser as date_parser

from price_checker import check_prices, format_price_results
from station_service import get_station_service

# ============================================================================
# 1. Configuration & Setup
# ============================================================================

# Create the MCP server
mcp = FastMCP("Renfe Train Search")

# Global variables for GTFS data
stops_df = None
routes_df = None
trips_df = None
stop_times_df = None
calendar_df = None
calendar_dates_df = None


# ============================================================================
# 2. Data Loading
# ============================================================================


def load_gtfs_data():
    """Load all GTFS CSV files into pandas DataFrames."""
    global stops_df, routes_df, trips_df, stop_times_df, calendar_df, calendar_dates_df

    data_dir = Path("renfe_schedule")

    print("Loading GTFS data...")

    # Load CSV files and strip whitespace from column names
    stops_df = pd.read_csv(data_dir / "stops.txt")
    stops_df.columns = stops_df.columns.str.strip()

    routes_df = pd.read_csv(data_dir / "routes.txt")
    routes_df.columns = routes_df.columns.str.strip()

    trips_df = pd.read_csv(data_dir / "trips.txt")
    trips_df.columns = trips_df.columns.str.strip()

    stop_times_df = pd.read_csv(data_dir / "stop_times.txt")
    stop_times_df.columns = stop_times_df.columns.str.strip()

    calendar_df = pd.read_csv(data_dir / "calendar.txt")
    calendar_df.columns = calendar_df.columns.str.strip()

    calendar_dates_df = pd.read_csv(data_dir / "calendar_dates.txt")
    calendar_dates_df.columns = calendar_dates_df.columns.str.strip()

    print("GTFS data loaded successfully!")

    # Initialize station service with GTFS data
    station_service = get_station_service(stops_df)
    coverage = station_service.validate_coverage()
    if coverage['warnings']:
        for warning in coverage['warnings']:
            print(f"⚠️  {warning}")


# ============================================================================
# 3. Core Helper Functions
# ============================================================================


def get_formatted_date(date_str=None):
    """
    Flexible date parser that handles multiple formats.
    Returns date in YYYY-MM-DD format.
    """
    if not date_str:
        dt_obj = datetime.now()
    else:
        try:
            # European date parsing (day-first)
            if "/" in date_str:
                parts = date_str.split()[0].split("/")
                if len(parts) >= 2 and parts[0].isdigit():
                    first_num = int(parts[0])
                    if first_num > 12:
                        # Must be day-first (e.g., 28/11/2025)
                        dt_obj = date_parser.parse(date_str, dayfirst=True)
                    else:
                        # Use European default for Renfe
                        dt_obj = date_parser.parse(date_str, dayfirst=True)
                else:
                    dt_obj = date_parser.parse(date_str, dayfirst=True)
            else:
                # For ISO and other formats
                dt_obj = date_parser.parse(date_str)

        except (ValueError, date_parser.ParserError) as e:
            raise ValueError(
                f"❌ Could not parse date '{date_str}'. "
                f"Supported formats:\n"
                f"  - ISO: '2025-11-28'\n"
                f"  - European: '28/11/2025'\n"
                f"  - Written: 'November 28, 2025' or '28 November 2025'\n"
                f"Error: {str(e)}"
            )

    return dt_obj.strftime("%Y-%m-%d")


def get_stops_for_city(city_name: str) -> dict[str, Any]:
    """
    Map a city name to all station IDs for that city.
    Returns a dict with: success, stop_ids, stations, context

    Now uses the unified StationService for consistent station lookups.
    """
    # Use unified station service
    station_service = get_station_service()
    unified_stations = station_service.find_stations(city_name)

    # Filter to only stations with GTFS data (needed for schedule search)
    gtfs_stations = [s for s in unified_stations if s.has_gtfs_data()]

    if not gtfs_stations:
        return {
            "success": False,
            "stop_ids": [],
            "stations": [],
            "context": f"❌ No stations found for '{city_name}'. Please check the spelling or try a different city name.",
        }

    stop_ids = [s.gtfs_id for s in gtfs_stations]
    stations = [s.name for s in gtfs_stations]

    # Build context narrative
    context = f"🔍 Searched for '{city_name}':\n"
    for i, (sid, name) in enumerate(zip(stop_ids[:3], stations[:3])):
        marker = "✓" if i == 0 else " "
        context += f"  {marker} {name} (ID: {sid})\n"

    if len(stations) == 1:
        context += f"\n→ Found 1 station"
    else:
        context += f"\n→ Found {len(stations)} stations"

    return {
        "success": True,
        "stop_ids": stop_ids,
        "stations": stations,
        "context": context,
    }


def get_day_of_week(date_str: str) -> str:
    """Convert date string to day of week name for GTFS calendar lookup."""
    date_obj = datetime.strptime(date_str, "%Y-%m-%d")
    day_name = date_obj.strftime("%A").lower()
    return day_name


def get_active_service_ids(date_str: str) -> set[str]:
    """
    Determine which service IDs are active on a specific date.
    Combines calendar.txt and calendar_dates.txt logic.
    """
    # Convert date to GTFS format (YYYYMMDD)
    gtfs_date = int(date_str.replace("-", ""))
    day_of_week = get_day_of_week(date_str)

    active_services = set()

    # Check calendar.txt for services running on this date
    for _, service in calendar_df.iterrows():
        service_id = service["service_id"]
        start_date = int(service["start_date"])
        end_date = int(service["end_date"])

        # Check if date is in range
        if start_date <= gtfs_date <= end_date:
            # Check if this day of week is active
            if service[day_of_week] == 1:
                active_services.add(service_id)

    # Apply exceptions from calendar_dates.txt
    exceptions = calendar_dates_df[calendar_dates_df["date"] == gtfs_date]
    for _, exception in exceptions.iterrows():
        service_id = exception["service_id"]
        exception_type = exception["exception_type"]

        if exception_type == 1:
            # Service added on this date
            active_services.add(service_id)
        elif exception_type == 2:
            # Service removed on this date
            active_services.discard(service_id)

    return active_services


def search_trains_with_context(origin_city: str, destination_city: str, date_str: str, page: int = 1, per_page: int = 10):
    """
    Find all trains traveling from origin city to destination city on a specific date.
    Returns a formatted string with paginated results.

    Args:
        origin_city: Origin city name
        destination_city: Destination city name
        date_str: Date in YYYY-MM-DD format
        page: Page number (1-indexed)
        per_page: Results per page
    """
    # Get station IDs for both cities
    origin_result = get_stops_for_city(origin_city)
    if not origin_result["success"]:
        return origin_result["context"]

    dest_result = get_stops_for_city(destination_city)
    if not dest_result["success"]:
        return dest_result["context"]

    origin_stops = origin_result["stop_ids"]
    dest_stops = dest_result["stop_ids"]

    # Get active service IDs for this date
    active_services = get_active_service_ids(date_str)

    if not active_services:
        return f"❌ No train services running on {date_str}. This might be a special holiday or outside the schedule date range."

    # Filter trips that run on this date
    active_trips = trips_df[trips_df["service_id"].isin(active_services)]

    results = []

    # For each active trip, check if it goes from origin to destination
    for _, trip in active_trips.iterrows():
        trip_id = trip["trip_id"]
        route_id = trip["route_id"]

        # Get all stops for this trip
        trip_stops = stop_times_df[stop_times_df["trip_id"] == trip_id].sort_values(
            "stop_sequence"
        )

        # Find origin and destination stops
        origin_stop = None
        dest_stop = None

        for _, stop in trip_stops.iterrows():
            # Check if this is an origin stop
            if stop["stop_id"] in origin_stops and origin_stop is None:
                # Make sure passengers can board (pickup_type == 0)
                if stop["pickup_type"] == 0:
                    origin_stop = stop

            # Check if this is a destination stop (must come after origin)
            if stop["stop_id"] in dest_stops and origin_stop is not None:
                # Make sure passengers can alight (drop_off_type == 0)
                if stop["drop_off_type"] == 0:
                    dest_stop = stop
                    break

        # If we found both origin and destination, add to results
        if origin_stop is not None and dest_stop is not None:
            # Get route information
            route = routes_df[routes_df["route_id"] == route_id].iloc[0]

            # Get stop names
            origin_name = stops_df[stops_df["stop_id"] == origin_stop["stop_id"]].iloc[
                0
            ]["stop_name"]
            dest_name = stops_df[stops_df["stop_id"] == dest_stop["stop_id"]].iloc[0][
                "stop_name"
            ]

            # Calculate duration
            def time_to_minutes(time_str):
                parts = time_str.split(":")
                return int(parts[0]) * 60 + int(parts[1])

            dep_minutes = time_to_minutes(origin_stop["departure_time"])
            arr_minutes = time_to_minutes(dest_stop["arrival_time"])
            duration_minutes = arr_minutes - dep_minutes
            duration_hours = duration_minutes // 60
            duration_mins = duration_minutes % 60

            results.append(
                {
                    "train_type": route["route_short_name"],
                    "origin_station": origin_name,
                    "departure_time": origin_stop["departure_time"],
                    "destination_station": dest_name,
                    "arrival_time": dest_stop["arrival_time"],
                    "duration_hours": duration_hours,
                    "duration_mins": duration_mins,
                    "trip_id": trip_id,
                }
            )

    # Sort by departure time (convert to minutes for proper numeric sorting)
    def time_to_minutes_for_sort(time_str):
        parts = time_str.split(":")
        return int(parts[0]) * 60 + int(parts[1])

    results.sort(key=lambda x: time_to_minutes_for_sort(x["departure_time"]))

    if not results:
        return f"❌ No direct trains found from {origin_city} to {destination_city} on {date_str}. Try a different date or check for connecting routes."

    # Calculate pagination
    total_results = len(results)
    total_pages = (total_results + per_page - 1) // per_page  # Ceiling division

    # Ensure page is within valid range
    if page > total_pages:
        page = total_pages
    if page < 1:
        page = 1

    # Calculate slice indices
    start_idx = (page - 1) * per_page
    end_idx = min(start_idx + per_page, total_results)

    # Get the current page of results
    page_results = results[start_idx:end_idx]

    # Format results with pagination info
    result_text = f"Found {total_results} train(s) total\n"
    result_text += f"Showing page {page} of {total_pages} ({len(page_results)} trains)\n\n"

    for i, train in enumerate(page_results, start=start_idx + 1):
        result_text += f"  {i}. {train['train_type']}\n"
        result_text += f"     {train['origin_station']} → {train['destination_station']}\n"
        result_text += f"     Departs: {train['departure_time']} | Arrives: {train['arrival_time']}\n"
        result_text += f"     Duration: {train['duration_hours']}h {train['duration_mins']}min\n\n"

    # Add pagination navigation hints
    if total_pages > 1:
        result_text += "─────────────────────────────────\n"
        if page < total_pages:
            result_text += f"💡 To see more trains, use page={page + 1}\n"
        if page > 1:
            result_text += f"💡 To see previous trains, use page={page - 1}\n"
        result_text += f"💡 Total pages: {total_pages}\n"

    return result_text


# ============================================================================
# 4. MCP Tools (The "Buttons" Claude Can Press)
# ============================================================================


@mcp.tool()
def search_trains(origin: str, destination: str, date: str = None, page: int = 1, per_page: int = 10) -> str:
    """
    Search for train journeys between two cities on a specific date.

    Args:
        origin: Starting city name (e.g., "Madrid", "Barcelona", "Valencia")
        destination: Destination city name (e.g., "Madrid", "Barcelona", "Sevilla")
        date: Travel date. Accepts flexible formats:
              - ISO: "2025-11-28" (RECOMMENDED)
              - European: "28/11/2025"
              - Written: "November 28, 2025" or "28 November 2025"
              If not provided, searches for today's date.
        page: Page number to display (default: 1)
        per_page: Number of results per page (default: 10, max: 50)

    Returns:
        Formatted string with available train options including times and durations.
    """

    # Build up a story for Claude
    story = "═══════════════════════════════════\n"
    story += "    RENFE TRAIN SEARCH\n"
    story += "═══════════════════════════════════\n\n"

    # Format the date
    try:
        formatted_date = get_formatted_date(date)
    except ValueError as e:
        story += str(e)
        story += "\n═══════════════════════════════════\n"
        return story

    if date:
        story += f"📅 Searching for trains on: {formatted_date}\n\n"
    else:
        story += f"📅 Searching for trains on: {formatted_date} (today)\n\n"

    # Validate pagination parameters
    page = max(1, page)  # Ensure page is at least 1
    per_page = min(max(1, per_page), 50)  # Ensure per_page is between 1 and 50

    # Search for trains
    story += "─────────────────────────────────\n"
    story += "🚄 AVAILABLE TRAINS\n"
    story += "─────────────────────────────────\n\n"

    train_results = search_trains_with_context(origin, destination, formatted_date, page, per_page)
    story += train_results

    story += "\n═══════════════════════════════════\n"

    return story


@mcp.tool()
def find_station(city_name: str) -> str:
    """
    Search for train stations in a city and return matching options.

    Useful for checking what stations are available in a city before
    searching for journeys.

    Args:
        city_name: City name to search for (e.g., "Madrid", "Barcelona", "Valencia")

    Returns:
        A formatted string showing all matching stations with their IDs and full names.
    """

    result = get_stops_for_city(city_name)

    story = "═══════════════════════════════════\n"
    story += "    STATION SEARCH\n"
    story += "═══════════════════════════════════\n\n"

    story += result["context"] + "\n"

    if result["success"]:
        story += "\n📍 All stations found:\n"
        for i, (sid, name) in enumerate(
            zip(result["stop_ids"], result["stations"]), 1
        ):
            story += f"  {i}. {name}\n"
            story += f"     ID: {sid}\n"

    story += "\n═══════════════════════════════════\n"

    return story


@mcp.tool()
def get_train_prices(origin: str, destination: str, date: str = None, page: int = 1, per_page: int = 5) -> str:
    """
    Check actual ticket prices for trains between two cities using web scraping with pagination.

    NOTE: This tool scrapes the Renfe website and may take a few seconds to complete.
    It complements the search_trains tool by providing real-time price information.

    Args:
        origin: Starting city name (e.g., "Madrid", "Barcelona", "Valencia")
        destination: Destination city name (e.g., "Madrid", "Barcelona", "Sevilla")
        date: Travel date. Accepts flexible formats:
              - ISO: "2025-11-28" (RECOMMENDED)
              - European: "28/11/2025"
              - Written: "November 28, 2025" or "28 November 2025"
              If not provided, checks prices for today's date.
        page: Page number to display (default: 1)
        per_page: Number of results per page (default: 5, max: 20)

    Returns:
        Formatted string with train prices, availability, and booking information.
    """
    story = "═══════════════════════════════════\n"
    story += "    RENFE PRICE CHECK\n"
    story += "═══════════════════════════════════\n\n"

    # Format the date
    try:
        formatted_date = get_formatted_date(date)
    except ValueError as e:
        story += str(e)
        story += "\n═══════════════════════════════════\n"
        return story

    if date:
        story += f"Checking prices for: {formatted_date}\n"
    else:
        story += f"Checking prices for: {formatted_date} (today)\n"

    story += f"Scraping Renfe website for live prices...\n\n"

    # Validate pagination parameters
    page = max(1, page)  # Ensure page is at least 1
    per_page = min(max(1, per_page), 20)  # Ensure per_page is between 1 and 20

    try:
        # Call the price checker with pagination
        results = check_prices(origin, destination, formatted_date, page=page, per_page=per_page)

        # Format results
        story += "─────────────────────────────────\n"
        story += "PRICE RESULTS\n"
        story += "─────────────────────────────────\n\n"

        if results:
            story += f"Showing page {page} ({len(results)} trains)\n\n"

            for i, train in enumerate(results, 1):
                hours = train["duration_minutes"] // 60
                mins = train["duration_minutes"] % 60
                duration_str = f"{hours}h {mins}min"

                availability = "[Available]" if train["available"] else "[Sold out]"
                price_str = f"{train['price']:.2f}€" if train["available"] else "N/A"

                story += f"  {i}. {train['train_type']}\n"
                story += f"     Departs: {train['departure_time']} | Arrives: {train['arrival_time']}\n"
                story += f"     Duration: {duration_str}\n"
                story += f"     Price: {price_str} | {availability}\n\n"

            story += "─────────────────────────────────\n"
            story += f"💡 To see more prices, try page={page + 1}\n"
        else:
            story += "No trains available for this page.\n"

        story += "\n💡 TIP: Use search_trains to see the complete schedule without prices.\n"

    except ValueError as e:
        story += f"❌ Error: {str(e)}\n"
    except Exception as e:
        story += f"❌ Failed to check prices: {str(e)}\n"
        story += "\n💡 The Renfe website may be temporarily unavailable or the station names may not match.\n"
        story += "   Try using exact station names like 'MADRID PTA. ATOCHA - ALMUDENA GRANDES' or 'BARCELONA-SANTS'.\n"

    story += "\n═══════════════════════════════════\n"

    return story


# ============================================================================
# 5. Server Startup
# ============================================================================

# Check for data updates before loading (optional - comment out to disable)
try:
    from update_data import update_if_needed
    update_if_needed()
except Exception as e:
    print(f"⚠️  Could not check for updates: {e}")

# Load GTFS data on module import
load_gtfs_data()


if __name__ == "__main__":
    # Run the MCP server
    mcp.run()
