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
   ```
   TWITTER_CLIENT_ID=your_client_id_here
   TWITTER_CLIENT_SECRET=your_client_secret_here
   REDIRECT_URI=your_redirect_uri_here
   TWITTER_ACCESS_TOKEN=your_access_token_here
   TWITTER_REFRESH_TOKEN=your_refresh_token_here
   ```

#### Redirect URI (Callback URL)

You can use either:

- **Local dev**: `http://127.0.0.1:5000/oauth/callback`
- **GitHub Pages** (recommended if you want an https callback):
  `https://<YOUR_GITHUB_USERNAME>.github.io/<YOUR_REPO_NAME>/oauth-callback.html`

This repo includes a minimal GitHub Pages callback page at `docs/oauth-callback.html`.

3. (Optional) Customize your tweet message:
   ```
   TWEET_MESSAGE=Your custom tweet message here!
   ```

### Getting Twitter API Credentials

1. Go to [Twitter Developer Portal](https://developer.twitter.com/en/portal/dashboard)
2. Create a new project and app (if you haven't already)
3. Navigate to your app settings
4. Under "User authentication settings", set up OAuth 2.0
5. Generate your access token and refresh token
6. Copy the credentials to your `.env` file

**Important**: Make sure your app has **Read and Write** permissions to post tweets.

## Usage

### Basic Usage

Run the bot to post a tweet:

```bash
python twitter_bot.py
```

## Scheduling (macOS) — Post 3 Times Per Day

To post automatically three times per day on macOS, use `launchd`.

This repo includes:
- `run_bot.sh` — runs the bot using the repo virtualenv and loads `.env`
- `com.moreorless13.twitterbot.plist` — `launchd` job that runs 3 times per day (default: 09:00, 14:00, 19:00)

### 1) Make the runner executable

```bash
chmod +x run_bot.sh
```

### 2) Install the LaunchAgent

```bash
mkdir -p ~/Library/LaunchAgents
cp com.moreorless13.twitterbot.plist ~/Library/LaunchAgents/
```

### 3) Load (start) the scheduler

```bash
launchctl unload -w ~/Library/LaunchAgents/com.moreorless13.twitterbot.plist 2>/dev/null || true
launchctl load -w ~/Library/LaunchAgents/com.moreorless13.twitterbot.plist
```

If you change the schedule times inside the `.plist`, run the unload/load commands again to apply changes.

Logs will be written to:
- `launchd.out.log`
- `launchd.err.log`

**Important**:
- The `.plist` contains an absolute path to `run_bot.sh`. If you move this repo, update the path inside `com.moreorless13.twitterbot.plist` before loading it.
- X/Twitter may block exact duplicate tweets. If you run on a schedule, prefer rotating messages via `TWEET_MESSAGES`.

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

**Option 1b (recommended for scheduling)**: Rotate multiple messages with `TWEET_MESSAGES`:
```
TWEET_MESSAGES=First tweet of the day!|Second tweet later today!|Third tweet this evening!
```

When `TWEET_MESSAGES` is set, each run posts the *next* message in the list.

## Deploy & Schedule on GitHub (Server)

If you want this to run on a server (not your Mac), the simplest option is GitHub Actions.

This repo includes a scheduled workflow: `.github/workflows/post-tweets.yml`.

### 1) Push the repo to GitHub

Create a GitHub repository and push this folder.

### 2) Add GitHub Secrets

In your repo: **Settings → Secrets and variables → Actions → Secrets**, add:
- `TWITTER_CLIENT_ID`
- `TWITTER_CLIENT_SECRET`
- `REDIRECT_URI` (must match the redirect URI you used when generating tokens)
- `TWITTER_ACCESS_TOKEN`
- `TWITTER_REFRESH_TOKEN` (recommended so the workflow can refresh when needed)

### 2b) Generate tokens using the GitHub Pages redirect URI (one-time)

If you change `REDIRECT_URI`, you must re-authorize and generate new tokens.

1. Enable GitHub Pages for this repo:
   - Repo **Settings → Pages**
   - Source: **Deploy from a branch**
   - Branch: `main` (or `master`) and folder: `/docs`
2. Set `REDIRECT_URI` in your local `.env` to your Pages URL:
   - `https://<YOUR_GITHUB_USERNAME>.github.io/<YOUR_REPO_NAME>/oauth-callback.html`
3. Run locally:
   - `python twitter_bot.py --authorize`
4. Authorize in the browser; you’ll land on the GitHub Pages callback page.
5. Copy the **full** URL shown there and run:
   - `python twitter_bot.py --callback-url "<PASTE_FULL_URL>"`
6. Copy the resulting `TWITTER_ACCESS_TOKEN` / `TWITTER_REFRESH_TOKEN` values into GitHub Secrets.

### 3) Add GitHub Variable for your 3 tweets

In **Settings → Secrets and variables → Actions → Variables**, add:
- `TWEET_MESSAGES` = `tweet1|tweet2|tweet3`

### 4) Enable the schedule

The workflow runs 3x/day using GitHub cron (UTC). For **EST** it is set to:
- 09:00 EST → 14:00 UTC
- 14:00 EST → 19:00 UTC
- 19:00 EST → 00:00 UTC

**Note:** GitHub cron is always UTC. If you observe DST (EDT), these will shift by 1 hour unless you update the cron entries.

### 5) Test it manually

Go to **Actions → Post tweets (3x/day) → Run workflow**.

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
