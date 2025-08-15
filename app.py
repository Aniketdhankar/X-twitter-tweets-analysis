import os, csv, secrets, base64, hashlib, datetime as dt
from urllib.parse import urlencode
from requests.auth import HTTPBasicAuth
import requests
from flask import Flask, redirect, request, session, url_for, render_template, jsonify, Response
import tweepy
from transformers import pipeline
from pymongo import MongoClient, UpdateOne
from dotenv import load_dotenv

load_dotenv()
app = Flask(__name__)
app.secret_key = os.getenv("FLASK_SECRET", secrets.token_urlsafe(16))

# Twitter config
CLIENT_ID = os.getenv("TW_CLIENT_ID")
CLIENT_SECRET = os.getenv("TW_CLIENT_SECRET")
REDIRECT_URI = os.getenv("TW_REDIRECT_URI", "http://127.0.0.1:5000/callback")
AUTH_URL = "https://twitter.com/i/oauth2/authorize"
TOKEN_URL = "https://api.twitter.com/2/oauth2/token"

# MongoDB
MONGO_URI = os.getenv("MONGO_URI", "mongodb://localhost:27017")
mongo = MongoClient(MONGO_URI)
db = mongo["twitter_analysis"]
tweets_col = db["tweets"]

# Ensure useful indexes
tweets_col.create_index([("timestamp", -1)])
tweets_col.create_index([("tweetId", 1)], unique=True)
tweets_col.create_index([("sentiment", 1)])
tweets_col.create_index([("topic", 1)])

# Sentiment model
sentiment_analyzer = pipeline("sentiment-analysis")  # default model (POSITIVE/NEGATIVE)

def generate_code_verifier():
    return secrets.token_urlsafe(64)

def generate_code_challenge(code_verifier):
    sha256 = hashlib.sha256(code_verifier.encode()).digest()
    return base64.urlsafe_b64encode(sha256).decode().rstrip("=")

def normalize_label(label):
    label = label.lower()
    if "pos" in label: return "positive"
    if "neg" in label: return "negative"
    if "neutral" in label: return "neutral"
    return "neutral"

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/authorize", methods=["POST"])
def authorize():
    topic = request.form.get("topic","").strip()
    tweet_count = int(request.form.get("tweet_count", 50))
    if not topic:
        return "Topic required", 400
    session["topic"] = topic
    session["tweet_count"] = min(max(tweet_count,10),100)
    code_verifier = generate_code_verifier()
    session["code_verifier"] = code_verifier
    code_challenge = generate_code_challenge(code_verifier)
    params = {
        "response_type": "code",
        "client_id": CLIENT_ID,
        "redirect_uri": REDIRECT_URI,
        "scope": "tweet.read users.read offline.access",
        "state": secrets.token_urlsafe(16),
        "code_challenge": code_challenge,
        "code_challenge_method": "S256"
    }
    return redirect(f"{AUTH_URL}?{urlencode(params)}")

@app.route("/callback")
def callback():
    auth_code = request.args.get("code")
    if not auth_code:
        return "Missing code", 400
    code_verifier = session.get("code_verifier")
    token_data = {
        "grant_type": "authorization_code",
        "code": auth_code,
        "redirect_uri": REDIRECT_URI,
        "client_id": CLIENT_ID,
        "code_verifier": code_verifier
    }
    resp = requests.post(TOKEN_URL, data=token_data, auth=HTTPBasicAuth(CLIENT_ID, CLIENT_SECRET))
    if resp.status_code != 200:
        return f"Token exchange failed: {resp.status_code} {resp.text}", 400
    data = resp.json()
    session["access_token"] = data["access_token"]
    return redirect(url_for("fetch_tweets"))

@app.route("/fetch_tweets")
def fetch_tweets():
    topic = session.get("topic")
    tweet_count = session.get("tweet_count", 50)
    access_token = session.get("access_token")
    if not (topic and access_token):
        return redirect(url_for("index"))
    client = tweepy.Client(bearer_token=access_token)
    tweets = client.search_recent_tweets(query=f"{topic} -is:retweet lang:en", max_results=min(int(tweet_count),100),
                                        tweet_fields=["created_at","text","author_id","lang"])
    ops = []
    now = dt.datetime.utcnow()
    if tweets.data:
        for t in tweets.data:
            analysis = sentiment_analyzer(t.text)[0]
            label = normalize_label(analysis["label"])
            doc = {
                "tweetId": int(t.id),
                "userId": str(t.author_id) if t.author_id else None,
                "timestamp": t.created_at,
                "text": t.text,
                "sentiment": label,
                "topic": topic,
                "lang": t.lang,
                "ingestedAt": now
            }
            ops.append(UpdateOne({"tweetId": int(t.id)}, {"$setOnInsert": doc}, upsert=True))
    if ops:
        tweets_col.bulk_write(ops, ordered=False)
    # create CSV for convenience (optional)
    csv_path = os.path.join(os.getcwd(), "sentiment_analysis_results.csv")
    with open(csv_path, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["sentiment", "tweet"])
        cursor = tweets_col.find({"topic": topic}, {"_id":0,"sentiment":1,"text":1})
        for r in cursor:
            w.writerow([r["sentiment"], r["text"]])
    return redirect(url_for("results"))

@app.route("/results")
def results():
    return render_template("result.html")

@app.route("/api/sentiment_counts")
def api_sentiment_counts():
    topic = session.get("topic")
    match = {"topic": topic} if topic else {}
    pipeline = [{"$match": match}, {"$group": {"_id":"$sentiment","count":{"$sum":1}}}]
    counts = {d["_id"]:d["count"] for d in tweets_col.aggregate(pipeline)}
    for k in ("positive","negative","neutral"):
        counts.setdefault(k,0)
    return jsonify(counts)

@app.route("/api/tweets")
def api_tweets():
    topic = session.get("topic")
    sentiment = request.args.get("sentiment")
    page = max(int(request.args.get("page",1)),1)
    page_size = min(max(int(request.args.get("page_size",20)),1),100)
    q = {"topic": topic} if topic else {}
    if sentiment in ("positive","negative","neutral"):
        q["sentiment"] = sentiment
    cursor = (tweets_col.find(q, {"_id":0,"tweetId":1,"sentiment":1,"text":1,"timestamp":1})
              .sort("timestamp",-1).skip((page-1)*page_size).limit(page_size))
    items = list(cursor)
    return jsonify({"items": items, "page": page, "page_size": page_size})

@app.route("/export")
def export_csv():
    topic = session.get("topic")
    q = {"topic": topic} if topic else {}
    cursor = tweets_col.find(q, {"_id":0})
    def gen():
        first = True
        for doc in cursor:
            if first:
                headers = list(doc.keys())
                yield ",".join(headers) + "\n"
                first = False
            row = [str(doc.get(h,"")).replace("\n"," ").replace("\r"," ") for h in headers]
            yield ",".join('"' + v.replace('"','""') + '"' for v in row) + "\n"
    filename = f"tweets_{topic.replace(' ', '_') if topic else 'all'}.csv"
    return Response(gen(), mimetype="text/csv",
                    headers={"Content-Disposition": f"attachment; filename={filename}"})

if __name__ == "__main__":
    app.run(debug=True)
