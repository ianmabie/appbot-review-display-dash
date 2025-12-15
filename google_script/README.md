# Google Apps Script Review Dashboard

A serverless version of the Appbot Review Display Dashboard that runs entirely on Google Apps Script with Google Sheets as the backend.

## Prerequisites

- A Google account
- Access to Google Drive and Google Sheets

## Quick Setup

### Step 1: Create a Google Sheet

1. Go to [Google Sheets](https://sheets.google.com) and create a new spreadsheet
2. Name it something like "App Reviews Dashboard"
3. The script will automatically create the "Reviews" sheet with proper headers on first run

### Step 2: Open Apps Script Editor

1. In your Google Sheet, go to **Extensions > Apps Script**
2. This opens the Apps Script editor in a new tab

### Step 3: Add the Code

1. **Replace the contents of `Code.gs`** with the contents from the `Code.gs` file in this folder
2. **Create a new HTML file:**
   - Click the **+** button next to "Files" in the left sidebar
   - Select **HTML**
   - Name it `Index` (it will become `Index.html`)
   - Replace the contents with the contents from the `Index.html` file in this folder

### Step 4: Deploy as Web App

1. Click **Deploy > New deployment**
2. Click the gear icon next to "Select type" and choose **Web app**
3. Configure the deployment:
   - **Description:** "App Reviews Dashboard v1"
   - **Execute as:** "Me"
   - **Who has access:** "Anyone"
4. Click **Deploy**
5. **Authorize the app** when prompted (click through the security warnings - this is your own script)
6. Copy the **Web app URL** - this is your webhook endpoint and dashboard URL

### Step 5: Configure Appbot Webhook

1. Go to your Appbot dashboard
2. Navigate to webhook settings
3. Set the webhook URL to your Apps Script Web app URL (ends in `/exec`)
4. Appbot will now send reviews to your Google Sheet

## Usage

### Viewing the Dashboard

Simply visit your Web app URL in any browser. The dashboard will display:
- The 100 most recent reviews
- Star ratings for each review
- App Store / Play Store indicator
- Publication date

### Dashboard Features

- **"Good Vibes Only" Toggle:** Filter to show only 5-star reviews
- **Auto-hide test reviews:** Reviews containing "test" or "appbot" are hidden by default
- **Hide individual reviews:** Click the × button on any review card
- **Auto-refresh:** Dashboard refreshes hourly automatically

### Testing the Webhook

You can test the webhook by sending a POST request:

```bash
curl -X POST "YOUR_WEB_APP_URL" \
  -H "Content-Type: application/json" \
  -d '{
    "reviews": [
      {
        "app_id": 12345,
        "app_store_id": "com.example.app",
        "author": "Test User",
        "rating": 5,
        "subject": "Great app!",
        "body": "This app is amazing and works perfectly.",
        "published_at": "2025-01-15",
        "sentiment": "positive"
      }
    ]
  }'
```

## File Structure

```
google_script/
├── Code.gs       # Main Apps Script with webhook handler and dashboard server
├── Index.html    # Dashboard HTML template with embedded CSS/JS
└── README.md     # This file
```

## Troubleshooting

### "Script function not found: doGet"
Make sure you copied the entire `Code.gs` file and saved it.

### Webhook returns 401/403
Ensure your deployment has "Who has access" set to "Anyone".

### Reviews not appearing
1. Check the Google Sheet directly to see if data was written
2. Look at **View > Executions** in Apps Script to see any errors
3. Verify the webhook payload matches the expected format

### Dashboard shows no reviews
The dashboard only shows reviews stored in the Google Sheet. Send a test webhook or wait for Appbot to send reviews.

## Limits and Quotas

Google Apps Script has generous free quotas:
- **Triggers:** 20 total / 20 per script
- **URL Fetch calls:** 20,000/day
- **Script runtime:** 6 minutes per execution
- **Spreadsheet cells:** 10 million per spreadsheet

For a review dashboard, you'll never hit these limits.

## Updating the Deployment

After making code changes:
1. Click **Deploy > Manage deployments**
2. Click the pencil icon to edit
3. Select **New version**
4. Click **Deploy**

The URL stays the same - no need to update Appbot.

## Security Notes

- The Web app URL acts as a secret key - anyone with the URL can view reviews or submit webhooks
- Consider adding a query parameter check if you need basic authentication
- Reviews are stored in your Google Sheet - you control the data

