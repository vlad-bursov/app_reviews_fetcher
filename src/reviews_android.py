import requests
import json
# for Google Play reviews and app details
from google_play_scraper import reviews, app
from datetime import datetime, timedelta, timezone
from one_pass_file_fetcher import fetch_file_with_op


def post_to_slack(text, slack_webhook_url):
    payload = {"text": text}
    requests.post(slack_webhook_url, json=payload)
    print(text)

# Function to get latest reviews from Google Play
def fetch_google_play_reviews(app_id):
    result, _ = reviews(
        app_id,
        count=100  # Fetch more reviews to cover all cases
    )
    return result

# Function to get app ratings summary
def fetch_google_play_ratings(app_id):
    app_info = app(app_id)
    ratings = {
        "total_ratings": app_info["ratings"],
        "average_rating": app_info["score"],
        "rating_breakdown": app_info["histogram"],
        "installs" : app_info["realInstalls"]
    }
    return ratings

# Filter reviews from yesterday
def filter_reviews_from_yesterday(reviews_list):
    days_before = 4
    yesterday = datetime.now(timezone.utc) - timedelta(days=days_before)
    yesterday_start = datetime(
        yesterday.year, yesterday.month, yesterday.day, tzinfo=timezone.utc)
    yesterday_end = yesterday_start + timedelta(days=days_before)

    filtered_reviews = []
    for review in reviews_list:
        review_time = datetime.fromtimestamp(
            review['at'].timestamp(), tz=timezone.utc)
        if yesterday_start <= review_time < yesterday_end:
            filtered_reviews.append(review)
    return filtered_reviews

# Main script to fetch and send new reviews and ratings to Slack
def main(app_id, slack_webhook_url):
    # Fetch reviews
    all_reviews = fetch_google_play_reviews(app_id)
    yesterday_reviews = filter_reviews_from_yesterday(all_reviews)

    # Fetch ratings
    ratings = fetch_google_play_ratings(app_id)

    # Prepare Slack messages
    messages = ["*Android*\n",f"*Total Installs: {ratings['installs']}*\n"]

    if yesterday_reviews:
        messages.append("*New Reviews from Yesterday:*")
        for review in yesterday_reviews:
            text = f"{review['userName']}: {review['content']}(Rating: {review['score']}/5)"
            messages.append(text)
    else:
        messages.append("No new reviews from yesterday.")

    # Add ratings summary
    messages.append(f"Total Ratings: {ratings['total_ratings']}")
    messages.append(f"Average Rating: {round(ratings['average_rating'], 2)}/5")
    messages.append(f"\n")
    # Send to Slack
    post_to_slack("\n".join(messages), slack_webhook_url)


if __name__ == "__main__":
    config = fetch_file_with_op(item_title="app_review_config_android")
    if config:
        main(
            config["app_id"],
            config["slack_webhook_url"]
        )
    else:
        print("Failed to load configuration.")