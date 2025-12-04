import cloudscraper
from bs4 import BeautifulSoup
import json
import time

scraper = cloudscraper.create_scraper(browser="chrome")
saved_data = []

ADMIN_USER = "admin"
ADMIN_PASS = "ramnath123"

def scrape_instagram(username, max_posts=100):
    try:
        url = f"https://www.instagram.com/{username}/?__a=1"
        html = scraper.get(url).text
        data = json.loads(html)
        user = data["graphql"]["user"]

        info = {
            "Username": user["username"],
            "Full Name": user["full_name"],
            "Bio": user["biography"],
            "Profile Pic": user["profile_pic_url_hd"],
            "Followers": user["edge_followed_by"]["count"],
            "Following": user["edge_follow"]["count"],
            "Posts": user["edge_owner_to_timeline_media"]["count"],
            "Private": user["is_private"],
            "Verified": user["is_verified"],
            "RecentPosts": []
        }

        edges = user["edge_owner_to_timeline_media"]["edges"]
        count = 0

        while edges and count < max_posts:
            for edge in edges:
                node = edge["node"]
                info["RecentPosts"].append({
                    "id": node["id"],
                    "shortcode": node["shortcode"],
                    "timestamp": node["taken_at_timestamp"],
                    "likes": node["edge_liked_by"]["count"],
                    "comments": node["edge_media_to_comment"]["count"],
                    "display_url": node["display_url"]
                })
                count += 1
                if count >= max_posts:
                    break
            page_info = user["edge_owner_to_timeline_media"]["page_info"]
            if page_info.get("has_next_page"):
                end_cursor = page_info.get("end_cursor")
                next_url = f"https://www.instagram.com/graphql/query/?query_hash=...&variables={{\"id\":\"{user['id']}\",\"first\":50,\"after\":\"{end_cursor}\"}}"
                res = scraper.get(next_url).text
                res_data = json.loads(res)
                edges = res_data["data"]["user"]["edge_owner_to_timeline_media"]["edges"]
                user["edge_owner_to_timeline_media"]["page_info"] = res_data["data"]["user"]["edge_owner_to_timeline_media"]["page_info"]
                time.sleep(2)
            else:
                break

        saved_data.append(info)
        return info

    except Exception as e:
        return {"error": str(e)}

def handler(request):
    mode = request.args.get("mode")

    if mode == "fetch":
        username = request.args.get("u")
        return scrape_instagram(username)

    if mode == "admin":
        u = request.args.get("user")
        p = request.args.get("pass")
        if u == ADMIN_USER and p == ADMIN_PASS:
            return {"status":"success","data":saved_data}
        else:
            return {"error":"Invalid admin credentials"}

    return {"error":"Invalid mode"}
