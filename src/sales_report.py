import csv
import datetime
import gzip
from io import StringIO
import requests

def generate_date_ranges(start_date_str):
    start_date = datetime.datetime.strptime(start_date_str, '%Y-%m-%d')
    current_date = datetime.datetime.now()
    
    date_ranges = []
    
    # 1. Yearly reports (except current year)
    for year in range(start_date.year, current_date.year):
        date_ranges.append(('YEARLY', str(year)))
    
    # 2. Monthly reports for current year (except current month)
    if start_date.year == current_date.year:
        start_month = start_date.month
    else:
        start_month = 1
        
    for month in range(start_month, current_date.month):
        date_ranges.append(('MONTHLY', f"{current_date.year}-{month:02d}"))
    
    # 3. Daily reports for current month (except today)
    if start_date.year == current_date.year and start_date.month == current_date.month:
        start_day = start_date.day
    else:
        start_day = 1
        
    for day in range(start_day, current_date.day):
        date_ranges.append(('DAILY', f"{current_date.year}-{current_date.month:02d}-{day:02d}"))
    
    return date_ranges

def get_report_data(jwt_token, app_id, start_date_str, vendor_number=None):
    date_ranges = generate_date_ranges(start_date_str)
    
    total_downloads = 0
    downloads_by_app = {}
    
    for frequency, date_str in date_ranges:
        report_results = get_app_units_report(jwt_token, frequency, "SUMMARY", app_id, date_str, vendor_number)
        
        if report_results:
        
            # Accumulate total downloads
            total_downloads += report_results['total_units']
            
            # Accumulate downloads by app
            for app, units in report_results['units_by_app'].items():
                if app in downloads_by_app:
                    downloads_by_app[app] += units
                else:
                    downloads_by_app[app] = units
        else:
            print(f"\nFailed to retrieve or process report data for {date_str}")
    
    # Print final totals
    return f"*Total Installs: {total_downloads}*\n"

def get_app_units_report(jwt_token, report_frequency, report_subtype, app_id=None, report_date=None, vendor_number=None):
    # --- Fetch data ---
    report_data = fetch_sales_report(jwt_token, frequency=report_frequency, report_sub_type=report_subtype, app_id=app_id, report_date=report_date, vendor_number=vendor_number)

    # --- Process the fetched data ---
    if report_data:
        total_units = 0
        units_by_app = {}

        for row in report_data:
            try:
                # The column names in the CSV header are used as keys in the dictionary
                units = int(row.get("Units", 0)) # Use .get() with a default to avoid KeyError
                app_name = row.get("Name", "Unknown App")
                product_type = row.get("Product Type Identifier", "Unknown Type") # e.g., "1F" for App, "IA1" for In-App Purchase

                # We are interested in app downloads/installs, which have specific Product Type Identifiers
                # "1F" is typically for app downloads
                # You might see other types like "1T" (TestFlight), "IA1" (In-App Purchase), etc.
                # Filter based on Product Type Identifier if needed to exclude IAPs, etc.
                if product_type == "1F": # Filter for App Units
                    total_units += units
                    if app_name in units_by_app:
                        units_by_app[app_name] += units
                    else:
                        units_by_app[app_name] = units

            except ValueError:
                print(f"Warning: Could not convert Units value '{row.get('Units', 'N/A')}' to integer for row: {row}")
            except Exception as e:
                print(f"An error occurred while processing row {row}: {e}")

        return {
            "total_units": total_units,
            "units_by_app": units_by_app
        }

    else:
        print("\nNo report data fetched.")
        return None

def fetch_sales_report(jwt_token, frequency="DAILY", report_sub_type="SUMMARY", app_id=None, report_date=None, vendor_number=None):
    api_url = "https://api.appstoreconnect.apple.com/v1/salesReports"
    params = {
        "filter[reportType]": "SALES",
        "filter[reportSubType]": report_sub_type,
        "filter[frequency]": frequency,
        "filter[vendorNumber]": vendor_number
    }
    
    if report_date:
        params["filter[reportDate]"] = report_date

    headers = {
        "Authorization": f"Bearer {jwt_token}",
        "Accept": "application/a-gzip" # Request gzipped data
    }

    try:
        response = requests.get(api_url, headers=headers, params=params)
        response.raise_for_status() # Raise an exception for bad status codes (4xx or 5xx)

        if response.status_code == 200:
            # Decompress the gzipped content
            decompressed_content = gzip.decompress(response.content).decode('utf-8')

            # Parse the tab-delimited CSV content
            csv_file = StringIO(decompressed_content)
            reader = csv.reader(csv_file, delimiter='\t')

            # Read header and data rows
            header = next(reader)
            data = [dict(zip(header, row)) for row in reader]
            return data

        else:
            print(f"Response Body: {response.text}")
            return []

    except requests.exceptions.RequestException as e:
        print(f"An error occurred during the API request: {e}")
        return []
    except gzip.BadGzipFile:
        print("Error: Received data is not a valid gzip file.")
        print(f"Response content (first 200 chars): {response.content[:200]}")
        return []
    except Exception as e:
        print(f"An unexpected error occurred during processing: {e}")
        return [] 