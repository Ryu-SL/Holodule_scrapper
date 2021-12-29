from bs4.element import ResultSet
import requests
from bs4 import BeautifulSoup
from flask import Flask, render_template
import csv
from datetime import date


# --------------search streams meeting criteria---------------
class stream:
    def __init__(self):
        self.main_url = "https://schedule.hololive.tv/"
        self.tags_lc = ["sing", "karaoke", "歌", "カラオケ", "cover"]
        self.tags_uc = ["Live", "3D LIVE"]
        self.tags_streamer = {
            "https://yt3.ggpht.com/UwxlX1PuB_RwJyEUW_ofbBR6saY8n5_p8A9_1bY65zygFrfqIb1GM8dIK33EJboDDnRVyw=s176-c-k-c0x00ffffff-no-rj": "irys",
            "https://yt3.ggpht.com/a/AGF-l783JgU1dmBOzvsmUfnbMLLOD1c0Gvuo7TKiVw=s88-c-k-c0xffffffff-no-rj-mo": "pekora",
            "https://yt3.ggpht.com/a/AGF-l78s_0WRnL7hthbRZPmmLSKSCKsxM2DI9FXyAQ=s88-c-k-c0xffffffff-no-rj-mo": "mio",
            "https://yt3.ggpht.com/a/AGF-l79dHleIBmBtLP2TfcmFpIJjmH7fa8tfG1qTKg=s88-c-k-c0xffffffff-no-rj-mo": "sora",
            "https://yt3.ggpht.com/a/AGF-l7-xWfYjQX1VHU2i1BuIap0Ba3tR3T6w4dcCkA=s88-c-k-c0xffffffff-no-rj-mo": "luna",
        }
        self.date_today = date.today().strftime("%m/%d")
        self.date_stream = self.date_today
        self.tag_stream = "sing"

    @staticmethod
    def make_soup(url):
        return BeautifulSoup(requests.get(url).text, "html.parser")

    def check_tag(self, tag, title):
        if "unarchive" in title:
            tag_stream = "unarchive"
        elif "cover" in title:
            tag_stream = "cover"
        elif "L" in tag:
            tag_stream = "live"
        else:
            tag_stream = "sing"
        self.tag_stream = tag_stream

    def check_singing(self, title, tags):
        for tag in tags:
            if tag in title:
                stream.check_tag(self, title, tag)
                return True
        return False

    def check_collab(self, streamers, selected_streamers):
        try:
            for streamer in streamers[3:]:
                if streamer["src"] in selected_streamers:
                    self.tag_stream = "collab"
                    return True
        except:
            None
        return False

    def get_title(self, url, streamers):
        soup = self.make_soup(url)
        title = soup.find("div", {"id": "watch7-content"}).find(
            "meta", {"itemprop": "name"}
        )
        title = str(title).split('"')[1]

        if not stream.check_singing(self, title.lower(), self.tags_lc):
            if not stream.check_singing(self, title, self.tags_uc):
                if not stream.check_collab(self, streamers, self.tags_streamer):
                    return False

        return title

    def get_details(self, soup):
        stream_url = soup["href"]
        if "youtube" in stream_url:
            stream_title = stream.get_title(self, stream_url, soup.find_all("img"))
            if stream_title:
                return (stream_url, stream_title)
        return False

    def check_date(self, soup):
        try:
            stream_date = soup.find("div", {"class": "holodule navbar-text"})
            self.date_stream = stream_date.string.replace(" ", "")[2:7]
            return True
        except:
            return False

    def search_stream(self):
        results = []
        soup = self.make_soup(self.main_url)
        containers = soup.find("div", {"id": "all"}).find_all(
            "div", {"class": "container"}
        )
        print("checking")
        stream_count = 0
        flag = 0
        for container in containers:
            if stream.check_date(self, container):
                flag = flag + 1
                if flag == 2:
                    # date became today, save current results
                    db.update_db(results)
                    print(self.date_stream, "csv updated")

                elif flag == 3:
                    # date became future, save unarchived streams only
                    db.update_db(
                        [result for result in results if result["Tag"] == "unarchive"]
                    )
                    print(self.date_stream, "csv updated - unarchived stream")

                elif flag > 3:
                    break

            schedules = container.find_all("a", {"class": "thumbnail"})
            for i in range(0, len(schedules)):
                result = stream.get_details(self, schedules[i])
                if result:
                    print(result[1])
                    results.append(
                        {
                            "Thumb": schedules[i].find_all("img")[1]["src"],
                            "Url": result[0],
                            "Title": result[1],
                            "Date": self.date_stream,
                            "Time": schedules[i].find("img").nextSibling.strip(),
                            "Streamer": schedules[i]
                            .find("div", {"class", "name"})
                            .string.strip(),
                            "Tag": self.tag_stream,
                        }
                    )
                else:
                    print(stream_count + i + 1, "stream")
            stream_count = stream_count + len(schedules)

        return results


# -------------------------------------------


# Saving stream details for future uses
class db:
    def update_db(results):
        field_names = ["Date", "Streamer", "Time", "Title", "Tag"]
        try:
            with open(
                "Hololive_stream_db.csv", "a", encoding="UTF-8", newline=""
            ) as f_object:
                writer_object = csv.DictWriter(
                    f_object, fieldnames=field_names, extrasaction="ignore"
                )
                writer_object.writerows(results)
                f_object.close()
        except:
            print("Failed to update DB")


# -------------------------------------------

"""
# test
t1 = stream().search_stream()

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
    streams = stream().search_stream()
    return render_template(
        "HoloSearch_outcome.html", resultNo=len(streams), lists=streams
    )


app.run(host="0.0.0.0")
