# Twitter Bot - Automated Posting

An automated Twitter bot account using Python, OAuth 2.0, and Twitter API v2. This bot can automatically post tweets using the free tier of Twitter API.

## Features

- ✅ OAuth 2.0 authentication
- ✅ Twitter API v2 integration
- ✅ Automated tweet posting
- ✅ Credential verification
- ✅ Environment-based configuration
- ✅ Free tier compatible

## Prerequisites

1. **Python 3.7 or higher**
2. **Twitter Developer Account** (free tier)
   - Sign up at [Twitter Developer Portal](https://developer.twitter.com/en/portal/dashboard)
   - Create a new project and app
   - Enable OAuth 2.0 and get your credentials

## Setup Instructions

### 1. Clone the Repository

```bash
git clone https://github.com/moreorless13/twitterbot.git
cd twitterbot
```

### 2. Install Dependencies

```bash
pip install -r requirements.txt
```

Or if you prefer using a virtual environment (recommended):

```bash
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### 3. Configure Twitter API Credentials

1. Copy the example environment file:
   ```bash
   cp .env.example .env
   ```

2. Edit `.env` and add your Twitter API credentials:
   
   **Option A - Using Bearer Token + OAuth 2.0 (Recommended):**
   ```
   TWITTER_BEARER_TOKEN=your_bearer_token_here
   TWITTER_CLIENT_ID=your_client_id_here
   TWITTER_CLIENT_SECRET=your_client_secret_here
   TWITTER_ACCESS_TOKEN=your_access_token_here
   TWITTER_REFRESH_TOKEN=your_refresh_token_here
   ```
   
   **Option B - Using OAuth 2.0 User Context Only:**
   ```
   TWITTER_CLIENT_ID=your_client_id_here
   TWITTER_CLIENT_SECRET=your_client_secret_here
   TWITTER_ACCESS_TOKEN=your_access_token_here
   TWITTER_REFRESH_TOKEN=your_refresh_token_here
   ```

3. (Optional) Customize your tweet message:
   ```
   TWEET_MESSAGE=Your custom tweet message here!
   ```

### Getting Twitter API Credentials

1. Go to [Twitter Developer Portal](https://developer.twitter.com/en/portal/dashboard)
2. Create a new project and app (if you haven't already)
3. Navigate to your app settings
4. Under "User authentication settings", set up OAuth 2.0
   - Set app permissions to **Read and Write** (required for posting)
   - Set Type of App to "Web App, Automated App or Bot"
   - Add a callback URL (can be http://localhost:3000 for testing)
5. In the "Keys and tokens" tab:
   - Generate **Bearer Token** (for app-level authentication)
   - Generate **OAuth 2.0 Client ID and Client Secret**
   - Generate **Access Token and Secret** (note: the secret is your refresh token for OAuth 2.0)
6. Copy all credentials to your `.env` file

**Important**: 
- Make sure your app has **Read and Write** permissions to post tweets
- The Access Token and Access Token Secret are generated with your user context
- For OAuth 2.0, the "Access Token Secret" functions as your refresh token

## Usage

### Basic Usage

Run the bot to post a tweet:

```bash
python twitter_bot.py
```

The bot will:
1. Load credentials from `.env` file
2. Authenticate with Twitter API v2
3. Verify your credentials
4. Post the configured tweet message

### Customizing Tweet Content

You can customize the tweet message in two ways:

**Option 1**: Edit the `TWEET_MESSAGE` in your `.env` file:
```
TWEET_MESSAGE=Hello Twitter! This is my automated bot 🤖
```

**Option 2**: Modify the bot script to implement custom logic for generating tweet content.

## Project Structure

```
twitterbot/
├── .env.example          # Example environment variables template
├── .gitignore           # Git ignore file (excludes .env and Python cache)
├── requirements.txt     # Python dependencies
├── twitter_bot.py       # Main bot script
└── README.md           # This file
```

## Code Overview

The bot is built using the `tweepy` library which provides a Python interface to Twitter API v2:

- **TwitterBot class**: Handles authentication and posting
- **OAuth 2.0**: Secure authentication method
- **API v2**: Uses the latest Twitter API version
- **Environment variables**: Secure credential management

### Key Components

- `_authenticate()`: Handles OAuth 2.0 authentication with Twitter
- `post_tweet()`: Posts a tweet (max 280 characters)
- `verify_credentials()`: Verifies API credentials are valid

## Security Notes

⚠️ **Important Security Practices**:

1. **Never commit your `.env` file** - It contains sensitive credentials
2. The `.gitignore` file is configured to exclude `.env` automatically
3. Use `.env.example` as a template for sharing configuration structure
4. Rotate your tokens regularly
5. Only grant necessary permissions to your Twitter app

## Troubleshooting

### Common Issues

**"Missing required credentials" error**:
- Ensure you've created a `.env` file from `.env.example`
- Verify all required credentials are filled in

**"Authentication failed" error**:
- Double-check your credentials are correct
- Ensure your app has the correct permissions (Read and Write)
- Verify your access token hasn't expired

**"Failed to post tweet" error**:
- Check that your app has Write permissions
- Ensure you're not posting duplicate tweets (Twitter blocks duplicates)
- Verify your tweet is under 280 characters

## API Rate Limits (Free Tier)

The free tier of Twitter API v2 includes:
- **Tweet creation**: Limited posts per month
- **Read operations**: Rate-limited requests

Monitor your usage in the [Twitter Developer Portal](https://developer.twitter.com/en/portal/dashboard).

## Future Enhancements

Possible improvements for this bot:
- Scheduled posting
- Reply to mentions
- Tweet different content types (images, videos)
- Analytics tracking
- Multiple account support

## License

This project is open source and available for educational purposes.

## Resources

- [Twitter API v2 Documentation](https://developer.twitter.com/en/docs/twitter-api)
- [Tweepy Documentation](https://docs.tweepy.org/)
- [OAuth 2.0 Guide](https://developer.twitter.com/en/docs/authentication/oauth-2-0)

## Support

For issues or questions:
1. Check the troubleshooting section above
2. Review Twitter's API documentation
3. Open an issue on GitHub
