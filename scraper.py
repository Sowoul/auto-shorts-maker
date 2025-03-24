import praw
from dataclasses import dataclass
from dotenv import load_dotenv
import os

load_dotenv()

@dataclass
class Item:
    _id: str
    title:str
    text: str
    author: str
    link: str
class Scraper:
    def __init__(self):
        self.reddit = praw.Reddit(
            client_id=os.environ.get("CLIENT_ID"),
            client_secret=os.environ.get("CLIENT_SECRET"),
            user_agent='python:shortspan:v1.0 (by u/eggplantenough)'
        )

    def fetch_posts(self, subreddit_name="AmITheAsshole", limit=5):
        subreddit = self.reddit.subreddit(subreddit_name)
        posts = []
        for post in subreddit.top(time_filter="day",limit=limit):
            if not post.stickied:
                posts.append(Item(
                    _id=post.id,
                    text=post.selftext,
                    author=post.author.name if post.author else "[Deleted]",
                    link=f"https://www.reddit.com{post.permalink}",
                    title=post.title
                ))
        return posts
