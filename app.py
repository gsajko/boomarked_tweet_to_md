# %%
from bs4 import BeautifulSoup
import os
from selenium import webdriver
from selenium.webdriver.common.by import By
import chromedriver_autoinstaller
# %%
def getting_source_code(url):
    # Automatically download and install ChromeDriver
    chromedriver_autoinstaller.install()
    # Set up the driver
    browser = webdriver.Chrome()
    # Navigate to the tweet's URL
    nitter_url = url.replace('twitter.com', 'nitter.net')
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
def generate_markdown(html_content):
    # Parsing the HTML content using BeautifulSoup
    soup = BeautifulSoup(html_content, 'html.parser')
    
    # Placeholder for the entire markdown content
    entire_markdown_content = ""
    
    # Extracting all timeline-items (tweets) in the thread
    timeline_items = soup.find_all("div", {"class": "timeline-item"})
    
    # If no timeline items are found, return empty content
    if not timeline_items:
        return "No tweets found in the provided HTML content.", None

    # Extracting the main tweet's URL from the first tweet's href attribute
    first_tweet_link = timeline_items[0].find("span", {"class": "tweet-date"}).find("a")
    main_tweet_url = first_tweet_link["href"] if first_tweet_link and "href" in first_tweet_link.attrs else "URL not found"
    
    # Extracting main tweet stats
    main_tweet_stats = soup.select_one("div.tweet-stats")
    if main_tweet_stats:
        main_likes = int(main_tweet_stats.find("span", class_="icon-heart").parent.text.strip() or "0")
        main_retweets = int(main_tweet_stats.find("span", class_="icon-retweet").parent.text.strip() or "0")
        main_replies = int(main_tweet_stats.find("span", class_="icon-comment").parent.text.strip() or "0")
    else:
        main_likes = main_retweets = main_replies = 0

    quoted_hyperlink = None  # Placeholder for the quoted tweet hyperlink
    for index, timeline_item in enumerate(timeline_items):
        # Extracting Author and Handle
        author = timeline_item.find("a", {"class": "fullname"}).text.strip()
        handle = timeline_item.find("a", {"class": "username"}).text.strip()

        # Extracting Tweet Date
        tweet_date = timeline_item.find("span", {"class": "tweet-date"}).a["title"].split('·')[0].strip()

        # Extracting Content
        content_div = timeline_item.find("div", {"class": "tweet-content"})
        
        # Extract all hyperlinks in the content
        for hyperlink_a in content_div.find_all("a", href=True):
            hyperlink = hyperlink_a["href"]
            hyperlink_text = hyperlink_a.text
            
            # Check if it's a Twitter handle and format accordingly
            if hyperlink_text.startswith('@'):
                hyperlink_a.replace_with(f"[{hyperlink_text}](https://twitter.com/{hyperlink_text[1:]}/)")            
            else:
                hyperlink_a.replace_with(f"[{hyperlink_text}]({hyperlink})")
        
        content = content_div.text.strip()

        # Extracting unique tweet ID from the href attribute of the tweet-link
        tweet_link = timeline_item.find("a", {"class": "tweet-link"})
        tweet_url = main_tweet_url
        if tweet_link and "href" in tweet_link.attrs:
            tweet_id = tweet_link["href"].split("/")[-1].split("#")[0]
            
            # Generating tweet URL based on the extracted ID
            tweet_url = f"https://twitter.com/{handle[1:]}/status/{tweet_id}"

        # Generating the markdown content for the main tweet's frontmatter
        if index == 0:
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

    # At the end of the content, append the ![[userhandle -tweetid]] representation if a quoted tweet link was found
    quoted_hyperlink = soup.find("a", {"class": "quote-link"})
    
    if quoted_hyperlink:
        quoted_hyperlink=quoted_hyperlink["href"]
        tweet_id = quoted_hyperlink.split("/")[3].split("#")[0]
        user_handle = quoted_hyperlink.split("/")[1]
        quoted_hyperlink= f"https://twitter.com/{user_handle}/status/{tweet_id}"
        entire_markdown_content += f"\n\n![[{user_handle} - {tweet_id}]]"

    # Finally, add the tweet link at the end
    entire_markdown_content += f"\n\n[Tweet link]({main_tweet_url})"

    return entire_markdown_content, quoted_hyperlink

# Generate markdown with quotes using the final fixed version of the function
# %%
# Read the list of bookmarked tweet URLs
with open("all_bookmarks_2023-09-16_19-40-21.txt", "r") as file:
    tweet_urls = file.readlines()
# Fetch details for the first tweet URL
url = tweet_urls[0].strip()
# url = "https://twitter.com/shakoistsLog/status/1703261285046231362"
html_content = getting_source_code(url)
# %%
md, quoted_tweet_link_final_fixed = generate_markdown(html_content)

print(md)



# %%
