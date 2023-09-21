# %%
import os

import chromedriver_autoinstaller
import requests
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By

# NITTER_URL = "https://nitter.net"
NITTER_URL = "https://nitter.unixfox.eu"


from selenium.common.exceptions import WebDriverException


def is_nitter_up():
    chromedriver_autoinstaller.install()
    try:
        with webdriver.Chrome() as driver:
            driver.get(NITTER_URL)
            return driver.current_url.rstrip('/') == NITTER_URL.rstrip('/')
    except WebDriverException:
        return False



# getting tweet html from nitter
def getting_source_code(url):
    # Automatically download and install ChromeDriver
    chromedriver_autoinstaller.install()
    browser = webdriver.Chrome()
    # Navigate to the tweet's URL
    nitter = url.replace("https://twitter.com", NITTER_URL)
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

def generate_markdown(html_content, output_folder):
    # Parse the HTML content
    soup = BeautifulSoup(html_content, "html.parser")

    # Extract the user handle and tweet ID from the canonical link
    canonical_link = soup.find("link", {"rel": "canonical"})["href"]
    canonical_parts = canonical_link.split("/")
    user_handle = canonical_parts[-3]
    canonical_parts[-1]
    meta_tag = soup.find('meta', {'property': 'og:title'})
    name = ' '.join(meta_tag['content'].split(' ')[:-1]) if meta_tag else None
    # Extract all timeline-items (tweets) in the thread
    timeline_items = soup.find_all("div", {"class": "timeline-item"})

    # Determine if it's a thread by checking multiple tweets by the same author
    tweets_to_include = [timeline_items[0]]
    for timeline_item in timeline_items[1:]:
        handle = timeline_item.find("a", {"class": "username"}).text.strip()
        if handle == "@" + user_handle:
            tweets_to_include.append(timeline_item)
        else:
            break

    is_thread = len(tweets_to_include) > 1

    # If it's a thread, set the source to the top tweet's URL
    if is_thread:
        source = (
            tweets_to_include[0].find("span", {"class": "tweet-date"}).find("a")["href"]
        )
        source = f"https://twitter.com{source.split(NITTER_URL)[-1]}"
    else:
        source = canonical_link.replace(
            NITTER_URL, "twitter.com"
        )  # Correcting to use twitter instead of nitter

    clean_date = {
        tweets_to_include[0]
        .find("span", {"class": "tweet-date"})
        .a["title"]
        .split("·")[0]
        .strip()
    }
    entire_markdown_content = f"""
---
author: "{name}"
handle: "@{user_handle}"
source: "{source}"
date: "{clean_date}"
---
"""

    # Process all tweets in the thread
    for timeline_item in tweets_to_include:
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

        entire_markdown_content += f"""
{author} ([{handle}](https://twitter.com/{handle[1:]}/)) - {tweet_date}

{content}
"""

    # Handle quoted tweet
    quoted_hyperlink = soup.find("a", {"class": "quote-link"})
    if quoted_hyperlink:
        quoted_hyperlink = quoted_hyperlink["href"]
        q_tweet_id = quoted_hyperlink.split("/")[3].split("#")[0]
        q_user_handle = quoted_hyperlink.split("/")[1]
        entire_markdown_content += f"\n\n![[{q_user_handle} - {q_tweet_id}]]"

    # Finally, add the tweet link at the end
    entire_markdown_content += f"\n\n[Tweet link]({source})"

    # Save the markdown content to a .md file
    filename = f"{user_handle} - {source.split('/')[-1].split('#')[0]}.md"
    file_path = f"{output_folder}/{filename}"
    with open(file_path, "w") as file:
        file.write(entire_markdown_content)
        print(f"saved {filename}")

    return entire_markdown_content, quoted_hyperlink





# processing list of tweets
def process_and_save_tweets(tweets_links, output_dir):
    # Directory to save the markdown files
    output_directory = output_dir

    if not is_nitter_up():
        print(f"{NITTER_URL} is down. Exiting...")
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


%%
processing bookmarks
with open("all_bookmarks_2023-09-21_16-23-49.txt", "r") as file:
    tweet_urls = [url.strip() for url in file.readlines()]
process_and_save_tweets(tweet_urls, "data/tweets_output/")

# %%
# with webdriver.Chrome() as driver:
#             driver.get(NITTER_URL)
#             print(driver.current_url) 
#             print(NITTER_URL)
#             print(driver.current_url.rstrip('/') == NITTER_URL.rstrip('/'))
        
# %%
# with open("all_bookmarks_2023-09-21_16-23-49.txt", "r") as file:
#     tweet_urls = file.readlines()

# # %%
# with open("all_bookmarks_2023-09-21_16-23-49.txt", "r") as file:
#     tweet_urls = [url.strip() for url in file.readlines()]
# %%
url = "https://twitter.com/shakoistsLog/status/1703261285046231362"
html_code = getting_source_code(url)
# %%

markdown_content, quoted_tweet_link = generate_markdown(
            html_code, "data"
        )
# %%
