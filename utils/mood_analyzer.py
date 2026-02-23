import re
from collections import deque
from textblob import TextBlob  # for more accurate sentiment

class MoodAnalyzer:
    def __init__(self, window_size=5):
        self.window_size = window_size
        self.scores = deque(maxlen=window_size)

    def analyze_sentiment(self, text):
        # Use TextBlob for English, fallback to simple lexicon for Malay
        blob = TextBlob(text)
        if blob.sentiment.polarity != 0:
            return blob.sentiment.polarity  # range -1 to 1
        else:
            # Simple Malay lexicon
            positive = {"baik", "suka", "happy", "gembira", "best", "seronok", "bagus", "terbaik",
                        "syiok", "cun", "lawaa", "power", "mantap", "semangat", "ok", "setuju"}
            negative = {"tak", "tidak", "sedih", "sad", "benci", "geram", "fail", "gagal", "susah",
                        "payah", "pening", "stress", "penat", "letih", "boring", "bosan", "malas"}
            tokens = re.findall(r"\w+", text.lower())
            pos = sum(1 for t in tokens if t in positive)
            neg = sum(1 for t in tokens if t in negative)
            total = len(tokens)
            if total == 0:
                return 0.0
            return (pos - neg) / total

    def update(self, text):
        score = self.analyze_sentiment(text)
        self.scores.append(score)
        avg_score = sum(self.scores) / len(self.scores)
        return avg_score

    def get_current_mood(self):
        if not self.scores:
            return 0.0
        return sum(self.scores) / len(self.scores)