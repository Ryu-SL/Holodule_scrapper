import requests
from bs4 import BeautifulSoup
from flask import Flask, render_template, request
import csv
from datetime import datetime, timedelta

KEY_HOLOMEM = {
    "irys": "https://yt3.ggpht.com/UwxlX1PuB_RwJyEUW_ofbBR6saY8n5_p8A9_1bY65zygFrfqIb1GM8dIK33EJboDDnRVyw=s176-c-k-c0x00ffffff-no-rj",
    "pekora": "https://yt3.ggpht.com/a/AGF-l783JgU1dmBOzvsmUfnbMLLOD1c0Gvuo7TKiVw=s88-c-k-c0xffffffff-no-rj-mo",
    "mio": "https://yt3.ggpht.com/a/AGF-l78s_0WRnL7hthbRZPmmLSKSCKsxM2DI9FXyAQ=s88-c-k-c0xffffffff-no-rj-mo",
    "sora": "https://yt3.ggpht.com/a/AGF-l79dHleIBmBtLP2TfcmFpIJjmH7fa8tfG1qTKg=s88-c-k-c0xffffffff-no-rj-mo",
    "luna": "https://yt3.ggpht.com/a/AGF-l7-xWfYjQX1VHU2i1BuIap0Ba3tR3T6w4dcCkA=s88-c-k-c0xffffffff-no-rj-mo",
}


class stream:
    """search streams meeting criteria from holodule"""

    def __init__(self, search_title, search_members):
        self.main_url = "https://schedule.hololive.tv/"
        self.tags_lc = ["sing", "karaoke", "歌", "カラオケ"]
        self.tags_uc = ["Live", "【LIVE", "LIVE【", "3DLIVE"]
        self.tags_mv = ["MV", "ORIGINAL", "COVER", "SONG"]
        self.date_stream = "m/d"
        self.date_count = 0
        self.tag_stream = "sing"
        self.tag_collab_member = []
        self.tag_filter = [
            "superchat",
            "スパチャ",
            "after",
            "closing",
            "振り返り",
            "draw",
            "後夜祭",
            "感想会",
            "missing",
            "crossing",
            "short",
        ]

        self.search_title = False
        if search_title != "":
            self.search_title = [search_title]

        self.search_members = {}
        for search_member in search_members:
            self.search_members[search_member] = KEY_HOLOMEM[search_member]

    @staticmethod
    def make_soup(url):
        return BeautifulSoup(requests.get(url).text, "html.parser")

    def check_tag(self, tag, title):
        if "archive" in title:
            tag_stream = "unarchive"
        elif "L" in tag:
            tag_stream = "live"
        elif "C" in tag or "M" in tag or "歌ってみた" in title:
            tag_stream = "cover"
        else:
            tag_stream = "sing"

        self.tag_stream = tag_stream

    def check_title(self, title, tags):
        for tag in tags:
            if tag in title:
                stream.check_tag(self, tag.upper(), title)
                return True
        return False

    def check_collab(self, streamers):
        # if selected member is host of collab it won't be picked up as youtube subscription will notify
        flag = False
        try:
            for streamer in streamers[3:]:
                for selected_streamer, selected_src in self.search_members.items():
                    if streamer["src"] == selected_src:
                        self.tag_stream = "collab"
                        self.tag_collab_member.append(selected_streamer)
                        flag = True
        except:
            None
        return flag

    def get_title(self, stream_url, streamers):
        soup = self.make_soup(stream_url)
        title = soup.find("div", {"id": "watch7-content"}).find(
            "meta", {"itemprop": "name"}
        )
        title = str(title).split('"')[1]
        self.tag_collab_member = []

        if self.search_title:
            if stream.check_title(self, title.lower(), self.search_title):
                self.tag_stream = "other"
                return title

        if stream.check_title(self, title.lower(), self.tag_filter):
            return False

        if not stream.check_title(self, title.lower(), self.tags_lc):
            if not stream.check_title(self, title.replace(" ", ""), self.tags_uc):
                if not stream.check_title(self, title.upper(), self.tags_mv):
                    if not stream.check_collab(self, streamers):
                        return False

        return title

    def get_details(self, soup):
        stream_url = soup["href"]
        if "youtube" in stream_url:
            try:
                stream_title = stream.get_title(self, stream_url, soup.find_all("img"))
                if stream_title:
                    return (stream_url, stream_title)
            except:
                pass
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
        if flag == 2:
            # date became today, save current results
            print("------------------updating csv")
            db.update_db(results, flag)
        return None
        #'unarcive' probably overweight for ML, may have to remove from db.
        if fla7g == 3:
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
                            "Collab": self.tag_collab_member,
                        }
                    )
                else:
                    print(stream_count + i + 1, "stream")
            stream_count = stream_count + len(schedules)

        return results

    # -------------------------------------------

    """
    #potential filter words:
    -s'ing' terms
        cros'sing'
        progres'sing'
    
    'Live' shows
        live drawing
    
    streamer name including tag:
        '歌'衣メイカ
    """


# -----------------------------------------------
class db:
    """Saving singing stream details for future uses"""

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
        results = [d for d in results if d["Tag"] != "other" and d["Tag"] != "collab"]
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
                # maybe show something on main.html as well?
            else:
                print("--------------update not required")
        except:
            print("Failed to update DB")


# -------------------------------------------

# test
# t1 = stream().search_stream()
# streams = [{"Thumb": "https://img.youtube.com/vi/8oJnlp4cjsk/mqdefault.jpg","Url": "https://www.youtube.com/watch?v=8oJnlp4cjsk","Title": "【歌枠】","Date": "01/04","Time": "22:03","Streamer": "夜空メル","Tag": "sing","Collab": [],}]

# flask
app = Flask("Holodule Search")


@app.route("/")
def search_home():
    return render_template("HoloSearch_main.html")


@app.route("/report", methods=["GET", "POST"])
def show_outcome():
    if request.method == "POST":
        search_title = request.form.get("title").strip()
        search_member = request.form.getlist("member")
    streams = stream(
        search_title=search_title, search_members=search_member
    ).search_stream()
    return render_template(
        "HoloSearch_outcome.html", resultNo=len(streams), lists=streams
    )


app.run(host="0.0.0.0")
