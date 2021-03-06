import os
import threading, time
from flask import Flask, request, jsonify, render_template
from flask_sqlalchemy import SQLAlchemy
import random
import operator
from datetime import datetime
import markovify


# make sure to use the up-to-date import formet: from flast_module import Module
# DO NOT use deprecated from flask.ext.module import Module
import tweepy
# from scripts import generate_freq_dict
tweetFile = 'tweets.txt'
app = Flask(__name__)

app.config.from_object(os.environ['APP_SETTINGS'])
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

auth = tweepy.OAuthHandler('secret', 'secret')
auth.set_access_token('secret', 'secret')

api = tweepy.API(auth)

db = SQLAlchemy(app)
print("tweepy")
print(tweepy)

isLiking = False

class Topic(db.Model):
    __tablename__ = 'topics'

    id = db.Column(db.Integer, primary_key=True)
    topicName = db.Column(db.String())

    def __init__(self, topicName):
        self.topicName = topicName


    def __repr__(self):
        return '<id {}>'.format(self.id)
    
    def serialize(self):
        return {
            'id': self.id, 
            'topicName': self.topicName
        }


class TweetText(db.Model):
    __tablename__ = 'tweetText'

    id = db.Column(db.Integer, primary_key=True)
    tweetText = db.Column(db.String())

    def __init__(self, tweetText):
        self.tweetText = tweetText


    def __repr__(self):
        return '<id {}>'.format(self.id)
    
    def serialize(self):
        return {
            'id': self.id, 
            'tweetText': self.tweetText
        }

@app.route("/")
def hello():
    return "goto main and start using"

def generate_freq_dict(tweetFile):
    freq_dict = {}
    beginning_dict = {}
    tweetTextLst = []
    try:
        tweets = TweetText.query.all()
    except:
         return "no tweets in db"
    if len(tweets) < 10:
        return "not enough tweets in db"
    partialTts = tweets



    for tts in partialTts:
        print("----")
        print(tts.tweetText)
        line = tts.tweetText
        lst = line.strip().replace(",", " ").replace(".", " ").replace("@", "").split(" ")
        lst = list(filter(None, lst))
        if len(lst) < 3:
            continue
        # print(lst)
        if len(lst) > 0:
            if lst[0].lower() in beginning_dict:
                beginning_dict[lst[0].lower()] += 1
            else:
                beginning_dict[lst[0].lower()] = 1
        for i in range(len(lst)-1):
            if lst[i].lower() not in freq_dict:
                tmp_dict = dict()
                tmp_dict[lst[i+1].lower()] = 1
                freq_dict[lst[i].lower()] = tmp_dict
            else:
                tmp_dict = freq_dict[lst[i].lower()]
                if lst[i+1].lower() not in tmp_dict:
                    tmp_dict[lst[i+1].lower()] = 1
                else:
                    tmp_dict[lst[i+1].lower()] += 1
        # print(freq_dict)
    # print(beginning_dict)
    try:
        beg = max(beginning_dict.iteritems(), key=operator.itemgetter(1))[0]
    except:
        print("error with getting beg")
        return "this is a fabulous day"
    # print(beg)
    cnt = 0
    finalstr = ""
    maxNext = beg
    while cnt < 50 and maxNext in freq_dict:
        # print(cnt)
        # guess the next word
        finalstr += " " + maxNext
        word_dict = freq_dict[maxNext]
        # print("word_dict")
        # print(word_dict)
        maxNext= max(word_dict.iteritems(), key=operator.itemgetter(1))[0]
        print("next: %s" % maxNext)
        word_dict[maxNext] = 0
        cnt += 1
    finalstr = finalstr + " " + maxNext

    print("finalstr")
    print(finalstr)
    if len(finalstr) < 35:
        beginning_dict[beg] = 0
        beg = max(beginning_dict.iteritems(), key=operator.itemgetter(1))[0]
        # print(beg)
        cnt = 0
        finalstr = finalstr + "."
        maxNext = beg
        while cnt < 50 and maxNext in freq_dict:
            # print(cnt)
            # guess the next word
            finalstr += " " + maxNext
            word_dict = freq_dict[maxNext]
            # print("word_dict")
            # print(word_dict)
            maxNext= max(word_dict.iteritems(), key=operator.itemgetter(1))[0]
            word_dict[maxNext] = 0

            print("next: %s" % maxNext)
            cnt += 1

        finalstr = finalstr + " " + maxNext
    print("finalstr")
    print(finalstr)
    print("bottom of generate_freq_dict")
    return finalstr


@app.before_first_request
def activate_job():
    def run_job():
        sendTweetCnt = 0
        wait = 1
        while True:
            print("Run recurring task")
            refresh_txt()
            sendTweetCnt += 1
            if sendTweetCnt == 2:
                sendTweet(sendTweetCnt)
            if sendTweetCnt % 2 == 0:
                refresh_txt()
            print("send cnt: %s" % sendTweetCnt)
            if sendTweetCnt % 2 == 0:
                print("sendTweetCnt: %s, time to send" % sendTweetCnt)
                sendTweet(sendTweetCnt)
                print("sent last tweet, sleeping %s" % wait)
            time.sleep(wait)

    thread = threading.Thread(target=run_job)
    thread.start()

def sendTweet(sendTweetCnt):
    print("in sendTweet")
    print("sendTweetCnt: %s" % sendTweetCnt)


    tweetText = "testing tweet plz don't take me serious :/ %s" % sendTweetCnt

    # Get text from MC function====
    # actualText = generate_freq_dict(tweetFile)
    start = datetime.now()
    print("markov start: %s" % start)

    print("Reading text")
    with open(tweetFile) as f:
        text = f.read()

    # build model
    print("build model")
    text_model = markovify.Text(text)

    print("text_model make")
    actualText = text_model.make_short_sentence(280)
    if actualText:
        actualText.replace("@", "at:")

        print("sendTweet actualText: %s" % actualText)
        tweetText = actualText + " " + str(sendTweetCnt)
# =====
    try:
        api.update_status(tweetText)
        print("if success, should send \"%s\" to account" % tweetText)
    except Exception as e:
        print("error in send tweet")
        print(e)
        return(str(e))


def likeTweet():
    topics = Topic.query.all()
    if len(topics) == 0:
        print("no topics, nothing to like")
        return
    topicNames = "Nyc"
    for topic in topics:
        print("topic:")
        print(topic)
        tpn = topic.serialize()['topicName'].encode('ascii', 'ignore')
        print("type(tpn)")
        print(type(tpn))
        topicNames=str(topicNames) + ' OR ' + str(tpn)
    print("topics from db: %s" % topicNames)

    query = topicNames
    print("query: %s" % query)
    count = 100
    last_id = -1
    print("in likeTweet")
    try:
        new_tweets = api.search(q=query, count=count, max_id=str(last_id - 1))
        print("new_tweets len: %s" % len(new_tweets))
    except:
        print("error in liketweet line 242")
        new_tweets = []

    # delete all old records
    try:
        TweetText.query.filter(TweetText.id>=0).delete()
        db.session.commit()
    except Exception as e:
            return(str(e))

    for t in new_tweets:
        # print(type(t))
        # print(t.text)
        # with open(tweetFile, 'w') as f:
        #     f.write(t.text.encode('ascii', 'ignore') + '\n')
        # print("t is===: %s" % t)
        text = t.text.encode('ascii', 'ignore')
        # print("new_tweets===: %s: " % text)
        try:
            tweetRow=TweetText(
                tweetText=text
            )
            db.session.add(tweetRow)
            db.session.commit()
            # topics = Topic.query.all()
            # topicNames = []
            # for topic in topics:
            #     topicNames.append(topic.serialize()['topicName'])
            info = "Added %s to db" % tweetRow
            print(info) 
        except Exception as e:
            return(str(e))

    # pick a new tweet to like
    r = int(random.random() * count)
    print("random:" + str(r))
    if new_tweets:
        print(new_tweets[r].text)


def start_runner():
    print("start runner")
    def start_loop():
        print("in start loop")
        not_started = True
        while not_started:
            print('In start loop, isLiking is %s' % isLiking)
            try:
                r = requests.get('http://127.0.0.1:5000/')
                if r.status_code == 200:
                    print('Server started, quiting start_loop')
                    not_started = False
                print(r.status_code)
            except:
                print('Server not yet started')
            time.sleep(30)

    print('Started runner')
    thread = threading.Thread(target=start_loop)
    thread.start()


def refresh_txt():
    # get topics from table
    # fill db with lines from these topics
    # convert db into a txt
    try:
        TweetText.query.filter(TweetText.id>=0).delete()
        db.session.commit()
    except Exception as e:
        return(str(e))

    with open(tweetFile, "w+") as f:
        f.write("start of tweetFile")

    topics = Topic.query.all()
    if len(topics) == 0:
        print("no topics, nothing to query")
        return
    print("topics from db: %s" % topics)
    topicStr = []
    for topic in topics:
        # put each topic's tweets into db
        print("topic:")
        print(topic)
        tpn = topic.serialize()['topicName'].encode('ascii', 'ignore')
        print("tpn: %s" % tpn)
        topicStr.append(str(tpn))
    print("topics from db: %s" % topics)

    for topic in topicStr:
        query = topic
        print("querying: %s" % query)
        count = 100
        last_id = -1
        print("in refresh_txt")
        try:
            new_tweets = api.search(q=query, count=count, max_id=str(last_id - 1))
            print("topis: %s new_tweets len: %s" % (topic, len(new_tweets)))
        except:
            print("error in refresh_txt line 350")
            new_tweets = []
            return

        for t in new_tweets:
            # print(type(t))
            # print(t.text)
            text = t.text.encode('ascii', 'ignore')
            text = text.replace("@", "at:")
            if len(text) <40:
                print("this is too short: %s" % text)
                continue
            if "https" in text:
                print("%s has links, remove" % text)
                continue
            print("write to file")
            with open(tweetFile, 'a+') as f:
                f.write(text + '\n')
            # print("t is===: %s" % t)
            # print("new_tweets===: %s: " % text)
            try:
                tweetRow=TweetText(
                    tweetText=text
                )
                db.session.add(tweetRow)
                db.session.commit()
                # topics = Topic.query.all()
                # topicNames = []
                # for topic in topics:
                #     topicNames.append(topic.serialize()['topicName'])
                info = "Added %s to db" % tweetRow
                print(info) 
            except Exception as e:
                return(str(e))

    print("bootom of refresh_txt")


@app.route('/tweets')
def show_tweets():
    timeline = api.home_timeline()
    tweets = []
    for t in timeline:
        tweets.append(t.text)
    topicNames = ["no topics"]
    info = "no infotext"
    return render_template("getdata.html", topicNames = topicNames, infotext = info, tweets = tweets)



@app.route("/add")
def add_topic():
    topicName=request.args.get('topicName')
    try:
        topic=Topic(
            topicName=topicName
        )
        db.session.add(topic)
        db.session.commit()
        return "Topic added. Topic id={}".format(topic.id)
    except Exception as e:
        return(str(e))

@app.route("/getall")
def get_all():
    try:
        topics=Topic.query.all()
        return  jsonify([e.serialize() for e in topics])
    except Exception as e:
        return(str(e))

@app.route("/get/<id_>")
def get_by_id(id_):
    try:
        topic=Topic.query.filter_by(id=id_).first()
        return jsonify(topic.serialize())
    except Exception as e:
        return(str(e))

@app.route("/main",methods=['GET', 'POST'])
def add_topic_form():
    topics = Topic.query.all()
    topicNames = []
    info = "Add a topic you would like to track"
    for topic in topics:
        topicNames.append(topic.serialize()['topicName'])
    print(topicNames)
    if request.method == 'POST':
        print("Post method")
        topicName=request.form.get('topicName')
        if topicName not in topicNames:
            try:
                topic=Topic(
                    topicName=topicName
                )
                db.session.add(topic)
                db.session.commit()
                topics = Topic.query.all()
                topicNames = []
                for topic in topics:
                    topicNames.append(topic.serialize()['topicName'])
                info = "Added %s to db" % topicName 
                return render_template("getdata.html", topicNames = topicNames, infotext = info)
            except Exception as e:
                return(str(e))
        else:
            info = "%s is in the db already" % topicName 
            return render_template("getdata.html", topicNames = topicNames, infotext = info)   
    print("returning at the bottom")          
    return render_template("getdata.html", topicNames = topicNames, infotext = info)


if __name__ == '__main__':
    start_runner()
    app.run()
