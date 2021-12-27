import requests
from bs4 import BeautifulSoup
from flask import Flask, render_template, request

hrs = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.101 Safari/537.36"
}
url_main = "https://schedule.hololive.tv/"
tag_sing = ["sing", "karaoke", "歌", "カラオケ", "cover", "song"]
tag_member = {
    "https://yt3.ggpht.com/UwxlX1PuB_RwJyEUW_ofbBR6saY8n5_p8A9_1bY65zygFrfqIb1GM8dIK33EJboDDnRVyw=s176-c-k-c0x00ffffff-no-rj": "irys",
    "https://yt3.ggpht.com/a/AGF-l783JgU1dmBOzvsmUfnbMLLOD1c0Gvuo7TKiVw=s88-c-k-c0xffffffff-no-rj-mo": "pekora",
    "https://yt3.ggpht.com/a/AGF-l78s_0WRnL7hthbRZPmmLSKSCKsxM2DI9FXyAQ=s88-c-k-c0xffffffff-no-rj-mo": "mio",
    "https://yt3.ggpht.com/a/AGF-l79dHleIBmBtLP2TfcmFpIJjmH7fa8tfG1qTKg=s88-c-k-c0xffffffff-no-rj-mo": "sora",
    "https://yt3.ggpht.com/a/AGF-l7-xWfYjQX1VHU2i1BuIap0Ba3tR3T6w4dcCkA=s88-c-k-c0xffffffff-no-rj-mo": "luna",
}

# --------------search with stream title---------------
class stream:
    def get_title(url, streamers):
        req = requests.get(url, headers=hrs)
        soup = BeautifulSoup(req.text, "html.parser")
        title = soup.find("div", {"id": "watch7-content"}).find(
            "meta", {"itemprop": "name"}
        )
        title = str(title).split('"')[1]
        for tag in tag_sing:
            if tag in title.lower():
                return title
        if "Live" in title or "3D LIVE" in title:
            return title
        try:
            for streamer in streamers[3:]:
                if streamer["src"] in tag_member:
                    return title
        except:
            None
        return False

    def get_details(soup):
        stream_url = soup["href"]
        if "youtube" in stream_url:
            stream_title = stream.get_title(stream_url, soup.find_all("img"))
            if stream_title:
                return (stream_url, stream_title)
        return False

    def search_stream():
        results = []
        req = requests.get(url_main, headers=hrs)
        soup = BeautifulSoup(req.text, "html.parser")
        containers = soup.find("div", {"id": "all"}).find_all(
            "a", {"class": "thumbnail"}
        )
        print("checking")
        for i in range(0, len(containers)):
            result = stream.get_details(containers[i])
            if result:
                print(result[1])
                results.append(
                    {
                        "url": result[0],
                        "title": result[1],
                        "thumb": containers[i].find_all("img")[1]["src"],
                        "time": containers[i].find("img").nextSibling.strip(),
                    }
                )
            else:
                print(i + 1, "stream")
        return results


# -------------------------------------------
"""
# test
t1 = stream.search_stream()
for t2 in t1:
    print(t2)
"""


# flask
app = Flask("Holodule Search")


@app.route("/")
def search_home():
    return render_template("HoloSearch_main.html")


@app.route("/report", methods=["POST"])
def show_outcome():
    streams = stream.search_stream()
    return render_template(
        "HoloSearch_outcome.html", resultNo=len(streams), lists=streams
    )


app.run(host="0.0.0.0")
