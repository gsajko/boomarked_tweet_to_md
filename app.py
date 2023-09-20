# %%
from bs4 import BeautifulSoup
import os
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
import chromedriver_autoinstaller


# %%
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
    nitter_url = url.replace("twitter.com", "nitter.net")
    browser.get(nitter_url)
    browser.implicitly_wait(3)
    try:
        while True:
            element = browser.find_element(By.XPATH, "//a[@class='more-replies-text']")
            browser.execute_script("window.scrollTo(0, 0);")
            element.click()
            browser.implicitly_wait(2)
    except Exception as e:
        pass

    else:
        pass
    html_content = browser.page_source
    return html_content


# %%
def generate_markdown(html_content, output_folder):
    # Parsing the HTML content using BeautifulSoup
    soup = BeautifulSoup(html_content, "html.parser")

    # Placeholder for the entire markdown content
    entire_markdown_content = ""

    # Extracting all timeline-items (tweets) in the thread
    timeline_items = soup.find_all("div", {"class": "timeline-item"})

    # If no timeline items are found, return empty content
    if not timeline_items:
        return "No tweets found in the provided HTML content.", None

    # Extracting the main tweet's URL from the first tweet's href attribute
    first_tweet_link = timeline_items[0].find("span", {"class": "tweet-date"}).find("a")
    main_tweet_url = (
        f"https://twitter.com{first_tweet_link['href']}"
        if first_tweet_link and "href" in first_tweet_link.attrs
        else "URL not found"
    )

    # Extracting main tweet stats
    main_tweet_stats = soup.select_one("div.tweet-stats")
    if main_tweet_stats:
        main_likes = int(
            main_tweet_stats.find("span", class_="icon-heart").parent.text.strip()
            or "0"
        )
        main_retweets = int(
            main_tweet_stats.find("span", class_="icon-retweet").parent.text.strip()
            or "0"
        )
        main_replies = int(
            main_tweet_stats.find("span", class_="icon-comment").parent.text.strip()
            or "0"
        )
    else:
        main_likes = main_retweets = main_replies = 0

    quoted_hyperlink = None  # Placeholder for the quoted tweet hyperlink
    for index, timeline_item in enumerate(timeline_items):
        # Extracting Author and Handle
        author = timeline_item.find("a", {"class": "fullname"}).text.strip()
        handle = timeline_item.find("a", {"class": "username"}).text.strip()
        if index > 0:
            if author_handle == handle:
                pass
            else:
                break
        # Extracting Tweet Date
        tweet_date = (
            timeline_item.find("span", {"class": "tweet-date"})
            .a["title"]
            .split("·")[0]
            .strip()
        )

        # Extracting Content
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
            elif hyperlink_text.split("/")[1] == "status":
                hyperlink_a.replace_with(
                    f"[{hyperlink_text}](https://twitter.com/{hyperlink_text[1:]}/)"
                )
            else:
                hyperlink_a.replace_with(f"[{hyperlink_text}]({hyperlink})")

        content = content_div.text.strip()

        # Generating the markdown content for the main tweet's frontmatter
        if index == 0:
            author_handle = handle
            entire_markdown_content += f"""
---
author: "{author}"
handle: "{handle}"
source: "{main_tweet_url}"
date: "{tweet_date}"
likes: {main_likes}
retweets: {main_retweets}
replies: {main_replies}
---
"""

        # Generating the markdown content for the current tweet
        markdown_content = f"""
{author} ([{handle}](https://twitter.com/{handle[1:]}/)) - {tweet_date}

{content}
"""
        # Appending the markdown content of the current tweet to the entire content
        entire_markdown_content += markdown_content
        # Saving the markdown content to a .md file
        tw_id = main_tweet_url.split("/")[5]
        filename = f"{handle[1:]} - {tw_id}.md"

    # At the end of the content, append the ![[userhandle -tweetid]] representation if a quoted tweet link was found
    quoted_hyperlink = soup.find("a", {"class": "quote-link"})

    if quoted_hyperlink:
        quoted_hyperlink = quoted_hyperlink["href"]
        tweet_id = quoted_hyperlink.split("/")[3].split("#")[0]
        user_handle = quoted_hyperlink.split("/")[1]
        quoted_hyperlink = f"https://twitter.com/{user_handle}/status/{tweet_id}"
        entire_markdown_content += f"\n\n![[{user_handle} - {tweet_id}]]"

    # Finally, add the tweet link at the end
    entire_markdown_content += f"\n\n[Tweet link]({main_tweet_url})"


    file_path = f"{output_folder}/{filename}"
    with open(file_path, 'w') as file:
        file.write(entire_markdown_content)
        print(f"saved {filename}")

    return entire_markdown_content, quoted_hyperlink


# %%

# %%
def process_and_save_tweets(tweets_links):
    """
    Processes a list of tweet links, converts each to markdown, and saves to separate files.
    If a tweet contains a quoted tweet, it is added to the list to be processed.
    
    Args:
    - tweets_links (list): List of tweet links.
    
    Returns:
    - str: Message indicating the completion and location of saved files.
    """
    # Directory to save the markdown files
    output_directory = "data/tweets_output/"
    
    # Ensure the output directory exists
    if not os.path.exists(output_directory):
        os.makedirs(output_directory)

    # Placeholder for additional tweets (quoted tweets) to process
    additional_tweets = []

    # Set to keep track of processed tweets to avoid duplicates
    processed_tweets = set()

    # Filtering out links that point to specific media


    # Process each tweet link
    for tweet_link in tweets_links:
        if tweet_link in processed_tweets:
            continue  # Skip processing if this tweet link has already been processed
        if tweet_link.split("/")[-2] == "photo":
            continue # Skip processing photo links
        print(f"processing {tweet_link}")
        tweet_html = getting_source_code(tweet_link)
        markdown_content, quoted_tweet_link = generate_markdown(tweet_html, output_directory)
        
        # Add the tweet link to the processed tweets set
        processed_tweets.add(tweet_link)
        print("done❗️")
        # If a quoted tweet is present, add its link to the list to be processed
        if quoted_tweet_link:
            additional_tweets.append(quoted_tweet_link)

    # If there are additional tweets (quoted tweets), process them
    if additional_tweets:
        process_and_save_tweets(additional_tweets)

    return f"Markdown files saved to {output_directory}"

# The function is now ready for you to execute on your end.


# The function is now ready for you to execute on your end.
# Read the list of bookmarked tweet URLs
# %%
with open("all_bookmarks_2023-09-20_19-48-27.txt", "r") as file:
    tweet_urls = file.readlines()
process_and_save_tweets(tweet_urls)

# %%
# url = "https://twitter.com/shakoistsLog/status/1703261285046231362" #shako
# url = "https://twitter.com/_akhaliq/status/1702506479650046369"
url = "https://twitter.com/eugeneyan/status/1703514020031185195"
html_code = getting_source_code(url)
output_directory = "data"
markdown_content, quoted_tweet_link = generate_markdown(html_code, output_directory)
print(markdown_content)
# %%
# TODO
# get user handle and tweet ID from canonical ...