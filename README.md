# App Reviews Monitor

A Python application that monitors and reports app reviews and ratings from both iOS App Store and Google Play Store.

## Features

- Fetches and analyzes app reviews from iOS App Store
- Retrieves app ratings from multiple countries
- Generates sales reports
- Posts updates to Slack

## Setup

1. Clone the repository:
```bash
git clone <repository-url>
cd app-reviews-monitor
```

2. Create and activate a virtual environment:
```bash
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Configure the application:
   - Create configuration files for iOS and Android apps
   - Add your App Store Connect API credentials
   - Set up Slack webhook URL

## Configuration

Create the following configuration files:

### iOS Configuration (app_review_config_ios)
```json
{
    "key_id": "YOUR_KEY_ID",
    "issuer_id": "YOUR_ISSUER_ID",
    "private_key": "YOUR_PRIVATE_KEY",
    "slack_webhook_url": "YOUR_SLACK_WEBHOOK_URL",
    "app_id": "YOUR_APP_ID",
    "vendor_number": "YOUR_VENDOR_NUMBER",
    "start_date": "YYYY-MM-DD"
}
```

## Usage

Run the iOS reviews monitor:
```bash
python src/reviews_ios.py
```

## Project Structure

```
.
├── .gitignore
├── README.md
├── requirements.txt
└── src/
    ├── reviews_ios.py
    ├── sales_report.py
    └── one_pass_file_fetcher.py
```

## Security Notes

- Never commit sensitive configuration files
- Keep your API keys and credentials secure
- Use environment variables for sensitive data in production

## License

[Your chosen license] 