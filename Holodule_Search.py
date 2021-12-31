import requests
from bs4 import BeautifulSoup
from flask import Flask, render_template
import csv
from datetime import datetime, timedelta


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
        self.date_stream = "m/d"
        self.date_count = 0
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
                stream.check_tag(self, tag, title)
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

    def get_title(self, stream_url, streamers):
        soup = self.make_soup(stream_url)
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
            self.date_count = self.date_count + 1
            return True
        except:
            return False

    @staticmethod
    def check_update(flag, results):
        # flag = 0  # do not update db
        if flag == 2:
            # date became today, save current results
            print("------------------updating csv")
            db.update_db(results, flag)

        elif flag == 3:
            # date became future, save unarchived streams only
            print("-----------------updating unarchived stream")
            db.update_db(
                [result for result in results if result["Tag"] == "unarchive"], flag
            )

    def search_stream(self):
        results = []
        soup = self.make_soup(self.main_url)
        containers = soup.find("div", {"id": "all"}).find_all(
            "div", {"class": "container"}
        )
        print("checking")
        stream_count = 0
        for container in containers:
            if stream.check_date(self, container):
                stream.check_update(self.date_count, results)

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
    def get_date(flag):
        date = datetime.today()
        if flag == 2:
            date = date - timedelta(1)
        return date.strftime("%m/%d")

    def check_dup(results, flag_date):
        # read date compare time as unique ID to check duplicate
        date_tbc = db.get_date(flag_date)
        with open("Hololive_stream_db.csv", "r", encoding="UTF-8") as f_object:
            read_object = csv.DictReader(f_object, delimiter=",")
            db_streams = [d for d in read_object if d["\ufeffDate"] == date_tbc]
            f_object.close()

        new_streams = []
        for i in range(0, len(db_streams)):
            db_streams[i]["Time"] = db_streams[i]["Time"].zfill(5)

        for result in results:
            result["Time"] = result["Time"].zfill(5)
            flag_duplicate = True
            for db_stream in db_streams:
                if result["Time"] == db_stream["Time"]:
                    flag_duplicate = False
                    db_streams.remove(db_stream)
                    break
            if flag_duplicate:
                new_streams.append(result)

        return new_streams

    def update_db(results, flag_date):
        field_names = ["Date", "Streamer", "Time", "Title", "Tag"]
        results = db.check_dup(results, flag_date)
        try:
            with open(
                "Hololive_stream_db.csv", "a", encoding="UTF-8", newline=""
            ) as f_object:
                writer_object = csv.DictWriter(
                    f_object, fieldnames=field_names, extrasaction="ignore"
                )
                writer_object.writerows(results)
                f_object.close()
            if results:
                print(f"----------------DB succesfully updated({len(results)} streams)")
            else:
                print("--------------update not required")
        except:
            print("Failed to update DB")


# -------------------------------------------


# test
# t1 = stream().search_stream()


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
