from flask import Flask, request, jsonify
import requests
from collections import defaultdict
from concurrent.futures import ThreadPoolExecutor

app = Flask(__name__)
BASE_URL = "http://20.244.56.144/evaluation-service"
CACHE = {"users": {}, "posts": defaultdict(list), "comments": defaultdict(list)}
HEADERS = {
    "Authorization": "Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJNYXBDbGFpbXMiOnsiZXhwIjoxNzQzNjAzMDMyLCJpYXQiOjE3NDM2MDI3MzIsImlzcyI6IkFmZm9yZG1lZCIsImp0aSI6IjkyYzZkY2UzLTIzMWYtNDBmYy04MjhkLTljMjhjNzhkY2NmYSIsInN1YiI6IjIyMDUyNjMwQGtpaXQuYWMuaW4ifSwiZW1haWwiOiIyMjA1MjYzMEBraWl0LmFjLmluIiwibmFtZSI6ImJvcm5payBkZWthdmlyYWoiLCJyb2xsTm8iOiIyMjA1MjYzMCIsImFjY2Vzc0NvZGUiOiJud3B3cloiLCJjbGllbnRJRCI6IjkyYzZkY2UzLTIzMWYtNDBmYy04MjhkLTljMjhjNzhkY2NmYSIsImNsaWVudFNlY3JldCI6Ik5RVFhKcnFuVnpocGFmTkYifQ.JNHYwqFuCkZ2tqc9Lj5UB3dit13iujuIC80nGexnnk4"
}
def fetch_users():
    response = requests.get(f"{BASE_URL}/users", headers=HEADERS)
    if response.status_code == 200:
        CACHE["users"] = response.json().get("users", {})
def fetch_posts(user_id):
    response = requests.get(f"{BASE_URL}/users/{user_id}/posts", headers=HEADERS)
    if response.status_code == 200:
        CACHE["posts"][user_id] = response.json().get("posts", [])
def fetch_comments(post_id):
    response = requests.get(f"{BASE_URL}/posts/{post_id}/comments", headers=HEADERS)
    if response.status_code == 200:
        CACHE["comments"][post_id] = response.json().get("comments", [])

@app.route("/users", methods=["GET"])
def top_users():
    user_post_counts = {user: len(CACHE["posts"].get(user, [])) for user in CACHE["users"]}
    top_users = sorted(user_post_counts.items(), key=lambda x: x[1], reverse=True)[:5]
    return jsonify({"top_users": [{"id": user, "name": CACHE["users"][str(user)], "posts": count} for user, count in top_users]})

@app.route("/posts", methods=["GET"])
def get_posts():
    post_type = request.args.get("type", "latest")
    all_posts = [post for posts in CACHE["posts"].values() for post in posts]
    if post_type == "popular":
        post_comment_counts = {post["id"]: len(CACHE["comments"].get(post["id"], [])) for post in all_posts}
        max_comments = max(post_comment_counts.values(), default=0)
        popular_posts = [post for post in all_posts if post_comment_counts.get(post["id"], 0) == max_comments]
        return jsonify({"popular_posts": popular_posts})
    
    elif post_type == "latest":
        latest_posts = sorted(all_posts, key=lambda x: x.get("id", 0), reverse=True)[:5]
        return jsonify({"latest_posts": latest_posts})
    return jsonify({"error": "Invalid type parameter"}), 400
if __name__ == "__main__":
    fetch_users()
    with ThreadPoolExecutor() as executor:
        for user_id in CACHE["users"]:
            executor.submit(fetch_posts, user_id)
            for post in CACHE["posts"].get(user_id, []):
                executor.submit(fetch_comments, post["id"])
    
    app.run(host="0.0.0.0", port=5000, debug=True)