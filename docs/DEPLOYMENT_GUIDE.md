# 🚀 X-Scraper Deployment & Usage Guide

This guide provides step-by-step instructions for deploying and using the X-Scraper tool from the GitHub repository.

## 📋 Table of Contents

- [Quick Setup](#-quick-setup)
- [Detailed Installation](#-detailed-installation)
- [First Run](#-first-run)
- [Usage Examples](#-usage-examples)
- [Configuration](#-configuration)
- [Troubleshooting](#-troubleshooting)
- [Advanced Usage](#-advanced-usage)

## ⚡ Quick Setup

### 1. Clone the Repository

```bash
# Clone the repository
git clone https://github.com/adminlove520/x-scraper.git
cd x-scraper
```

### 2. Setup Environment

```bash
# Create virtual environment
python -m venv venv

# Activate virtual environment
# On Windows:
venv\Scripts\activate
# On macOS/Linux:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### 3. Quick Test

```bash
# Test single user scraping
python src/advanced_twitter_scraper.py --username elonmusk --count 3

# Test batch scraping
echo "elonmusk" > test_user.txt
python src/enterprise_batch_scraper.py --users test_user.txt --tweet-count 3 --workers 1
```

## 🔧 Detailed Installation

### Prerequisites

- **Python 3.8+**: Download from [python.org](https://www.python.org/downloads/)
- **Chrome Browser**: Download from [google.com/chrome](https://www.google.com/chrome/)
- **Git**: Download from [git-scm.com](https://git-scm.com/downloads)

### Step-by-Step Installation

#### 1. Download the Code

**Option A: Using Git (Recommended)**
```bash
git clone https://github.com/adminlove520/x-scraper.git
cd x-scraper
```

**Option B: Download ZIP**
1. Go to [https://github.com/adminlove520/x-scraper](https://github.com/adminlove520/x-scraper)
2. Click "Code" → "Download ZIP"
3. Extract the ZIP file
4. Open terminal/command prompt in the extracted folder

#### 2. Create Virtual Environment

**Windows:**
```cmd
python -m venv venv
venv\Scripts\activate
```

**macOS/Linux:**
```bash
python3 -m venv venv
source venv/bin/activate
```

#### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

#### 4. Verify Installation

```bash
# Check Python version
python --version

# Check installed packages
pip list

# Test scraper
python src/advanced_twitter_scraper.py --username elonmusk --count 1
```

## 🎯 First Run

### Single User Example

```bash
# Scrape 5 tweets from @elonmusk
python src/advanced_twitter_scraper.py \
  --username elonmusk \
  --count 5 \
  --method selenium \
  --headless
```

**Expected Output:**
```
✅ Successfully scraped 5 tweets for elonmusk
📁 Results saved to: elonmusk_advanced_YYYYMMDD_HHMMSS.json
```

### Multiple Users Example

```bash
# Create user list
echo -e "elonmusk\nbillgates\ntim_cook" > my_users.txt

# Scrape 3 tweets from each user
python src/enterprise_batch_scraper.py \
  --users my_users.txt \
  --tweet-count 3 \
  --workers 2 \
  --headless
```

**Expected Output:**
```
🚀 Starting batch scraping...
👥 Processing 3 users with 2 workers
✅ elonmusk: 3 tweets scraped
✅ billgates: 3 tweets scraped
✅ tim_cook: 3 tweets scraped
📊 SCRAPING COMPLETE
📁 Results saved to: batch_results.json
```

## 📖 Usage Examples

### Basic Examples

#### 1. Single User with Custom Settings

```bash
python src/advanced_twitter_scraper.py \
  --username nasa \
  --count 20 \
  --delay-min 2.0 \
  --delay-max 4.0 \
  --headless
```

#### 2. Batch Processing with Text File

```bash
# Create user list
cat > tech_leaders.txt << EOF
elonmusk
billgates
tim_cook
sundarPichai
satyanadella
EOF

# Scrape with custom settings
python src/enterprise_batch_scraper.py \
  --users tech_leaders.txt \
  --tweet-count 10 \
  --workers 3 \
  --delay-min 1.5 \
  --delay-max 3.0 \
  --format csv \
  --headless
```

#### 3. Using JSON Configuration

```bash
# Use predefined configuration
python src/enterprise_batch_scraper.py \
  --config config/twitter_exclusive_config.json \
  --headless
```

### Advanced Examples

#### 1. Large Scale Processing

```bash
# For 100+ users
python src/enterprise_batch_scraper.py \
  --users large_user_list.txt \
  --tweet-count 15 \
  --workers 5 \
  --delay-min 2.0 \
  --delay-max 5.0 \
  --format csv \
  --log-level INFO \
  --headless
```

#### 2. Debug Mode

```bash
# Enable detailed logging
python src/enterprise_batch_scraper.py \
  --users users.txt \
  --tweet-count 5 \
  --workers 1 \
  --log-level DEBUG
```

#### 3. Production Run

```bash
# Background processing with logging
nohup python src/enterprise_batch_scraper.py \
  --config config/production_config.json \
  --headless \
  --format csv \
  > scraping.log 2>&1 &

# Monitor progress
tail -f scraping.log
```

## ⚙️ Configuration

### Creating User Lists

#### Text File Format

```bash
# Create simple user list
cat > my_users.txt << EOF
elonmusk
billgates
tim_cook
jeffbezos
EOF
```

#### JSON Configuration Format

```bash
# Create advanced configuration
cat > my_config.json << 'EOF'
{
  "users": [
    {"username": "elonmusk", "tweet_count": 20},
    {"username": "billgates", "tweet_count": 15},
    {"username": "tim_cook", "tweet_count": 10}
  ],
  "settings": {
    "max_workers": 3,
    "headless": true,
    "delay_range": [1.5, 3.0],
    "output_format": "json",
    "log_level": "INFO"
  }
}
EOF
```

### Environment Variables

```bash
# Copy example environment file
cp .env.example .env

# Edit with your preferences
nano .env  # or use your preferred editor
```

## 🛠️ Troubleshooting

### Common Issues and Solutions

#### 1. "No tweets found" Error

**Problem**: Scraper returns 0 tweets

**Solutions**:
```bash
# Test with known active account
python src/advanced_twitter_scraper.py --username elonmusk --count 3

# Check if account exists and is public
# Try different usernames
```

#### 2. Chrome Driver Issues

**Problem**: "ChromeDriver not found" or version mismatch

**Solutions**:
```bash
# Reinstall webdriver manager
pip uninstall webdriver-manager
pip install webdriver-manager

# Update Chrome browser to latest version
```

#### 3. Rate Limiting

**Problem**: "Rate limited" messages or slow responses

**Solutions**:
```bash
# Increase delays
python src/enterprise_batch_scraper.py \
  --users users.txt \
  --delay-min 3.0 \
  --delay-max 6.0 \
  --workers 1

# Use fewer workers
# Add longer delays between requests
```

#### 4. Memory Issues

**Problem**: System slowdown or out of memory errors

**Solutions**:
```bash
# Reduce workers and tweet count
python src/enterprise_batch_scraper.py \
  --users users.txt \
  --workers 1 \
  --tweet-count 5

# Process in smaller batches
# Close other applications
```

#### 5. Permission Errors

**Problem**: Cannot write to output files

**Solutions**:
```bash
# Check file permissions
ls -la

# Create data directory if missing
mkdir -p data

# Run with appropriate permissions
```

### Debug Commands

```bash
# Test single user first
echo "elonmusk" > test.txt
python src/enterprise_batch_scraper.py \
  --users test.txt \
  --tweet-count 1 \
  --workers 1 \
  --log-level DEBUG

# Check system resources
# On Linux/macOS:
top
# On Windows:
# Open Task Manager

# Verify Python environment
python --version
pip list | grep selenium
pip list | grep beautifulsoup4
```

## 🚀 Advanced Usage

### Batch Processing Strategies

#### For Large Datasets (1000+ users)

```bash
# Split large user list
split -l 500 large_users.txt batch_

# Process each batch
for batch in batch_*; do
  echo "Processing $batch..."
  python src/enterprise_batch_scraper.py \
    --users "$batch" \
    --tweet-count 10 \
    --workers 3 \
    --format csv \
    --output "results_${batch}.csv" \
    --headless
  
  echo "Waiting 5 minutes before next batch..."
  sleep 300
done
```

#### Automated Scheduling

```bash
# Create cron job for daily scraping
# Edit crontab
crontab -e

# Add line for daily execution at 2 AM
0 2 * * * cd /path/to/x-scraper && source venv/bin/activate && python src/enterprise_batch_scraper.py --config config/daily_config.json --headless
```

### Performance Optimization

#### System Resource Guidelines

| User Count | RAM Needed | Workers | Expected Time |
|------------|------------|---------|---------------|
| 1-50       | 2GB        | 1-3     | 10-30 min     |
| 50-200     | 4GB        | 3-5     | 1-2 hours     |
| 200-1000   | 8GB        | 5-8     | 3-6 hours     |
| 1000+      | 16GB+      | 8-12    | 6+ hours      |

#### Optimal Settings by Scale

```bash
# Small scale (1-50 users)
python src/enterprise_batch_scraper.py \
  --users small_list.txt \
  --tweet-count 15 \
  --workers 3 \
  --delay-min 1.0 \
  --delay-max 2.0

# Medium scale (50-500 users)
python src/enterprise_batch_scraper.py \
  --users medium_list.txt \
  --tweet-count 10 \
  --workers 5 \
  --delay-min 1.5 \
  --delay-max 3.0

# Large scale (500+ users)
python src/enterprise_batch_scraper.py \
  --users large_list.txt \
  --tweet-count 8 \
  --workers 8 \
  --delay-min 2.0 \
  --delay-max 5.0
```

### Data Analysis

#### Working with Results

```python
# Python script to analyze results
import json
import pandas as pd

# Load JSON results
with open('batch_results.json', 'r') as f:
    data = json.load(f)

# Convert to DataFrame
tweets = []
for result in data['results']:
    if result['success']:
        for tweet in result['tweets']:
            tweets.append({
                'username': result['username'],
                'text': tweet['text'],
                'likes': tweet['metrics']['likes'],
                'retweets': tweet['metrics']['retweets'],
                'created_at': tweet['created_at']
            })

df = pd.DataFrame(tweets)
print(f"Total tweets: {len(df)}")
print(f"Average likes: {df['likes'].mean():.2f}")
print(f"Top tweets by engagement:")
print(df.nlargest(5, 'likes')[['username', 'text', 'likes']])
```

## 📞 Support

### Getting Help

1. **Check Documentation**: Read README.md and SCRAPING_GUIDE.md
2. **Search Issues**: Look at [GitHub Issues](https://github.com/adminlove520/x-scraper/issues)
3. **Create Issue**: Report bugs or request features
4. **Include Details**: Always provide logs and system information

### Reporting Issues

When reporting issues, include:

```bash
# System information
python --version
pip list
uname -a  # On Linux/macOS
# or systeminfo on Windows

# Error logs
python src/enterprise_batch_scraper.py --users test.txt --log-level DEBUG

# Configuration used
cat config/your_config.json
```

### Contributing

```bash
# Fork the repository on GitHub
# Clone your fork
git clone https://github.com/yourusername/x-scraper.git
cd x-scraper

# Create feature branch
git checkout -b feature/your-feature-name

# Make changes and test
# Commit and push
git add .
git commit -m "Add your feature"
git push origin feature/your-feature-name

# Create Pull Request on GitHub
```

## 🎯 Best Practices Summary

### For New Users

1. **Start Small**: Test with 1-5 users first
2. **Use Headless Mode**: Always add `--headless` for production
3. **Monitor Logs**: Watch for rate limiting warnings
4. **Be Patient**: Large datasets take time
5. **Respect Limits**: Don't overwhelm Twitter's servers

### For Production Use

1. **Use JSON Configs**: Better control and repeatability
2. **Implement Monitoring**: Track progress and errors
3. **Plan Resources**: Ensure adequate system capacity
4. **Schedule Wisely**: Run during off-peak hours
5. **Backup Data**: Save results regularly

---

**🎉 You're Ready to Start Scraping!**

This tool is designed to be powerful yet user-friendly. Start with small tests and gradually scale up as you become more comfortable with the system.

**Repository**: [https://github.com/adminlove520/x-scraper](https://github.com/adminlove520/x-scraper)

**Happy Scraping! 🐦**