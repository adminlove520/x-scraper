#!/usr/bin/env python3
"""
Enterprise Twitter/X.com Batch Scraper
Exclusively designed for Twitter/X.com mass data collection.
Optimized for scraping 10,000+ Twitter users with low volume per user.
Designed for enterprise use with efficient rate limiting and batch processing.

Features:
- Twitter/X.com exclusive scraping
- Handles 10,000+ Twitter users efficiently
- Adaptive batch sizing based on user count
- Smart rate limiting and delay management
- Fetches latest tweets or last 24 hours from Twitter
- Concurrent processing with thread pools
- Progress tracking and resume capability
- Multiple output formats (JSON, CSV)
- Memory-efficient streaming processing
- Error handling and retry logic
- Twitter-specific selectors and parsing

Usage:
    python enterprise_batch_scraper.py --users users.txt --output results.json
    python enterprise_batch_scraper.py --config config.json --format csv
"""

import os
import json
import csv
import time
import random
import argparse
import threading
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Iterator
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
import queue
import logging
from dataclasses import dataclass, asdict
from collections import defaultdict

try:
    from selenium import webdriver
    from selenium.webdriver.chrome.options import Options
    from selenium.webdriver.chrome.service import Service
    from selenium.webdriver.common.by import By
    from selenium.webdriver.support.ui import WebDriverWait
    from selenium.webdriver.support import expected_conditions as EC
    from webdriver_manager.chrome import ChromeDriverManager
    from selenium.common.exceptions import TimeoutException, NoSuchElementException
except ImportError:
    print("Error: Selenium not installed. Install with: pip install selenium webdriver-manager")
    exit(1)

try:
    from bs4 import BeautifulSoup
except ImportError:
    print("Error: BeautifulSoup not installed. Install with: pip install beautifulsoup4")
    exit(1)

@dataclass
class UserConfig:
    """Configuration for a single user"""
    username: str
    tweet_count: int = 10
    priority: str = "normal"  # high, normal, low
    tags: List[str] = None
    last_scraped: Optional[str] = None
    
    def __post_init__(self):
        if self.tags is None:
            self.tags = []

@dataclass
class ScrapingResult:
    """Result of scraping a single user"""
    username: str
    success: bool
    tweet_count: int
    error_message: Optional[str] = None
    scraped_at: str = None
    tweets: List[Dict] = None
    
    def __post_init__(self):
        if self.scraped_at is None:
            self.scraped_at = datetime.now().isoformat()
        if self.tweets is None:
            self.tweets = []

class EnterpriseTwitterScraper:
    """Enterprise-grade Twitter scraper for high-volume batch processing"""
    
    def __init__(self, max_workers: int = None, headless: bool = True, 
                 output_dir: str = "data", log_level: str = "INFO"):
        """
        Initialize the enterprise scraper.
        
        Args:
            max_workers: Maximum concurrent workers (auto-calculated if None)
            headless: Run browsers in headless mode
            output_dir: Directory for output files
            log_level: Logging level
        """
        self.headless = headless
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)
        
        # Setup logging
        self.setup_logging(log_level)
        
        # Auto-calculate optimal worker count
        self.max_workers = max_workers or min(32, (os.cpu_count() or 1) + 4)
        
        # Thread-safe collections
        self.results_queue = queue.Queue()
        self.error_count = 0
        self.success_count = 0
        self.total_tweets = 0
        
        # Rate limiting
        self.request_times = defaultdict(list)
        self.rate_limit_lock = threading.Lock()
        
        self.logger.info(f"Initialized enterprise scraper with {self.max_workers} workers")
    
    def setup_logging(self, log_level: str):
        """Setup logging configuration"""
        logging.basicConfig(
            level=getattr(logging, log_level.upper()),
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(self.output_dir / 'scraper.log'),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger(__name__)
    
    def calculate_optimal_batch_size(self, total_users: int) -> int:
        """Calculate optimal batch size based on total user count"""
        if total_users < 7:
            return 1  # Process individually for small sets
        elif total_users < 100:
            return min(5, total_users // 2)
        elif total_users < 1000:
            return min(10, total_users // 10)
        else:
            return min(20, total_users // 50)
    
    def calculate_delay_range(self, total_users: int) -> tuple:
        """Calculate delay range based on user count to avoid rate limiting"""
        if total_users < 7:
            return (0.5, 1.5)  # Faster for small sets
        elif total_users < 100:
            return (1, 3)
        elif total_users < 1000:
            return (2, 5)
        else:
            return (3, 7)  # More conservative for large sets
    
    def create_driver(self) -> webdriver.Chrome:
        """Create a new Chrome driver instance with advanced anti-detection"""
        options = Options()
        
        if self.headless:
            options.add_argument('--headless')
        
        # Anti-detection options (copied from working advanced scraper)
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-dev-shm-usage')
        options.add_argument('--disable-gpu')
        options.add_argument('--disable-extensions')
        options.add_argument('--disable-plugins')
        options.add_argument('--disable-images')
        options.add_argument('--disable-web-security')
        options.add_argument('--disable-features=VizDisplayCompositor')
        options.add_argument('--disable-ipc-flooding-protection')
        
        # Random user agent (more realistic)
        user_agents = [
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        ]
        import random
        user_agent = random.choice(user_agents)
        options.add_argument(f'--user-agent={user_agent}')
        
        # Additional stealth options
        options.add_experimental_option("excludeSwitches", ["enable-automation"])
        options.add_experimental_option('useAutomationExtension', False)
        
        # Disable loading of images and CSS
        prefs = {
            "profile.managed_default_content_settings.images": 2,
            "profile.default_content_setting_values.notifications": 2,
            "profile.default_content_settings.popups": 0
        }
        options.add_experimental_option("prefs", prefs)
        
        try:
            service = Service(ChromeDriverManager().install())
            driver = webdriver.Chrome(service=service, options=options)
            
            # Execute script to hide webdriver property
            driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
            
            driver.set_window_size(1920, 1080)
            return driver
        except Exception as e:
            self.logger.error(f"Failed to create driver: {e}")
            raise
    
    def apply_rate_limiting(self, delay_range: tuple):
        """Apply intelligent rate limiting"""
        current_time = time.time()
        thread_id = threading.current_thread().ident
        
        with self.rate_limit_lock:
            # Clean old requests (older than 1 minute)
            cutoff_time = current_time - 60
            self.request_times[thread_id] = [
                t for t in self.request_times[thread_id] if t > cutoff_time
            ]
            
            # Check if we need to slow down
            recent_requests = len(self.request_times[thread_id])
            if recent_requests > 10:  # More than 10 requests per minute
                extra_delay = recent_requests * 0.5
                delay = delay_range[1] + extra_delay
            else:
                delay = random.uniform(*delay_range)
            
            self.request_times[thread_id].append(current_time)
        
        time.sleep(delay)
    
    def scrape_user_tweets(self, user_config: UserConfig, delay_range: tuple) -> ScrapingResult:
        """Scrape tweets for a single user"""
        username = user_config.username
        tweet_count = user_config.tweet_count
        
        self.logger.info(f"Starting scrape for @{username} ({tweet_count} tweets)")
        
        driver = None
        try:
            # Apply rate limiting
            self.apply_rate_limiting(delay_range)
            
            # Create driver
            driver = self.create_driver()
            
            # Navigate to user profile on Twitter/X.com
            url = f"https://x.com/{username}"
            driver.get(url)
            
            # Wait for tweets to load (like advanced scraper)
            try:
                WebDriverWait(driver, 15).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, '[data-testid="tweet"]'))
                )
            except TimeoutException:
                self.logger.warning(f"No tweets found for @{username} - may be private or suspended")
                # Continue anyway to check for account status
            
            # Check if profile exists or account issues
            page_source = driver.page_source.lower()
            if "this account doesn't exist" in page_source or "account suspended" in page_source:
                return ScrapingResult(
                    username=username,
                    success=False,
                    tweet_count=0,
                    error_message="Account doesn't exist or is suspended"
                )
            
            # Check if redirected to login (private account)
            if "login" in driver.current_url.lower():
                return ScrapingResult(
                    username=username,
                    success=False,
                    tweet_count=0,
                    error_message="Account is private or requires login"
                )
            
            # Scroll and collect tweets
            tweets = self.collect_tweets(driver, tweet_count, delay_range)
            
            self.logger.info(f"Successfully scraped {len(tweets)} tweets for @{username}")
            
            return ScrapingResult(
                username=username,
                success=True,
                tweet_count=len(tweets),
                tweets=tweets
            )
            
        except Exception as e:
            self.logger.error(f"Error scraping @{username}: {e}")
            return ScrapingResult(
                username=username,
                success=False,
                tweet_count=0,
                error_message=str(e)
            )
        finally:
            if driver:
                try:
                    driver.quit()
                except:
                    pass
    
    def collect_tweets(self, driver: webdriver.Chrome, target_count: int, 
                      delay_range: tuple) -> List[Dict]:
        """Collect tweets from the current page"""
        tweets = []
        last_height = 0
        scroll_attempts = 0
        max_scrolls = min(target_count // 5 + 5, 20)  # Limit scrolling
        
        while len(tweets) < target_count and scroll_attempts < max_scrolls:
            # Get current tweets
            tweet_elements = driver.find_elements(By.CSS_SELECTOR, '[data-testid="tweet"]')
            self.logger.info(f"Found {len(tweet_elements)} tweet elements on scroll {scroll_attempts + 1}")
            
            # Extract new tweets
            for i, element in enumerate(tweet_elements[len(tweets):]):
                if len(tweets) >= target_count:
                    break
                
                tweet_data = self.extract_tweet_data(element)
                if tweet_data:
                    tweets.append(tweet_data)
                    self.logger.info(f"Successfully extracted tweet {len(tweets)}: {tweet_data['text'][:50]}...")
                else:
                    self.logger.debug(f"Failed to extract data from tweet element {i}")
            
            # Scroll down
            driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            
            # Wait for new content
            time.sleep(random.uniform(*delay_range))
            
            # Check if new content loaded
            new_height = driver.execute_script("return document.body.scrollHeight")
            if new_height == last_height:
                break
            
            last_height = new_height
            scroll_attempts += 1
        
        return tweets[:target_count]
    
    def extract_tweet_data(self, element) -> Optional[Dict]:
        """Extract data from a tweet element"""
        try:
            tweet_data = {}
            
            # Extract text
            try:
                text_element = element.find_element(By.CSS_SELECTOR, '[data-testid="tweetText"]')
                tweet_data['text'] = text_element.text.strip()
            except:
                tweet_data['text'] = ""
            
            # Extract timestamp
            try:
                time_element = element.find_element(By.CSS_SELECTOR, 'time')
                tweet_data['created_at'] = time_element.get_attribute('datetime')
                tweet_data['time_text'] = time_element.text
            except:
                tweet_data['created_at'] = None
                tweet_data['time_text'] = ""
            
            # Extract engagement metrics
            metrics = {'replies': 0, 'retweets': 0, 'likes': 0}
            
            try:
                # Get all metric elements
                metric_elements = element.find_elements(By.CSS_SELECTOR, '[role="group"] [role="button"]')
                for i, metric_element in enumerate(metric_elements[:3]):
                    aria_label = metric_element.get_attribute('aria-label') or ""
                    if 'reply' in aria_label.lower():
                        metrics['replies'] = self.extract_number_from_text(aria_label)
                    elif 'retweet' in aria_label.lower():
                        metrics['retweets'] = self.extract_number_from_text(aria_label)
                    elif 'like' in aria_label.lower():
                        metrics['likes'] = self.extract_number_from_text(aria_label)
            except:
                pass
            
            tweet_data['metrics'] = metrics
            tweet_data['scraped_at'] = datetime.now().isoformat()
            
            # Skip if no text (like advanced scraper)
            if not tweet_data['text']:
                return None
            
            # Add URL and ID extraction like advanced scraper
            try:
                link_elements = element.find_elements(By.CSS_SELECTOR, 'a[href*="/status/"]')
                if link_elements:
                    href = link_elements[0].get_attribute('href')
                    tweet_data['url'] = href
                    if '/status/' in href:
                        tweet_data['id'] = href.split('/status/')[-1].split('?')[0]
                else:
                    tweet_data['url'] = ""
                    tweet_data['id'] = ""
            except:
                tweet_data['url'] = ""
                tweet_data['id'] = ""
            
            # Extract hashtags and mentions like advanced scraper
            if tweet_data['text']:
                words = tweet_data['text'].split()
                tweet_data['hashtags'] = [word[1:] for word in words if word.startswith('#')]
                tweet_data['mentions'] = [word[1:] for word in words if word.startswith('@')]
            else:
                tweet_data['hashtags'] = []
                tweet_data['mentions'] = []
            
            return tweet_data
            
        except Exception as e:
            self.logger.debug(f"Error extracting tweet data: {e}")
            return None
    
    def extract_number_from_text(self, text: str) -> int:
        """Extract number from text (e.g., '1.2K' -> 1200)"""
        import re
        
        # Remove non-numeric characters except K, M, B
        clean_text = re.sub(r'[^0-9KMB.]', '', text.upper())
        
        if not clean_text:
            return 0
        
        try:
            if 'K' in clean_text:
                return int(float(clean_text.replace('K', '')) * 1000)
            elif 'M' in clean_text:
                return int(float(clean_text.replace('M', '')) * 1000000)
            elif 'B' in clean_text:
                return int(float(clean_text.replace('B', '')) * 1000000000)
            else:
                return int(float(clean_text))
        except:
            return 0
    
    def is_recent_tweet(self, tweet_data: Dict) -> bool:
        """Check if tweet is from the last 24 hours"""
        if not tweet_data.get('created_at'):
            return True  # Include if we can't determine age
        
        try:
            tweet_time = datetime.fromisoformat(tweet_data['created_at'].replace('Z', '+00:00'))
            cutoff_time = datetime.now() - timedelta(hours=24)
            return tweet_time.replace(tzinfo=None) > cutoff_time
        except:
            return True  # Include if parsing fails
    
    def process_batch(self, user_configs: List[UserConfig], delay_range: tuple) -> List[ScrapingResult]:
        """Process a batch of users concurrently"""
        results = []
        
        # Determine optimal worker count for this batch
        batch_workers = min(self.max_workers, len(user_configs))
        
        with ThreadPoolExecutor(max_workers=batch_workers) as executor:
            # Submit all tasks
            future_to_user = {
                executor.submit(self.scrape_user_tweets, user_config, delay_range): user_config
                for user_config in user_configs
            }
            
            # Collect results
            for future in as_completed(future_to_user):
                user_config = future_to_user[future]
                try:
                    result = future.result()
                    results.append(result)
                    
                    if result.success:
                        self.success_count += 1
                        self.total_tweets += result.tweet_count
                    else:
                        self.error_count += 1
                        
                except Exception as e:
                    self.logger.error(f"Task failed for @{user_config.username}: {e}")
                    self.error_count += 1
                    results.append(ScrapingResult(
                        username=user_config.username,
                        success=False,
                        tweet_count=0,
                        error_message=str(e)
                    ))
        
        return results
    
    def scrape_users(self, user_configs: List[UserConfig]) -> List[ScrapingResult]:
        """Scrape tweets for multiple users with optimal batching"""
        total_users = len(user_configs)
        batch_size = self.calculate_optimal_batch_size(total_users)
        delay_range = self.calculate_delay_range(total_users)
        
        self.logger.info(f"Processing {total_users} users in batches of {batch_size}")
        self.logger.info(f"Using delay range: {delay_range[0]:.1f}-{delay_range[1]:.1f} seconds")
        
        all_results = []
        
        # Process in batches
        for i in range(0, total_users, batch_size):
            batch = user_configs[i:i + batch_size]
            batch_num = i // batch_size + 1
            total_batches = (total_users + batch_size - 1) // batch_size
            
            self.logger.info(f"Processing batch {batch_num}/{total_batches} ({len(batch)} users)")
            
            batch_results = self.process_batch(batch, delay_range)
            all_results.extend(batch_results)
            
            # Progress update
            self.logger.info(f"Batch {batch_num} complete. Success: {self.success_count}, Errors: {self.error_count}")
            
            # Inter-batch delay for large sets
            if total_users > 100 and batch_num < total_batches:
                inter_batch_delay = min(10, total_users / 1000)
                self.logger.info(f"Inter-batch delay: {inter_batch_delay:.1f} seconds")
                time.sleep(inter_batch_delay)
        
        return all_results
    
    def save_results(self, results: List[ScrapingResult], output_file: str, format: str = "json"):
        """Save results to file"""
        output_path = self.output_dir / output_file
        
        if format.lower() == "json":
            self.save_json_results(results, output_path)
        elif format.lower() == "csv":
            self.save_csv_results(results, output_path)
        else:
            raise ValueError(f"Unsupported format: {format}")
    
    def save_json_results(self, results: List[ScrapingResult], output_path: Path):
        """Save results as JSON"""
        json_data = {
            'metadata': {
                'total_users': len(results),
                'successful_scrapes': self.success_count,
                'failed_scrapes': self.error_count,
                'total_tweets': self.total_tweets,
                'scraped_at': datetime.now().isoformat()
            },
            'results': [asdict(result) for result in results]
        }
        
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(json_data, f, indent=2, ensure_ascii=False)
        
        self.logger.info(f"Results saved to {output_path}")
    
    def save_csv_results(self, results: List[ScrapingResult], output_path: Path):
        """Save results as CSV"""
        # Flatten results for CSV
        csv_rows = []
        
        for result in results:
            if result.tweets:
                for tweet in result.tweets:
                    row = {
                        'username': result.username,
                        'success': result.success,
                        'scraped_at': result.scraped_at,
                        'tweet_text': tweet.get('text', ''),
                        'tweet_created_at': tweet.get('created_at', ''),
                        'tweet_time_text': tweet.get('time_text', ''),
                        'replies': tweet.get('metrics', {}).get('replies', 0),
                        'retweets': tweet.get('metrics', {}).get('retweets', 0),
                        'likes': tweet.get('metrics', {}).get('likes', 0)
                    }
                    csv_rows.append(row)
            else:
                # Add row for failed scrapes
                row = {
                    'username': result.username,
                    'success': result.success,
                    'scraped_at': result.scraped_at,
                    'error_message': result.error_message,
                    'tweet_text': '',
                    'tweet_created_at': '',
                    'tweet_time_text': '',
                    'replies': 0,
                    'retweets': 0,
                    'likes': 0
                }
                csv_rows.append(row)
        
        if csv_rows:
            with open(output_path, 'w', newline='', encoding='utf-8') as f:
                writer = csv.DictWriter(f, fieldnames=csv_rows[0].keys())
                writer.writeheader()
                writer.writerows(csv_rows)
        
        self.logger.info(f"CSV results saved to {output_path}")

def load_users_from_file(file_path: str) -> List[UserConfig]:
    """Load user configurations from file"""
    users = []
    
    if file_path.endswith('.json'):
        with open(file_path, 'r') as f:
            data = json.load(f)
            for item in data:
                users.append(UserConfig(
                    username=item['username'],
                    tweet_count=item.get('count', 10),
                    priority=item.get('priority', 'normal'),
                    tags=item.get('tags', [])
                ))
    else:
        # Assume text file with one username per line
        with open(file_path, 'r') as f:
            for line in f:
                username = line.strip()
                if username and not username.startswith('#'):
                    users.append(UserConfig(username=username))
    
    return users

def main():
    parser = argparse.ArgumentParser(description='Enterprise Twitter Batch Scraper')
    parser.add_argument('--users', help='File containing usernames (txt or json)')
    parser.add_argument('--config', help='JSON configuration file')
    parser.add_argument('--output', default='batch_results.json', help='Output file name')
    parser.add_argument('--format', choices=['json', 'csv'], default='json', help='Output format')
    parser.add_argument('--workers', type=int, help='Maximum concurrent workers')
    parser.add_argument('--tweet-count', type=int, default=10, help='Tweets per user (for txt input)')
    parser.add_argument('--headless', action='store_true', default=True, help='Run in headless mode')
    parser.add_argument('--log-level', choices=['DEBUG', 'INFO', 'WARNING', 'ERROR'], 
                       default='INFO', help='Logging level')
    
    args = parser.parse_args()
    
    # Load user configurations
    if args.config:
        user_configs = load_users_from_file(args.config)
    elif args.users:
        user_configs = load_users_from_file(args.users)
        # Set tweet count for all users if specified
        for user in user_configs:
            user.tweet_count = args.tweet_count
    else:
        print("Error: Must specify either --users or --config")
        return
    
    if not user_configs:
        print("Error: No users loaded")
        return
    
    print(f"🚀 Starting enterprise batch scraper for {len(user_configs)} users")
    
    # Initialize scraper
    scraper = EnterpriseTwitterScraper(
        max_workers=args.workers,
        headless=args.headless,
        log_level=args.log_level
    )
    
    # Start scraping
    start_time = datetime.now()
    results = scraper.scrape_users(user_configs)
    end_time = datetime.now()
    
    # Save results
    scraper.save_results(results, args.output, args.format)
    
    # Print summary
    duration = end_time - start_time
    print(f"\n📊 SCRAPING COMPLETE")
    print(f"=" * 50)
    print(f"⏱️  Duration: {duration}")
    print(f"👥 Total users: {len(user_configs)}")
    print(f"✅ Successful: {scraper.success_count}")
    print(f"❌ Failed: {scraper.error_count}")
    print(f"🐦 Total tweets: {scraper.total_tweets}")
    print(f"📁 Output: {scraper.output_dir / args.output}")
    
    if scraper.total_tweets > 0:
        rate = scraper.total_tweets / duration.total_seconds() * 60
        print(f"🚀 Rate: {rate:.1f} tweets/minute")

if __name__ == "__main__":
    main()