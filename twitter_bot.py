#!/usr/bin/env python3
"""
Twitter Bot - Automated posting using Twitter API v2 with OAuth 2.0
"""

import os
import sys
from dotenv import load_dotenv
import tweepy

# Load environment variables from .env file
load_dotenv()


class TwitterBot:
    """Twitter Bot class for automated posting using Twitter API v2"""
    
    def __init__(self):
        """Initialize the Twitter bot with OAuth 2.0 credentials"""
        # Get credentials from environment variables
        self.client_id = os.getenv('TWITTER_CLIENT_ID')
        self.client_secret = os.getenv('TWITTER_CLIENT_SECRET')
        self.access_token = os.getenv('TWITTER_ACCESS_TOKEN')
        self.refresh_token = os.getenv('TWITTER_REFRESH_TOKEN')
        
        # Validate credentials
        if not all([self.client_id, self.client_secret, self.access_token]):
            raise ValueError(
                "Missing required credentials. Please check your .env file.\n"
                "Required: TWITTER_CLIENT_ID, TWITTER_CLIENT_SECRET, TWITTER_ACCESS_TOKEN"
            )
        
        # Initialize Twitter API v2 client with OAuth 2.0
        self.client = None
        self._authenticate()
    
    def _authenticate(self):
        """Authenticate with Twitter API v2 using OAuth 2.0"""
        try:
            # Create client with OAuth 2.0 user authentication
            self.client = tweepy.Client(
                bearer_token=None,
                consumer_key=self.client_id,
                consumer_secret=self.client_secret,
                access_token=self.access_token,
                access_token_secret=self.refresh_token
            )
            print("✓ Successfully authenticated with Twitter API v2")
        except Exception as e:
            raise Exception(f"Authentication failed: {str(e)}")
    
    def post_tweet(self, text):
        """
        Post a tweet using Twitter API v2
        
        Args:
            text (str): The tweet text to post (max 280 characters)
            
        Returns:
            dict: Response from Twitter API containing tweet data
        """
        if not text:
            raise ValueError("Tweet text cannot be empty")
        
        if len(text) > 280:
            raise ValueError(f"Tweet text too long ({len(text)} characters). Maximum is 280 characters.")
        
        try:
            # Post tweet using API v2
            response = self.client.create_tweet(text=text)
            print(f"✓ Tweet posted successfully!")
            print(f"  Tweet ID: {response.data['id']}")
            print(f"  Text: {text}")
            return response.data
        except tweepy.errors.TweepyException as e:
            raise Exception(f"Failed to post tweet: {str(e)}")
    
    def verify_credentials(self):
        """
        Verify that the credentials are valid
        
        Returns:
            bool: True if credentials are valid, False otherwise
        """
        try:
            # Try to get authenticated user's information
            user = self.client.get_me()
            if user.data:
                print(f"✓ Credentials verified for user: @{user.data.username}")
                return True
            return False
        except Exception as e:
            print(f"✗ Credential verification failed: {str(e)}")
            return False


def main():
    """Main function to run the Twitter bot"""
    print("=" * 50)
    print("Twitter Bot - Automated Posting")
    print("=" * 50)
    print()
    
    try:
        # Initialize the bot
        bot = TwitterBot()
        
        # Verify credentials
        print("\nVerifying credentials...")
        if not bot.verify_credentials():
            print("\n✗ Failed to verify credentials. Please check your .env file.")
            sys.exit(1)
        
        # Get tweet message from environment or use default
        tweet_message = os.getenv('TWEET_MESSAGE', 'Hello from my automated Twitter bot!')
        
        # Post a tweet
        print("\nPosting tweet...")
        bot.post_tweet(tweet_message)
        
        print("\n" + "=" * 50)
        print("✓ Bot execution completed successfully!")
        print("=" * 50)
        
    except ValueError as e:
        print(f"\n✗ Configuration Error: {str(e)}")
        print("\nPlease ensure you have:")
        print("1. Copied .env.example to .env")
        print("2. Added your Twitter API credentials to .env")
        sys.exit(1)
    except Exception as e:
        print(f"\n✗ Error: {str(e)}")
        sys.exit(1)


if __name__ == "__main__":
    main()
