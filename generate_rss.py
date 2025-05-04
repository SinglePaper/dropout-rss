import requests
from bs4 import BeautifulSoup
from feedgen.feed import FeedGenerator
import os
import re

def slugify(title):
    return re.sub(r'\W+', '-', title.lower()).strip('-')

url = 'https://www.dropout.tv/new-releases'
html = requests.get(url).text
soup = BeautifulSoup(html, 'html.parser')

all_videos = []

for video in soup.select('.item-type-video'):
    try:
        id = video["data-item-id"]
        link_tag = video.find('a', href=True)
        link = link_tag['href'] if link_tag else None
        player_html = requests.get(link).text
        player_soup = BeautifulSoup(player_html, 'html.parser')
        tags = player_soup.select(".meta-data-info")[0].get_text(strip=True).split(",")
        series = tags[0].strip()
        title = player_soup.select_one('.video-title').get_text(strip=True)
        img = video.find("img")
        thumbnail = img['src'].split("?")[0] if img else ''
        duration = video.select_one('.duration-container').get_text(strip=True)
        description = player_soup.find(id="watch-info").p.get_text(strip=True)

        all_videos.append({
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
for video in all_videos:
    videos_by_series[video["series"]].append(video)

# Generate one RSS feed per series
os.makedirs("feeds", exist_ok=True)
for series, videos in videos_by_series.items():
    fg = FeedGenerator()
    fg.title(f'Dropout.tv - {series}')
    fg.link(href=f'https://www.dropout.tv/{series.lower()}', rel='alternate')
    fg.description(f'Latest releases from Dropout.tv: {series}')

    for v in videos:
        fe = fg.add_entry()
        fe.title(f"[{v['series']}] {v['title']}")
        fe.link(href=v['url'])
        fe.description(f'<img src="{v["thumbnail"]}"/><br/><br/>{v["description"]}<br/><br/>Duration: {v["duration"]}<br/><br/>Tags: {", ".join(v["tags"])}')
        fe.guid(v['url'])

    filename = f"feeds/feed-{slugify(series)}.xml"
    fg.rss_file(filename)

import json

feed_index_path = 'feeds.json'

# Load existing feeds.json if it exists
if os.path.exists(feed_index_path):
    with open(feed_index_path, 'r') as f:
        feed_index = json.load(f)
else:
    feed_index = {}
    
for series in videos_by_series:
    feed_filename = f'feeds/feed-{slugify(series)}.xml'
    feed_index[series] = feed_filename

with open('feeds.json', 'w') as f:
    json.dump(feed_index, f, indent=2)