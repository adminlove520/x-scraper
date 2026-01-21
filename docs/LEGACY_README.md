# Twitter/X.com Post Fetcher

A Python script that fetches the latest posts and news from any given user's Twitter/X.com profile using the Twitter API v2.

## Features

- Fetch latest tweets from any public Twitter user
- Display tweets with metrics (likes, retweets, replies, quotes)
- Extract hashtags, mentions, and URLs
- Save results to JSON file
- Command-line interface for easy usage
- Excludes retweets and replies (shows only original content)

## Prerequisites

1. **Twitter Developer Account**: You need a Twitter Developer account to access the API
2. **Bearer Token**: Generate a Bearer Token from your Twitter Developer dashboard
3. **Python 3.7+**: Make sure you have Python installed

## Setup

### 1. Get Twitter API Access

1. Go to [Twitter Developer Portal](https://developer.twitter.com/)
2. Apply for a developer account (if you don't have one)
3. Create a new app/project
4. Generate a **Bearer Token** from your app's "Keys and Tokens" section

### 2. Install Dependencies

```bash
# Install required packages
pip install -r requirements.txt
```

### 3. Configure API Token

Choose one of these methods:

**Option A: Environment Variable (Recommended)**
```bash
# Copy the example file
cp .env.example .env

# Edit .env file and add your token
echo "TWITTER_BEARER_TOKEN=your_actual_bearer_token_here" > .env
```

**Option B: Command Line Argument**
```bash
# Use --bearer-token flag when running the script
python twitter_fetcher.py --username elonmusk --bearer-token your_token_here
```

## Usage

### Basic Usage

```bash
# Fetch latest 10 tweets from a user
python twitter_fetcher.py --username elonmusk

# Fetch latest 20 tweets
python twitter_fetcher.py --username elonmusk --count 20

# Save to specific file
python twitter_fetcher.py --username elonmusk --output elon_tweets.json
```

### Command Line Options

```
usage: twitter_fetcher.py [-h] --username USERNAME [--count COUNT] [--output OUTPUT] [--bearer-token BEARER_TOKEN]

Fetch latest tweets from a Twitter user

optional arguments:
  -h, --help            show this help message and exit
  --username USERNAME, -u USERNAME
                        Twitter username (without @)
  --count COUNT, -c COUNT
                        Number of tweets to fetch (default: 10, max: 100)
  --output OUTPUT, -o OUTPUT
                        Output JSON file (optional)
  --bearer-token BEARER_TOKEN
                        Twitter API Bearer Token (or set TWITTER_BEARER_TOKEN env var)
```

### Examples

```bash
# Fetch tweets from different users
python twitter_fetcher.py -u elonmusk -c 15
python twitter_fetcher.py -u openai -c 25 -o openai_posts.json
python twitter_fetcher.py -u nasa --count 30

# Using full username format (@ will be automatically removed)
python twitter_fetcher.py -u @elonmusk
```

## Output Format

The script displays tweets in the terminal and saves them to a JSON file. Each tweet includes:

- **Tweet ID and URL**
- **Creation timestamp**
- **Full text content**
- **Engagement metrics** (likes, retweets, replies, quotes)
- **Hashtags** (if any)
- **Mentions** (if any)
- **URLs** (if any)

### Sample Output

```
================================================================================
LATEST 5 TWEETS
================================================================================

[1] Tweet ID: 1234567890123456789
Created: 2024-01-15T10:30:00+00:00
URL: https://twitter.com/elonmusk/status/1234567890123456789

Text:
Just launched another rocket! 🚀 The future is looking bright for space exploration.

Metrics: ❤️ 15420 | 🔄 3250 | 💬 892 | 📝 156
Hashtags: #SpaceX, #Mars
Mentions: @spacex
--------------------------------------------------------------------------------
```

### JSON Output Structure

```json
[
  {
    "id": "1234567890123456789",
    "text": "Tweet content here...",
    "created_at": "2024-01-15T10:30:00+00:00",
    "url": "https://twitter.com/username/status/1234567890123456789",
    "metrics": {
      "retweets": 3250,
      "likes": 15420,
      "replies": 892,
      "quotes": 156
    },
    "hashtags": ["SpaceX", "Mars"],
    "mentions": ["spacex"],
    "urls": ["https://example.com"]
  }
]
```

## Error Handling

The script handles common errors gracefully:

- **Invalid username**: Shows "User not found" message
- **Private account**: May return no tweets if account is private
- **API rate limits**: Twitter API has rate limits (300 requests per 15 minutes)
- **Network issues**: Connection errors are caught and displayed
- **Missing dependencies**: Clear error messages for missing packages

## Rate Limits

Twitter API v2 rate limits:
- **User lookup**: 300 requests per 15 minutes
- **User tweets**: 300 requests per 15 minutes
- Each request can fetch up to 100 tweets

## Troubleshooting

### Common Issues

1. **"Error: tweepy not installed"**
   ```bash
   pip install tweepy
   ```

2. **"Error: Twitter API Bearer Token is required"**
   - Make sure you've set up your `.env` file correctly
   - Or use the `--bearer-token` argument

3. **"User 'username' not found"**
   - Check if the username is correct
   - Make sure the account exists and is public

4. **"No tweets found"**
   - User might have no tweets
   - Account might be private
   - User might have only retweets/replies (which are excluded)

5. **API Rate Limit Exceeded**
   - Wait 15 minutes before making more requests
   - Reduce the number of requests

## Security Notes

- Never commit your `.env` file to version control
- Keep your Bearer Token secure and private
- The `.env.example` file is safe to commit (it doesn't contain real tokens)

## License

This project is open source and available under the MIT License.