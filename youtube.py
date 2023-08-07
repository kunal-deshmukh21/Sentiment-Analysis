from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from flask import Blueprint, render_template, request, jsonify
from textblob import TextBlob
import re 
import os
import matplotlib
matplotlib.use('agg')
import matplotlib.pyplot as plt

third = Blueprint("third",  __name__, static_folder="static",
                  template_folder="templates")


def get_video_title(video_id):
    YOUTUBE_API_SERVICE_NAME = "youtube"
    YOUTUBE_API_VERSION = "v3"
    youtube = build(YOUTUBE_API_SERVICE_NAME, YOUTUBE_API_VERSION,
                    developerKey=os.environ.get('DEVELOPERKEY'))

    try:
        video_response = youtube.videos().list(
            part='snippet',
            id=video_id,
            hl='en'
        ).execute()
        if not video_response['items']:
            return None  # Video not found
        video_title = video_response['items'][0]['snippet']['title']
        return video_title
    except HttpError as error:
        print(f"An HTTP error {error.resp.status} occurred:\n{error.content}")
        return None  # Error occurred while fetching video details


@third.route("/sentiment_analyzer1")
def sentiment_analyzer1():
    if request.method == "GET":
        return render_template("sentiment_analyzer1.html")
    elif request.method == "POST":
        video_id = request.form["video_id"]
    comments = request.form["comments"]
    analysis = SentimentAnalysis()
    analysis.DownloadData1(video_id, comments)
    return jsonify(polarity=analysis.fpolarity, positive=analysis.positive, wpositive=analysis.wpositive, spositive=analysis.spositive, negative=analysis.negative, wnegative=analysis.wnegative, snegative=analysis.snegative, neutral=analysis.neutral)


class SentimentAnalysis:
    def __init__(self):
        self.comments = []
        self.commentText = []
        self.fpolarity = None
        self.positive = None
        self.wpositive = None
        self.spositive = None
        self.negative = None
        self.wnegative = None
        self.snegative = None
        self.neutral = None

    def DownloadData1(self, video_id, comments):
        video_title = get_video_title(video_id)
        if video_title is None:
            return {'message': "Video not found. Please check the video ID and try again."}

        video_title_words = video_title.split()
        video_final_words = ' '.join(video_title_words[:7])
        print("video" + video_final_words)

        YOUTUBE_API_SERVICE_NAME = "youtube"
        YOUTUBE_API_VERSION = "v3"
        youtube = build(YOUTUBE_API_SERVICE_NAME, YOUTUBE_API_VERSION,
                        developerKey=os.environ.get('DEVELOPERKEY'))

        comments = int(comments)
        existing_comments = set()
        try:
            video_response = youtube.videos().list(
                part='snippet',
                id=video_id,
                hl='en'
            ).execute()
            if not video_response['items']:
                return {'message': "Video not found. Please check the video ID and try again."}
            video_title = video_response['items'][0]['snippet']['title']
            video_title_words = video_title.split()
            video_final_words = ' '.join(video_title_words[:7])
            print("video" + video_final_words)

            results = youtube.commentThreads().list(
                part="snippet",
                maxResults=comments,
                videoId=video_id,
                textFormat="plainText",
                # hl="en"
            ).execute()
        except HttpError as error:
            print(
                f"An HTTP error {error.resp.status} occurred:\n{error.content}")
            return {'message': "Error retrieving comments. Please try again later"}

        self.comments = results["items"]

        polarity = 0
        positive = 0
        wpositive = 0
        spositive = 0
        negative = 0
        wnegative = 0
        snegative = 0
        neutral = 0

        for comment in self.comments:
                comment_text = self.cleanComment(
                    comment["snippet"]["topLevelComment"]["snippet"]["textDisplay"]).encode('utf-8')
                if comment_text not in existing_comments:
                    self.commentText.append(self.cleanComment(
                        comment["snippet"]["topLevelComment"]["snippet"]["textDisplay"]).encode('utf-8'))
                    existing_comments.add(comment_text)

                analysis = TextBlob(
                    comment["snippet"]["topLevelComment"]["snippet"]["textDisplay"])
                polarity += analysis.sentiment.polarity
                if (analysis.sentiment.polarity == 0):
                    neutral += 1
                elif (analysis.sentiment.polarity > 0 and analysis.sentiment.polarity <= 0.3):
                    wpositive += 1
                elif (analysis.sentiment.polarity > 0.3 and analysis.sentiment.polarity <= 0.6):
                    positive += 1
                elif (analysis.sentiment.polarity > 0.6 and analysis.sentiment.polarity <= 1):
                    spositive += 1
                elif (analysis.sentiment.polarity >= -0.3 and analysis.sentiment.polarity < 0):
                    wnegative += 1
                elif (analysis.sentiment.polarity >= -0.6 and analysis.sentiment.polarity < -0.3):
                    negative += 1
                elif (analysis.sentiment.polarity >= -1 and analysis.sentiment.polarity < -0.6):
                    snegative += 1


        positive = self.percentage(positive, comments)
        wpositive = self.percentage(wpositive, comments)
        spositive = self.percentage(spositive, comments)
        negative = self.percentage(negative, comments)
        wnegative = self.percentage(wnegative, comments)
        snegative = self.percentage(snegative, comments)
        neutral = self.percentage(neutral, comments)

        polarity = polarity / comments

        if (polarity == 0):
            fpolarity = "Neutral"
        elif (polarity > 0 and polarity <= 0.3):
            fpolarity = "Weakly Positive"
        elif (polarity > 0.3 and polarity <= 0.6):
            fpolarity = "Positive"
        elif (polarity > 0.6 and polarity <= 1):
            fpolarity = "Strongly Positive"
        elif (polarity >= -0.3 and polarity < 0):
            fpolarity = "Weakly Negative"
        elif (polarity >= -0.6 and polarity < -0.3):
            fpolarity = "Negative"
        elif (polarity >= -1 and polarity < -0.6):
            fpolarity = "Strongly Negative"

        self.plotPieChart(positive, wpositive, spositive, negative,
                          wnegative, snegative, neutral, video_final_words, comments)
        print(polarity, fpolarity)
        return polarity, fpolarity, positive, wpositive, spositive, negative, wnegative, snegative, neutral, video_final_words, comments
    

    def cleanComment(self,comment):
        comment = re.sub(r'http\S+', '', comment)

        emoji_pattern = re.compile("["
            u"\U0001F600-\U0001F64F"  
            u"\U0001F300-\U0001F5FF"  
            u"\U0001F680-\U0001F6FF"
            u"\U0001F1E0-\U0001F1FF"  
            "]+", flags=re.UNICODE)
        comment = emoji_pattern.sub(r'', comment)


        comment = re.sub(r'[^\w\s]', '', comment)

        comment = re.sub(r'\s+', ' ', comment).strip()

        return comment

    def percentage(self, part, whole):
        temp = 100 * float(part) / float(whole)
        return format(temp, '.2f')

    def plotPieChart(self, positive, wpositive, spositive, negative, wnegative, snegative, neutral, video_final_words, comments):
        try:
            positive = float(positive)
            wpositive = float(wpositive)
            spositive = float(spositive)
            neutral = float(neutral)
            negative = float(negative)
            wnegative = float(wnegative)
            snegative = float(snegative)
            fig, ax = plt.subplots()
            labels = []
            sizes = []
            colors = []
            if positive > 0:
                labels.append('Positive')
                sizes.append(positive)
                colors.append('lightgreen')
            if wpositive > 0:
                labels.append('Weakly Positive')
                sizes.append(wpositive)
                colors.append('yellowgreen')                
            if spositive > 0:
                labels.append('Strongly Positive')
                sizes.append(spositive)
                colors.append('darkgreen')  
            if neutral > 0:
                labels.append('Neutral')
                sizes.append(neutral)
                colors.append('gold')
            if negative > 0:
                labels.append('Negative')
                sizes.append(negative)
                colors.append('red')
            if wnegative > 0:
                labels.append('Weakly Negative')
                sizes.append(wnegative)
                colors.append('lightsalmon')
            if snegative > 0:
                labels.append('Strongly Negative')
                sizes.append(snegative)
                colors.append('darkred')
            patches, texts,autotexts = ax.pie(sizes, colors=colors, startangle=90,autopct='%.2f%%',textprops={'fontsize': 8, 'weight': 'light'})
            ax.legend(patches, labels, loc="best")
            ax.axis('equal')
            ax.set_title("Sentiment Analysis on "+video_final_words)
            fig.tight_layout()
            strFile = r"static\images\youtube.png"
            if os.path.isfile(strFile):
                os.remove(strFile)
            plt.savefig(strFile)
            plt.close(fig)
        except:
            return {'message': 'Error Occured '}

from urllib.error import HTTPError

@third.route("/sentiment_analyzer1/result1")
def result1():
    return render_template("result1.html")


@third.route('/visualize1')
def visualize1():
    return render_template('PieChart1.html')


@third.route('/sentiment_logic1', methods=['POST', 'GET'])
def sentiment_logic1():
    video_id = request.form.get('video_id') 
    print("Videoid is "+video_id)
    comments = request.form.get('comments')
    print("Comment is "+comments)
    if not video_id:
        return "Error: Missing video id"
    if not comments:
        return "Error: Missing comments"
    sa = SentimentAnalysis()

    sentiment_result1 = sa.DownloadData1(video_id, comments)
    print(type(sentiment_result1))
    print(sentiment_result1)
    


    if isinstance(sentiment_result1, dict) and "message" in sentiment_result1:
        print("Debugg"+polarity, fpolarity)
        return sentiment_result1
    else:
        print("Error: Unexpected result type")
    

    polarity, fpolarity, positive, wpositive, spositive, negative, wnegative, snegative, neutral, video_final_words1, comment1 = sentiment_result1
    print(positive)
    print(neutral)
    print(fpolarity)
    print(video_final_words1)
    print(comment1)
    return render_template('result1.html', polarity=polarity, fpolarity=fpolarity, positive=positive, wpositive=wpositive, spositive=spositive,
                           negative=negative, wnegative=wnegative, snegative=snegative, neutral=neutral, video_final_words=video_final_words1, comments=comment1)
    

