# %%
import os

import chromedriver_autoinstaller
import requests
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By

NITTER_URL = "https://nitter.net"


def is_nitter_up():
    try:
        response = requests.get(NITTER_URL, timeout=10)
        return response.status_code == 200
    except (requests.ConnectionError, requests.Timeout):
        return False


# getting tweet html from nitter
def getting_source_code(url):
    # Automatically download and install ChromeDriver
    chromedriver_autoinstaller.install()
    # Set up the driver
    chrome_options = Options()
    # chrome_options.add_argument("--headless")
    # start browser minimized
    chrome_options.add_argument("window-position=-2000,0")
    browser = webdriver.Chrome(options=chrome_options)
    # Navigate to the tweet's URL
    nitter = url.replace("twitter.com", NITTER_URL)
    browser.get(nitter)
    browser.implicitly_wait(3)
    try:
        while True:
            element = browser.find_element(By.XPATH, "//a[@class='more-replies-text']")
            browser.execute_script("window.scrollTo(0, 0);")
            element.click()
            browser.implicitly_wait(2)
    except Exception:
        pass

    else:
        pass
    html_content = browser.page_source
    return html_content


# extracting data from html and converting to md
def extract_metadata(soup):
    """Extract metadata such as user handle, tweet ID, etc."""
    canonical_link = soup.find("link", {"rel": "canonical"})["href"]
    canonical_parts = canonical_link.split("/")
    user_handle = canonical_parts[-3]
    tweet_id = canonical_parts[-1]
    return user_handle, tweet_id


def process_tweet_content(timeline_item):
    """Process an individual tweet's content."""
    author = timeline_item.find("a", {"class": "fullname"}).text.strip()
    handle = timeline_item.find("a", {"class": "username"}).text.strip()
    tweet_date = (
        timeline_item.find("span", {"class": "tweet-date"})
        .a["title"]
        .split("·")[0]
        .strip()
    )
    content_div = timeline_item.find("div", {"class": "tweet-content"})
    content = content_div.text.strip()
    return f"""
{author} ([{handle}](https://twitter.com/{handle[1:]}/)) - {tweet_date}

{content}
"""


def handle_quoted_tweet(soup):
    """Handle the quoted tweet scenario."""
    quoted_hyperlink = soup.find("a", {"class": "quote-link"})
    if quoted_hyperlink:
        quoted_hyperlink = quoted_hyperlink["href"]
        q_tweet_id = quoted_hyperlink.split("/")[3].split("#")[0]
        q_user_handle = quoted_hyperlink.split("/")[1]
        return f"\n\n![[{q_user_handle} - {q_tweet_id}]]"
    return ""


def generate_markdown(html_content, output_folder):
    """Generate the markdown content for a given tweet's HTML content."""
    soup = BeautifulSoup(html_content, "html.parser")
    user_handle, tweet_id = extract_metadata(soup)
    timeline_items = soup.find_all("div", {"class": "timeline-item"})

    clean_date = {
        timeline_items[0]
        .find("span", {"class": "tweet-date"})
        .a["title"]
        .split("·")[0]
        .strip()
    }
    entire_markdown_content = f"""
---
author: "{user_handle}"
handle: "@{user_handle}"
source: "https://twitter.com/{user_handle}/status/{tweet_id}"
date: "{clean_date}"
---
"""

    # Process all tweets in the thread
    for timeline_item in timeline_items:
        entire_markdown_content += process_tweet_content(timeline_item)

    # Handle quoted tweet
    entire_markdown_content += handle_quoted_tweet(soup)

    # Finally, add the tweet link at the end
    entire_markdown_content += (
        f"\n\n[Tweet link](https://twitter.com/{user_handle}/status/{tweet_id})"
    )

    # Save the markdown content to a .md file
    filename = f"{user_handle} - {tweet_id}.md"
    file_path = f"{output_folder}/{filename}"
    with open(file_path, "w") as file:
        file.write(entire_markdown_content)
        print(f"saved {filename}")

    return entire_markdown_content


# processing list of tweets
def process_and_save_tweets(tweets_links, output_dir):
    # Directory to save the markdown files
    output_directory = output_dir

    if not is_nitter_up():
        print("Nitter.net is down. Exiting...")
        return

    # Ensure the output directory exists
    if not os.path.exists(output_directory):
        os.makedirs(output_directory)

    # Placeholder for additional tweets (quoted tweets) to process
    tweets_queue = list(tweets_links)  # Convert initial tweets to a list (queue)

    # Set to keep track of processed tweets to avoid duplicates
    processed_tweets = set()

    # Process each tweet link
    while tweets_queue:
        tweet_link = tweets_queue.pop(0)  # Get the first tweet from the queue

        if tweet_link in processed_tweets:
            continue  # Skip processing if this tweet link has already been processed

        if tweet_link.split("/")[-2] == "photo":
            continue  # Skip processing photo links

        print(f"processing {tweet_link}")
        tweet_html = getting_source_code(tweet_link)
        markdown_content, quoted_tweet_link = generate_markdown(
            tweet_html, output_directory
        )

        # Add the tweet link to the processed tweets set
        processed_tweets.add(tweet_link)
        print("done❗️")

        # If a quoted tweet is present, add its link to the queue to be processed
        if quoted_tweet_link:
            tweets_queue.append(quoted_tweet_link)

    return f"Markdown files saved to {output_directory}"


# %%
# processing bookmarks
with open("all_bookmarks_2023-09-21_16-23-49.txt", "r") as file:
    tweet_urls = file.readlines()
process_and_save_tweets(tweet_urls, "data/tweets_output/")

# %%
