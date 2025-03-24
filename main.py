from renderer import render_video
from scraper import Scraper
import random
import json


scraper = Scraper()

subs = ["AmITheAsshole", "tifu", "TrueOffMyChest"]

used = []

with open('used.json','r') as file:
    used = json.load(file)


def get_post():
    posts = scraper.fetch_posts(subreddit_name=random.choice(subs),limit=10)
    for i in posts:
        if i._id not in used:
            used.append(i._id)
            with open("used.json",'w') as file:
                json.dump(used,file)
            return i

def make_vid():
    post = get_post()
    text = post.text
    render_video(text=text, output_prefix=post.title)

make_vid()
