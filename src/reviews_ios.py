import csv
import gzip
from io import StringIO
import jwt
import requests
import time
from datetime import datetime, timedelta, timezone

from one_pass_file_fetcher import fetch_file_with_op
from sales_report import get_report_data

# Function to post a message to Slack


def post_to_slack(text, slack_webhook_url):
    payload = {"text": text}
    requests.post(slack_webhook_url, json=payload)
    print(text)

# Function to generate JWT token


def generate_token(key_id, issuer_id, private_key):
    headers = {
        "alg": "ES256",
        "kid": key_id
    }
    payload = {
        "iss": issuer_id,
        "exp": int(time.time()) + 20 * 60,  # Token valid for 20 minutes
        "aud": "appstoreconnect-v1"
    }
    return jwt.encode(payload, private_key, algorithm="ES256", headers=headers)

# Function to fetch reviews from the App Store


def fetch_reviews(app_id, token):
    url = f"https://api.appstoreconnect.apple.com/v1/apps/{app_id}/customerReviews"
    headers = {"Authorization": f"Bearer {token}"}
    response = requests.get(url, headers=headers)
    # Check if the request was successful
    if response.status_code == 200:
        return response.json()  # Return the reviews data as JSON
    else:
        return {"error": f"Failed to fetch reviews, status code: {response.status_code}"}

# Filter reviews from yesterday


def filter_reviews_from_yesterday(reviews_list):
    days_before = 12
    yesterday = datetime.now(timezone.utc) - timedelta(days=days_before)
    yesterday_start = datetime(
        yesterday.year, yesterday.month, yesterday.day, tzinfo=timezone.utc)
    yesterday_end = yesterday_start + timedelta(days=days_before)

    filtered_reviews = []
    for review in reviews_list:
        review_attr = review['attributes']
        review_time = datetime.strptime(
            review_attr['createdDate'], "%Y-%m-%dT%H:%M:%S%z")
        if yesterday_start <= review_time < yesterday_end:
            filtered_reviews.append(review)
    return filtered_reviews


def get_country_ratings(app_id, country_codes):
    base_url = "https://itunes.apple.com/lookup"
    ratings_data = []

    for country in country_codes:
        response = requests.get(
            base_url, params={"id": app_id, "country": country})
        response.raise_for_status()
        data = response.json()

        if data["resultCount"] > 0:
            app_data = data["results"][0]
            ratings_data.append({
                "country": country,
                "average_rating": app_data.get("averageUserRating", 0),
                "rating_count": app_data.get("userRatingCount", 0)
            })

    return ratings_data


def flatten_ratings(ratings_data):
    total_ratings = sum(data["rating_count"] for data in ratings_data)
    if total_ratings == 0:
        return {"global_average_rating": 0, "total_ratings": 0}

    weighted_sum = sum(data["average_rating"] *
                       data["rating_count"] for data in ratings_data)
    global_average = weighted_sum / total_ratings

    return {"global_average_rating": round(global_average, 2), "total_ratings": round(total_ratings, 2)}

# Main function

def main(key_id, issuer_id, private_key, slack_webhook_url, app_id, vendor_number, start_date):
    token = generate_token(key_id, issuer_id, private_key.replace("\\n", "\n"))
    downloads = get_report_data(token, app_id, start_date, vendor_number)

    reviews_data = fetch_reviews(app_id, token)
    if "data" not in reviews_data:
        print["reviews_data:" + reviews_data]
        print("Error fetching reviews.")
        return


    # Fetch ratings for only USA, Canada and Australia
    country_codes = ["us", "ca", "au"]

    ratings = get_country_ratings(app_id, country_codes)

    global_ratings = flatten_ratings(ratings)
    yesterday_reviews = filter_reviews_from_yesterday(reviews_data["data"])

    # Prepare Slack messages
    messages = ["*iOS*\n",downloads]

    if yesterday_reviews:
        messages.append("*New Reviews from Yesterday:*")
        for review in yesterday_reviews:
            attributes = review["attributes"]
            user_name = attributes.get("reviewerNickname", "Anonymous")
            review_text = attributes.get("body", "No content")
            rating = attributes.get("rating")
            text = f"{user_name}: {review_text} (Rating: {rating}/5)"
            messages.append(text)
    else:
        messages.append("No new reviews from yesterday.")

    # Add ratings by country
    messages.append("\n*iOS App Ratings by Country:*")
    country_names = {"us": "USA", "ca": "Canada", "au": "Australia"}
    for rating in ratings:
        country_code = rating["country"]
        country_name = country_names.get(country_code, country_code.upper())
        messages.append(f"{country_name}: {rating['average_rating']} ({rating['rating_count']} ratings)")
    
    messages.append(f"\nTotal Ratings: {global_ratings['total_ratings']}")

    # Send to Slack
    post_to_slack("\n".join(messages), slack_webhook_url)


if __name__ == "__main__":
    config = fetch_file_with_op("app_review_config_ios")
    if config:
        main(
            config["key_id"],
            config["issuer_id"],
            config["private_key"],
            config["slack_webhook_url"],
            config["app_id"],
            config["vendor_number"],
            config["start_date"]
        )
    else:
        print("Failed to load configuration.")
