import requests
from bs4 import BeautifulSoup
from feedgen.feed import FeedGenerator
from datetime import datetime,timezone
import xml.etree.ElementTree as ET
import os
import re

rss_feed_path = 'feeds/all.xml'

def get_pub_date(video_id):
    if os.path.exists(rss_feed_path):
        try:
            tree = ET.parse(rss_feed_path)
            root = tree.getroot()

            # Iterate through all <item> elements to find the video by ID
            for item in root.findall(".//item"):
                guid = item.find("guid").text
                if guid and video_id in guid:  # Check if the video ID is in the GUID
                    pub_date = item.find("pubDate").text
                    return pub_date  # Return the found pubDate
            
        except Exception as e:
            print(f"Error parsing {rss_feed_path}: {e}")
    
    return str(datetime.now(tz=timezone.utc).replace(minute=0,second=0,microsecond=0))  # If not found or an error occurred, return Today

def slugify(title):
    return re.sub(r'\W+', '-', title.lower()).strip('-')

url = 'https://www.dropout.tv/new-releases'
html = requests.get(url).text
soup = BeautifulSoup(html, 'html.parser')

all_videos = []
video_elements = soup.select('.item-type-video')
video_elements.reverse()
for video in video_elements:
    try:
        # Get video ID
        id = video["data-item-id"]
        # https://www.dropout.tv/dimension-20-s-adventuring-party/season:20/videos/a-cheeseburger-intimidation-check


        link_tag = video.find('a', href=True)
        link = link_tag['href'].replace("new-releases/", "") if link_tag else None
        player_html = requests.get(link).text
        player_soup = BeautifulSoup(player_html, 'html.parser')
        tags = player_soup.select(".meta-data-info")[0].get_text(strip=True).split(",")
        series = tags[0].strip()
        title = player_soup.select_one('.video-title').get_text(strip=True)
        img = video.find("img")
        thumbnail = img['src'].split("?")[0] if img else ''
        duration = video.select_one('.duration-container').get_text(strip=True)
        description = player_soup.find(id="watch-info").p.get_text(strip=True)
        pubdate = get_pub_date(id)


        all_videos.append({
            "id": id,
            "pubdate": pubdate,
            "series": series,
            "title": title,
            "url": link,
            "thumbnail": thumbnail,
            "duration": duration,
            "description": description,
            "tags": tags
        })
    except Exception as e:
        print(f"Error parsing video: {e}")

# Group videos by series
from collections import defaultdict
videos_by_series = defaultdict(list)

all_fg = FeedGenerator()
all_fg.title("Dropout.tv - New Releases")
all_fg.link(href=f'https://www.dropout.tv/browse', rel='alternate')
all_fg.description(f'All releases from from Dropout.tv')

for video in all_videos:
    videos_by_series[video["series"]].append(video)

    fe = all_fg.add_entry()
    fe.title(f"{video['title']} - {video["series"]}")
    fe.link(href=video['url'])
    fe.description(f'<img src="{video["thumbnail"]}"/><br/><br/>{video["description"]}<br/><br/>Duration: {video["duration"]}<br/><br/>Tags: {", ".join(video["tags"])}')
    fe.guid(video['id'], permalink=True)
    fe.pubDate(video['pubdate'])
    # fe.id(video['id'])

all_fg.rss_file("feeds/all.xml")

# Generate one RSS feed per series
os.makedirs("feeds", exist_ok=True)
for series, videos in videos_by_series.items():
    fg = FeedGenerator()
    fg.title(series)
    fg.link(href=f'https://www.dropout.tv/{series.lower()}', rel='alternate')
    fg.description(f'Latest releases from {series} on Dropout.tv')

    for v in videos:
        fe = fg.add_entry()
        fe.title(f"{v['title']}")
        fe.link(href=v['url'])
        fe.description(f'<img src="{v["thumbnail"]}"/><br/><br/>{v["description"]}<br/><br/>Duration: {v["duration"]}<br/><br/>Tags: {", ".join(v["tags"])}')
        fe.guid(v['id'], permalink=True)
        fe.pubDate(v['pubdate'])
        # fe.id(video['id'])

    filename = f"feeds/feed-{slugify(series)}.xml"
    fg.rss_file(filename)

import json

feed_index_path = 'feeds.json'

# Load existing feeds.json if it exists
if os.path.exists(feed_index_path):
    with open(feed_index_path, 'r') as f:
        feed_index = json.load(f)
        print("Prior feed index found!\n========================")
        print(feed_index)
        print()
else:
    print("No prior feed index. Creating new one...")
    feed_index = {}

for series in videos_by_series:
    feed_filename = f'feeds/feed-{slugify(series)}.xml'
    feed_index[series] = feed_filename
    print(f"Adding {series}: {feed_filename}")

print("\nExporting feed index...\n========================\n",feed_index)

with open('feeds.json', 'w') as f:
    json.dump(feed_index, f, indent=2)