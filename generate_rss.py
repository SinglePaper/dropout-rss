import requests
from bs4 import BeautifulSoup
from feedgen.feed import FeedGenerator

url = 'https://www.dropout.tv/new-releases'
html = requests.get(url).text
soup = BeautifulSoup(html, 'html.parser')

fg = FeedGenerator()
fg.title('Dropout.tv - New Releases')
fg.link(href='https://www.dropout.tv/new-releases', rel='alternate')
fg.description('Latest video releases from Dropout.tv')

# print(soup.select('.item-type-video'))
for video in soup.select('.item-type-video'):
    id = video["data-item-id"]
    link_tag = video.find('a', href=True)
    link = link_tag['href'] if link_tag else None
    player_html = requests.get(link).text
    player_soup = BeautifulSoup(player_html, 'html.parser')
    tags = player_soup.select(".meta-data-info")[0].get_text(strip=True).split(",")
    tags_string = ", ".join(tags)
    series = tags[0]
    title = player_soup.select_one('.video-title').get_text(strip=True)
    img = video.find("img")
    thumbnail = img['src'].split("?")[0] if img else ''
    duration = video.select_one('.duration-container').get_text(strip=True)
    description = player_soup.find(id="watch-info").p.get_text(strip=True)
    print(f"{series}: {title}")

    fe = fg.add_entry()
    fe.title(f"[{series}] {title}")
    fe.link(href=link)
    fe.description(f'<img src="{thumbnail}"/><br/><br/>{description}<br/><br/>Duration: {duration}<br/><br/>Tags: {tags_string}')
    fe.guid(link)

fg.rss_file('dropout_feed.xml')
