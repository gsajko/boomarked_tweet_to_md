# %%
import os
import time
from datetime import datetime

import chromedriver_autoinstaller
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.common.exceptions import WebDriverException
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from tqdm import tqdm

NITTER_URL = "https://nitter.net"
# NITTER_URL = "https://nitter.unixfox.eu"
MAX_RETRIES = 3
SLEEP_INTERVAL = 15  # 15 seconds


def is_nitter_up():
    chromedriver_autoinstaller.install()
    try:
        with webdriver.Chrome() as driver:
            driver.get(NITTER_URL)
            return driver.current_url.rstrip("/") == NITTER_URL.rstrip("/")
    except WebDriverException:
        return False


# getting tweet html from nitter
def getting_source_code(url, output_folder):
    # Automatically download and install ChromeDriver
    chromedriver_autoinstaller.install()
    browser = webdriver.Chrome()
    # Navigate to the tweet's URL
    nitter = url.replace("https://twitter.com", NITTER_URL)
    browser.get(nitter)
    wait = WebDriverWait(browser, 10)
    wait.until(
        lambda browser: browser.execute_script("return document.readyState")
        == "complete"
    )

    try:
        while True:
            element = browser.find_element(
                By.XPATH,
                "//a[@class='more-replies-text'] and text()='earlier replies']",
            )
            browser.execute_script("window.scrollTo(0, 0);")
            element.click()
            browser.implicitly_wait(2)
    except Exception:
        pass
    html_content = browser.page_source
    soup = BeautifulSoup(html_content, "html.parser")
    canonical_link = soup.find("link", {"rel": "canonical"})["href"]
    main_tweet_id = canonical_link.split("/")[-1]

    # Extract all timeline items
    timeline_items = soup.find_all("div", {"class": "timeline-item"})

    image_urls = []

    # Iterate over each timeline item to check
    # if it's the main tweet and extract its images
    for item in timeline_items:
        tweet_date_element = item.find("span", {"class": "tweet-date"})
        if tweet_date_element and tweet_date_element.a:
            tweet_link = tweet_date_element.a["href"]
            tweet_id = tweet_link.split("/")[-1].split("#")[0]
            tweet_link = tweet_date_element.a["href"]
            tweet_id = tweet_link.split("/")[-1].split("#")[0]

            if tweet_id == main_tweet_id:
                attachments_div = item.find("div", {"class": "attachments"})
                if attachments_div:
                    image_links = attachments_div.find_all(
                        "div", {"class": "attachment image"}
                    )
                    for link_element in image_links:
                        image_urls.append(link_element.a["href"])

    attachment_dir = f"{output_folder}/tweet_attachments"
    if not os.path.exists(attachment_dir):
        os.makedirs(attachment_dir)
    for idx, image_url in enumerate(image_urls):
        full_url = (
            NITTER_URL + image_url
        )  # Assuming NITTER_URL is a variable with the base URL
        browser.get(full_url)
        browser.implicitly_wait(3)
        # Get the image element on the new page.
        # This assumes the image is the primary content of the navigated page.
        img_element = browser.find_element(By.TAG_NAME, "img")

        # Use screenshot_as_png to capture the image
        img_data = img_element.screenshot_as_png

        # Save the image to a file. Use appropriate naming conventions as needed.
        with open(f"{attachment_dir}/{main_tweet_id}_{idx}.png", "wb") as img_file:
            img_file.write(img_data)

    return html_content


def generate_markdown(html_content, output_folder, tweet_link):
    # Parse the HTML content
    soup = BeautifulSoup(html_content, "html.parser")

    # Extract the user handle and tweet ID from the canonical link
    og_link = tweet_link
    og_parts = og_link.split("/")
    user_handle = og_parts[-3]
    og_parts[-1]
    meta_tag = soup.find("meta", {"property": "og:title"})
    name = " ".join(meta_tag["content"].split(" ")[:-1]) if meta_tag else None
    tweet_id = og_link.split("/")[-1].split("#")[0]
    # Extract all timeline-items (tweets) in the thread
    timeline_items = soup.find_all("div", {"class": "timeline-item"})

    # Determine if it's a thread by checking multiple tweets by the same author
    first_tweet = timeline_items[0]
    clean_date = (
        first_tweet.find("span", {"class": "tweet-date"})
        .a["title"]
        .split("·")[0]
        .strip()
    )

    entire_markdown_content = f"""---
author: "{name}"
handle: "@{user_handle}"
source: "{og_link}"
date: "{clean_date}"
---
"""

    tweets_to_include = [first_tweet]
    for timeline_item in timeline_items[1:]:
        handle = timeline_item.find("a", {"class": "username"}).text.strip()
        if handle == "@" + user_handle:
            tweets_to_include.append(timeline_item)
        else:
            break

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

        # Extract all hyperlinks in the content
        for hyperlink_a in content_div.find_all("a", href=True):
            hyperlink = hyperlink_a["href"]
            hyperlink_text = hyperlink_a.text

            # Check if it's a Twitter handle and format accordingly
            if hyperlink_text.startswith("@"):
                hyperlink_a.replace_with(
                    f"[{hyperlink_text}](https://twitter.com/{hyperlink_text[1:]}/)"
                )
            elif "/status/" in hyperlink:
                hyperlink_a.replace_with(
                    f"[{hyperlink_text}](https://twitter.com/{hyperlink})"
                )
            else:
                hyperlink_a.replace_with(f"[{hyperlink_text}]({hyperlink})")
        content = content_div.text.strip()

        entire_markdown_content += f"""
{author} ([{handle}](https://twitter.com/{handle[1:]}/)) - {tweet_date}

{content}
"""
        # Process and download images
        attachments_div = timeline_item.find("div", {"class": "attachments"})
        if attachments_div:
            for index, a_tag in enumerate(attachments_div.find_all("a", href=True)):
                image_filename = f"{tweet_id}_{index}.png"
                # add img link
                entire_markdown_content += (
                    f"\n\n![[tweet_attachments/{image_filename}]]"
                )

    # Handle quoted tweet
    quoted_hyperlink = soup.find("a", {"class": "quote-link"})
    if quoted_hyperlink:
        quoted_hyperlink = quoted_hyperlink["href"]
        q_tweet_id = quoted_hyperlink.split("/")[3].split("#")[0]
        q_user_handle = quoted_hyperlink.split("/")[1]
        entire_markdown_content += f"\n\n![[{q_user_handle} - {q_tweet_id}]]"
        if not quoted_hyperlink.startswith("https://"):
            quoted_hyperlink = "https://twitter.com" + quoted_hyperlink

    # Finally, add the tweet link at the end
    entire_markdown_content += f"\n\n[Tweet link]({og_link})"

    # Save the markdown content to a .md file
    filename = f"{user_handle} - {tweet_id}.md"
    file_path = f"{output_folder}/{filename}"
    with open(file_path, "w") as file:
        file.write(entire_markdown_content)
        print(f"saved {filename}")

    return entire_markdown_content, quoted_hyperlink


# processing list of tweets
def process_and_save_tweets(tweets_links, output_dir):
    # Directory to save the markdown files
    output_directory = output_dir
    attachment_dir = f"{output_dir}/tweet_attachments"
    retry_count = 0

    while not is_nitter_up() and retry_count < MAX_RETRIES:
        print(
            f"{NITTER_URL} appears to be down. Retrying in {SLEEP_INTERVAL} seconds..."
        )
        time.sleep(SLEEP_INTERVAL)
        retry_count += 1

    if retry_count == MAX_RETRIES:
        print(f"{NITTER_URL} is still down after {MAX_RETRIES} retries. Exiting...")
        return

    # Ensure the output directory exists
    if not os.path.exists(output_directory):
        os.makedirs(output_directory)
    if not os.path.exists(attachment_dir):
        os.makedirs(attachment_dir)

    # Placeholder for additional tweets (quoted tweets) to process
    tweets_queue = list(tweets_links)  # Convert initial tweets to a list (queue)

    # Set to keep track of processed tweets to avoid duplicates
    processed_tweets = set()

    # Log file to save problematic tweets and their error messages
    # Process each tweet link
    error_log = []
    for tweet_link in tqdm(
        tweets_queue, desc="Processing tweets", unit="tweet"
    ):  # Wrap the loop with tqdm for a progress bar
        if tweet_link in processed_tweets:
            continue  # Skip processing if this tweet link has already been processed

        try:
            print(f"processing {tweet_link}")
            tweet_html = getting_source_code(tweet_link, output_directory)
            markdown_content, quoted_tweet_link = generate_markdown(
                tweet_html, output_directory, tweet_link
            )

            # Add the tweet link to the processed tweets set
            processed_tweets.add(tweet_link)
            print("done❗️")

            # If a quoted tweet is present, add its link to the queue to be processed
            if quoted_tweet_link:
                tweets_queue.insert(0, quoted_tweet_link)
        except Exception as e:
            error_log.append({"url": tweet_link, "error": str(e)})

    # Save the error log with the current date appended to its name
    log_filename = f"error_log_{datetime.now().strftime('%Y%m%d')}.txt"
    with open(log_filename, "w") as f:
        for entry in error_log:
            f.write(f"URL: {entry['url']} | Error: {entry['error']}\n")

    return f"Markdown files saved to {output_directory}"


# %%

# img_tweet = "https://twitter.com/GokuMohandas/status/1701960178965557284"
# # html_code = getting_source_code(img_tweet)
# process_and_save_tweets([img_tweet], "data/tweets_output/")

# %%
# processing bookmarks


# with open("all_bookmarks_2023-09-22_08-30-10.txt", "r") as file:
#     tweet_urls = []
#     for url in file.readlines():
#         url = url.strip()
#         if len(url.split("status")[1].split("/")) > 2:
#             continue
#         tweet_urls.append(url)

# process_and_save_tweets(tweet_urls, "data/tweets_output/")
# %%
with open("all_bookmarks_2023-09-22_08-30-10.txt", "r") as file:
    img_urls = set()
    for url in file.readlines():
        url = url.strip()
        if (
            len(url.split("status")[1].split("/")) > 2
            and url.split("status")[1].split("/")[-2] == "photo"
        ):
            img_urls.add(url.split("/photo")[0])
img_urls
process_and_save_tweets(img_urls, "data/tweets_output/")
# %%
urls = ["https://twitter.com/jeremyphoward/status/1642726620082606080"]
out_dir = "data/tweets_output/"
link = urls[0]
# process_and_save_tweets(urls, "data/tweets_output/")
html_content = getting_source_code(link, out_dir)
# %%
generate_markdown(html_content, out_dir, tweet_link=link)
# %%
# TODO
# save files using selenium with correct name and in correct folder
# selenium only uses visible html! I should extract data using soup,
#  then use selenium to scrape
# with multiple tweets it's get index wrong right now
# handle deleted tweets
