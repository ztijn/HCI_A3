# File: coursework3.py
# Date: April 10th, 2020
# Authors: Lars de Roo(s3728072)
# and Robin Snoek (s3792846)

import io
import tweepy
import geopy  # pip3 install geopy
from geopy.geocoders import Nominatim
from geopy import distance as Distance
from iso639 import languages as iso_languages  # pip3 install iso-639
import tkinter as tk
import tkinter.ttk as ttk
from tkinter import messagebox
from tkinter.filedialog import askopenfilename
import threading
import time
import queue
import nltk
from nltk.sentiment.vader import SentimentIntensityAnalyzer  # pip3 install nltk
# nltk.download('vader_lexicon')
import re
import numpy as np  # pip3 install numpy
from googletrans import Translator


class Dialog(tk.Toplevel):
    def __init__(self, parent):
        super().__init__(parent)
        self.transient(parent)  # Bind to parent window
        self.title('Change Credentials')
        self.parent = parent

        self.body = tk.Frame(self)  # create body for input and buttons
        self.rows = 0
        while self.rows < 7:
            self.rowconfigure(self.rows, weight=1)
            self.columnconfigure(self.rows, weight=1)
            self.rows += 1
        self.body.grid(padx=5, pady=5)

        self.grab_set()  # Make window modal
        self.body.focus_set()
        self.protocol("WM_DELETE_WINDOW", self.cancel)

        self.e1 = ttk.Entry(self.body)
        self.e2 = ttk.Entry(self.body)
        self.e3 = ttk.Entry(self.body)
        self.e4 = ttk.Entry(self.body)
        self.change_button = ttk.Button(self.body, text='Change credentials', command=self.ok, width=20)
        self.cancel_button = ttk.Button(self.body, text='Cancel', command=self.cancel, width=14)
        self.to_body()
        self.body.grid(padx=5, pady=5)

    def to_body(self):
        if Part1.started:
            warning = tk.Label(self.body, text='(Changes will be applied after program restart.)')
            warning.grid(row=0, column=0, columnspan=2, pady=3, sticky="w")
        tk.Label(self.body, text="Consumer key:").grid(row=1, pady=3, sticky="w")
        tk.Label(self.body, text="Consumer key secret:").grid(row=2, pady=3, sticky="w")
        tk.Label(self.body, text="Access token:").grid(row=3, pady=3, sticky="w")
        tk.Label(self.body, text="Access token secret:").grid(row=4, pady=3, sticky="w")

        self.e1.grid(row=1, column=1)
        self.e2.grid(row=2, column=1)
        self.e3.grid(row=3, column=1)
        self.e4.grid(row=4, column=1)
        self.change_button.grid(row=5, column=0, pady=5, padx=3)
        self.cancel_button.grid(row=5, column=1, pady=5, padx=3)
        self.bind("<Return>", self.ok)
        self.bind("<Escape>", self.cancel)

    def ok(self, event=None):
        self.withdraw()
        self.update_idletasks()
        self.apply()
        self.cancel()

    def cancel(self, event=None):
        # put focus back to the parent window
        self.parent.focus_set()
        self.destroy()

    def apply(self):
        e1, e2, e3, e4 = self.e1.get(), self.e2.get(), self.e3.get(), self.e4.get()
        if e1 and e2 and e3 and e4:
            f = io.open('credentials.txt', 'w', encoding='utf8')
            print(e1, e2, e3, e4, file=f, sep='\n', end='')
            f.close()
        else:
            messagebox.showerror("Error:", "Please fill in all fields")


class MyStreamListener(tweepy.StreamListener):
    def on_status(self, status):
        if status.in_reply_to_status_id and status.in_reply_to_status_id is not None:
            tweet_queue.put(status)

    def on_error(self, status_code):
        if status_code == 420:  # Disconnect stream if request limit reached
            return False
        if status_code == 179:
            pass


class NewMenu(tk.Frame):
    current_file = None

    def __init__(self, master):
        super().__init__(master)
        self.menubar = tk.Menu(master)
        self.file_menu = tk.Menu(self.menubar, tearoff=0)
        self.edit_menu = tk.Menu(self.menubar, tearoff=0)
        self.create_menu()
        master.config(menu=self.menubar)
        self.master = master

    def create_menu(self):
        self.file_menu.add_command(label="Open", command=self.on_open)
        self.file_menu.add_command(label="Exit", command=self.on_exit)
        self.menubar.add_cascade(label="File", menu=self.file_menu)
        self.edit_menu.add_command(label="Change credentials", command=lambda: Dialog(self.master))
        self.edit_menu.add_command(label="Reset credentials", command=self.on_reset)
        self.menubar.add_cascade(label="Edit", menu=self.edit_menu)

    def on_exit(self):
        self.quit()
        self.master.destroy()

    def on_open(self):
        NewMenu.current_file = askopenfilename(parent=self.master)

    def on_reset(self):
        f = io.open('credentials.txt', 'w', encoding='utf8')
        print('mCrqdMTpF8MBqaZyzGERQUTCy',
              'vc141IO4yN1EBbMJie7neYH0cjNMu5chM8a827CL80KRGjzwjz',
              '1242373306768113664-tTy0GsqqJFwOPG0ZD59ulgLXuP5Ppu',
              'Ao9C0zQbU3rLWHDyCKFnk0MmOOgMNlDG542vpEbc5Qidq', file=f, sep='\n', end='')
        f.close()


class MainWindow(ttk.Notebook):
    def __init__(self, master):
        super().__init__(master)
        master.title('HCI Coursework 3: Twitter Conversation')
        self.part1 = Part1(master)
        self.part2 = Part2(master)
        self.add(self.part1, text='Twitter Conversations')
        self.add(self.part2, text='Sentiment Analysis')


class Part1(tk.Frame):
    started = False

    def __init__(self, master):
        super().__init__(master)
        self.bottom = tk.Frame(self)
        # Configure grid
        self.rows = 0
        while self.rows < 50:
            self.rowconfigure(self.rows, weight=1)
            self.columnconfigure(self.rows, weight=1)
            self.bottom.columnconfigure(self.rows, weight=1)
            self.rows += 1
        self.rows = 0
        while self.rows < 3:
            self.bottom.rowconfigure(self.rows, weight=1)
            self.rows += 1

        self.bottom.grid(row=47, column=0, columnspan=50, rowspan=3, sticky='ew', padx=3, pady=3)

        # Define widgets
        self.tree = ttk.Treeview(self)  # Conversation tree view
        self.tree["columns"] = "title"
        self.tree.column("#0", stretch='NO', anchor="w", minwidth=50)
        self.tree.column("title", stretch='YES', anchor="w")
        self.tree.heading("#0", text="User", anchor="w")
        self.tree.heading("title", text="Tweet", anchor="w")
        self.vsb = ttk.Scrollbar(self.tree, orient="vertical", command=self.tree.yview)
        self.hsb = ttk.Scrollbar(self.tree, orient="horizontal", command=self.tree.xview)
        self.tree.configure(yscrollcommand=self.vsb.set, xscrollcommand=self.hsb.set)

        self.filter_label = ttk.Label(self.bottom, text='Search Options', font=("Helvetica", 14))
        self.filter_desc_label = ttk.Label(self.bottom, text='Filter tweets based on input', font=("", 9))
        self.search_term_label = ttk.Label(self.bottom, text='Search terms / hashtag:', font=("", 10))
        self.search_term_desc_label = ttk.Label(self.bottom, text='(Seperate terms with a comma and a space)', font=("", 8))
        self.search_term = ttk.Entry(self.bottom)  # Search term entry
        self.language_label = ttk.Label(self.bottom, text='Tweet language:', font=("", 10))
        self.language_desc_label = ttk.Label(self.bottom, text='(ISO 639-1 code)', font=("", 8))
        self.language = ttk.Entry(self.bottom)  # Language entry
        self.address_label = ttk.Label(self.bottom, text='Sent from location:', font=("", 10))
        self.address_desc_label = ttk.Label(self.bottom, text='(Address or City)', font=("", 8))
        self.address = ttk.Entry(self.bottom)  # Location
        self.address_radius_label = ttk.Label(self.bottom, text='Maximum distance from location:', font=("", 10))
        self.address_radius_desc_label = ttk.Label(self.bottom, text='(In kilometers):', font=("", 8))
        self.address_radius = ttk.Entry(self.bottom)  # Radius entry
        self.start_button = ttk.Button(self.bottom, text='Start stream', command=self.start_stream)
        self.pause_button = ttk.Button(self.bottom, text='Pause stream', state="disabled", command=self.toggle_stream,
                                       width=14)
        self.to_grid()  # Put widgets on grid
        # Define variables
        self.paused = False
        self.conversation_queue = queue.Queue()
        self.languages = [lang.part1 for lang in iso_languages]
        self.filename = ''

    def to_grid(self):
        self.tree.grid(row=0, column=0, rowspan=46, columnspan=50, sticky="nsew")
        self.vsb.pack(side="right", fill="y")
        self.hsb.pack(side="bottom", fill="x")
        self.filter_label.grid(row=1, column=0, rowspan=1, columnspan=8, sticky="nsw")
        self.filter_desc_label.grid(row=1, column=11, rowspan=1, columnspan=20, sticky="nsw")
        self.search_term_label.grid(row=2, column=0, rowspan=1, columnspan=10, sticky="nsw")
        self.search_term.grid(row=3, column=0, rowspan=1, columnspan=10, sticky="ew")
        self.search_term_desc_label.grid(row=4, column=0, rowspan=1, columnspan=10, sticky="nsw")
        self.language_label.grid(row=2, column=11, rowspan=1, columnspan=10, sticky="nsw")
        self.language.grid(row=3, column=11, rowspan=1, columnspan=10, sticky="ew")
        self.language_desc_label.grid(row=4, column=11, rowspan=1, columnspan=10, sticky="nsw")
        self.address_label.grid(row=2, column=22, rowspan=1, columnspan=10, sticky="nsw")
        self.address.grid(row=3, column=22, rowspan=1, columnspan=10, sticky="ew")
        self.address_desc_label.grid(row=4, column=22, rowspan=1, columnspan=10, sticky="nsw")
        self.address_radius_label.grid(row=2, column=33, rowspan=1, columnspan=10, sticky="nsw")
        self.address_radius.grid(row=3, column=33, rowspan=1, columnspan=10, sticky="ew")
        self.address_radius_desc_label.grid(row=4, column=33, rowspan=1, columnspan=10, sticky="nsw")
        self.start_button.grid(row=4, column=45, rowspan=1, columnspan=6, padx=3, pady=3, sticky="nesw")
        self.pause_button.grid(row=3, column=45, rowspan=1, columnspan=6, padx=3, pady=3, sticky="nesw")

    def start_stream(self):
        # Start processes on seperate threads
        tweet_stream = threading.Thread(target=self.stream_tweets, daemon=True).start()
        process_stream = threading.Thread(target=self.process_tweets, daemon=True).start()
        conversation_stream = threading.Thread(target=self.to_tree, daemon=True).start()
        # Edit buttons and unpause
        self.start_button.configure(state='disabled')
        self.pause_button.configure(state='normal')
        self.paused = False
        # Disable filters
        self.search_term.configure(state='disabled')  # Search term entry
        self.language.configure(state='disabled')  # Language entry
        self.address.configure(state='disabled')  # Location
        self.address_radius.configure(state='disabled')  # Radius entry
        Part1.started = True

    def stream_tweets(self):
        self.authenticate()
        listener = MyStreamListener()
        stream = tweepy.Stream(auth=self.twitter.auth, listener=listener)
        stream.filter(**self.get_filter())

    def process_tweets(self):
        while True:
            try:
                if not self.paused:
                    tweet = tweet_queue.get(block=False)
                    if tweet is not None:
                        #  Check if conversation, add to list, add reply
                        self.get_conversation(tweet, [], [])
            except queue.Empty:
                time.sleep(1)
                pass

    def toggle_stream(self):
        self.paused = not self.paused
        if self.paused:
            self.pause_button.configure(text="Continue stream")
        else:
            self.pause_button.configure(text='Pause stream')

    def get_conversation(self, tweet, convo, participants):
        convo.append(tweet)
        participants.append(tweet.user.screen_name)
        try:
            # Check if tweet has a reply
            if tweet.in_reply_to_status_id and tweet.in_reply_to_status_id is not None:
                self.get_conversation(self.twitter.get_status(id=tweet.in_reply_to_status_id), convo, participants)
            else:
                if 3 <= len(convo) <= 10 and len(set(participants)) > 1:
                    self.conversation_queue.put(convo)
        except tweepy.error.TweepError:
            time.sleep(1)
            pass

    def get_location(self, address):
        geolocator = Nominatim(user_agent="HCI:Coursework 3")
        address_geo = geolocator.geocode(address)
        if address_geo is not None:
            address_point = geopy.Point(address_geo.latitude, address_geo.longitude)
            if self.address_radius.get() and self.address_radius.get() is not None and re.match(
                    '^[0-9]*$', self.address_radius.get()):
                radius = int(self.address_radius.get())
                distance = Distance.geodesic(kilometers=radius)
                n = distance.destination(point=address_point, bearing=0)
                e = distance.destination(point=address_point, bearing=90)
                s = distance.destination(point=address_point, bearing=180)
                w = distance.destination(point=address_point, bearing=270)
                location = [n.latitude, w.longitude, s.latitude, e.longitude]
            else:
                location = [address_geo.latitude, address_geo.longitude, address_geo.latitude, address_geo.longitude]
            return location

    def get_filter(self):
        search = self.search_term.get()
        tweet_filter = {}
        filters = []
        if search is not None:
            if len(search) == 0:
                tweet_filter['track'] = 'twitter'
                filters.append('twitter')
            else:
                tweet_filter['track'] = search.split(', ')
                filters.append(' '.join(search.split(', ')))
        if self.language.get() in self.languages:
            tweet_filter['languages'] = [self.language.get()]
            filters.append(self.language.get())
        if self.address.get() != '':
            tweet_filter['locations'] = self.get_location(self.address.get())
            filters.append(self.address.get())
        self.filename = '+'.join(filters) + '.txt'
        return tweet_filter

    def to_tree(self):
        while True:
            try:
                if not self.paused:
                    conversation = self.conversation_queue.get(block=False)
                    if conversation is not None:
                        with io.open(self.filename, "a", encoding='utf8') as myfile:
                            print(conversation[0].id, file=myfile)
                            for tweet in conversation[::-1]:
                                self.tree.insert('', 'end', text=(tweet.user.screen_name,), values=(tweet.text,))
                        self.tree.insert('', 'end', text='')  # Conversation separator
            except queue.Empty:
                time.sleep(1)
                pass

    def authenticate(self):
        with io.open('credentials.txt', 'r', encoding='utf8') as file:
            credentials = [x.split('\n') for x in file]
            # Authenticate to Twitter
            auth = tweepy.OAuthHandler(credentials[0][0], credentials[1][0])
            auth.set_access_token(credentials[2][0], credentials[3][0])
            self.twitter = tweepy.API(auth)  # test authentication


class Part2(tk.Frame):
    def __init__(self, master):
        super().__init__(master)
        self.bottom = tk.Frame(self)
        # Configure grid
        self.rows = 0
        while self.rows < 50:
            self.rowconfigure(self.rows, weight=1)
            self.columnconfigure(self.rows, weight=1)
            self.bottom.columnconfigure(self.rows, weight=1)
            self.rows += 1
        self.rows = 0
        while self.rows < 3:
            self.bottom.rowconfigure(self.rows, weight=1)
            self.rows += 1

        self.bottom.grid(row=47, column=0, columnspan=50, rowspan=3, sticky='ew', padx=3, pady=3)
        # Treeview for conversations
        self.tree = ttk.Treeview(self)
        self.tree["columns"] = "title", "sentiment"
        self.tree.column("#0", stretch='NO', anchor="w", minwidth=50)
        self.tree.column("title", stretch='YES', anchor="w")
        self.tree.column("sentiment", stretch='YES', anchor="w")
        self.tree.heading("#0", text="User", anchor="w")
        self.tree.heading("title", text="Tweet", anchor="w")
        self.tree.heading("sentiment", text="Sentiment", anchor="w")
        self.vsb = ttk.Scrollbar(self.tree, orient="vertical", command=self.tree.yview)
        self.hsb = ttk.Scrollbar(self.tree, orient="horizontal", command=self.tree.xview)
        self.tree.configure(yscrollcommand=self.vsb.set, xscrollcommand=self.hsb.set)
        self.tree.grid(row=0, column=0, rowspan=46, columnspan=50, sticky="nsew")
        self.vsb.pack(side="right", fill="y")
        self.hsb.pack(side="bottom", fill="x")

        self.filter_label = ttk.Label(self.bottom, text='Options', font=("Helvetica", 14))
        self.filter_desc_label = ttk.Label(self.bottom, text='(Filter conversations based on your input)', font=("", 9))
        self.filter_label.grid(row=1, column=0, rowspan=1, columnspan=3, sticky="nsw")
        self.filter_desc_label.grid(row=1, column=1, rowspan=1, columnspan=3, sticky="nsw")

        # scale for participants
        self.min_participants_label = ttk.Label(self.bottom, text='Minimum participants:', font=("", 9))
        self.max_participants_label = ttk.Label(self.bottom, text='Maximum participants:', font=("", 9))
        self.min_participants = tk.Scale(self.bottom, from_=2, to=10, orient="horizontal", resolution=1)
        self.max_participants = tk.Scale(self.bottom, from_=2, to=10, orient="horizontal", resolution=1)
        self.max_participants.set(10)
        self.min_participants_label.grid(row=2, column=0, rowspan=1, columnspan=1, padx=3, pady=3, sticky="ew")
        self.max_participants_label.grid(row=3, column=0, rowspan=1, columnspan=1, padx=3, pady=3, sticky="ew")
        self.min_participants.grid(row=2, column=1, rowspan=1, columnspan=1, padx=3, pady=3, sticky="ew")
        self.max_participants.grid(row=3, column=1, rowspan=1, columnspan=1, padx=3, pady=3, sticky="ew")
        # scale for turns
        self.min_turns_label = ttk.Label(self.bottom, text='Minimum turns:', font=("", 9))
        self.max_turns_label = ttk.Label(self.bottom, text='Maximum turns:', font=("", 9))
        self.min_turns = tk.Scale(self.bottom, from_=2, to=10, orient="horizontal", resolution=1)
        self.max_turns = tk.Scale(self.bottom, from_=2, to=10, orient="horizontal", resolution=1)
        self.max_turns.set(10)
        self.min_turns_label.grid(row=2, column=3, rowspan=1, columnspan=1, padx=3, pady=3, sticky="ew")
        self.max_turns_label.grid(row=3, column=3, rowspan=1, columnspan=1, padx=3, pady=3, sticky="ew")
        self.min_turns.grid(row=2, column=4, rowspan=1, columnspan=1, padx=3, pady=3, sticky="ew")
        self.max_turns.grid(row=3, column=4, rowspan=1, columnspan=1, padx=3, pady=3, sticky="ew")
        # scale for neg threshold
        self.min_thres_label = ttk.Label(self.bottom, text='Minimum sentiment threshold:', font=("", 9))
        self.max_thres_label = ttk.Label(self.bottom, text='Maximum sentiment threshold:', font=("", 9))
        self.min_thres = tk.Scale(self.bottom, from_=-1, to=1, orient="horizontal", resolution=0.01)
        self.max_thres = tk.Scale(self.bottom, from_=-1, to=1, orient="horizontal", resolution=0.01)
        self.min_thres.set(-1)
        self.max_thres.set(1)
        self.min_thres_label.grid(row=2, column=5, rowspan=1, columnspan=1, padx=3, pady=3, sticky="ew")
        self.max_thres_label.grid(row=3, column=5, rowspan=1, columnspan=1, padx=3, pady=3, sticky="ew")
        self.min_thres.grid(row=2, column=6, rowspan=1, columnspan=1, padx=3, pady=3, sticky="ew")
        self.max_thres.grid(row=3, column=6, rowspan=1, columnspan=1, padx=3, pady=3, sticky="ew")
        # # button to update tree
        self.update_button = ttk.Button(self.bottom, text='Update', command=self.update_tree)
        self.update_button.grid(row=3, column=46, rowspan=1, columnspan=2, padx=3, pady=3, sticky="nesw")
        self.authenticate()
        self.conversation_queue = queue.Queue()
        threading.Thread(target=self.initialize_tree, daemon=True).start()
        self.max_participants_val = 10
        self.min_participants_val = 2
        self.min_turns_val = 2
        self.max_turns_val = 10
        self.min_thresval = -1
        self.max_thresval = 1
        self.update = True
        self.new_filter = False
        self.filter_loop = False
        self.convo_list = []

    def initialize_tree(self):
        t = True
        while t:
            if NewMenu.current_file is not None:
                threading.Thread(target=self.to_tree, daemon=True).start()
                threading.Thread(target=self.filter_convo, daemon=True).start()
                self.process_tweets()
                t = False

    def process_tweets(self):
        self.old_file = NewMenu.current_file
        self.convo_list = []
        with io.open(self.old_file, "r", encoding='utf8') as f:
            for line in f:
                if self.old_file is not NewMenu.current_file:
                    break
                self.get_conversation(self.twitter.get_status(id=int(line.rstrip())), [], [], [])

    def remove_pattern(self, input_txt, pattern):
        r = re.findall(pattern, input_txt)
        for i in r:
            input_txt = re.sub(i, '', input_txt)
        return input_txt

    def clean_tweets(self, lst):
        lst = np.vectorize(self.remove_pattern)(lst, "RT @[\w]*:")
        lst = np.vectorize(self.remove_pattern)(lst, "@[\w]*")
        lst = np.vectorize(self.remove_pattern)(lst, "https?://[A-Za-z0-9./]*")
        lst = np.core.defchararray.replace(lst, "[^a-zA-Z#]", " ")
        return lst

    def get_sentiment(self, tweet):
        tweettext = self.clean_tweets([tweet.text])
        if len(tweettext) > 1:
            tweettext = ' '.join(tweettext)
        else:
            tweettext = tweettext[0]
        sid = SentimentIntensityAnalyzer()
        score = sid.polarity_scores(tweettext)
        return score

    def get_conversation(self, tweet, convo, participants, sentiment):
        convo.append(tweet)
        participants.append(tweet.user.screen_name)
        sentiment.append(self.get_sentiment(tweet))
        try:
            # Check if tweet has a reply
            if tweet.in_reply_to_status_id and tweet.in_reply_to_status_id is not None:
                self.get_conversation(self.twitter.get_status(id=tweet.in_reply_to_status_id), convo, participants,
                                      sentiment)
            else:
                convo_info = {'tweets': convo, 'participants': len(set(participants)), 'turns': len(convo),
                              'sentiment': sentiment}
                self.conversation_queue.put(convo_info)
                self.convo_list.append(convo_info)
        except tweepy.error.TweepError:
            time.sleep(1)
            pass

    def to_tree(self):
        while True:
            try:
                conversation = self.conversation_queue.get(block=False)
                for i in range(len(conversation['tweets'])-1, -1, -1):
                    self.tree.insert('', 'end', text=(conversation['tweets'][i].user.screen_name,), values=(
                        conversation['tweets'][i].text, conversation['sentiment'][i]['compound'],))
                self.tree.insert('', 'end', text='')  # Conversation separator
            except queue.Empty:
                time.sleep(1)  # slow down next request
                pass

    def filter_convo(self):
        while True:
            if self.filter_loop:
                for convo in self.convo_list:
                    if self.new_filter:
                        with self.conversation_queue.mutex:
                            self.conversation_queue.queue.clear()
                        self.tree.delete(*self.tree.get_children())
                        self.new_filter = False
                        break
                    if self.valid_convo(convo):
                        self.conversation_queue.put(convo)
                    if convo == self.convo_list[-1]:
                        self.filter_loop = False
            else:
                time.sleep(1)

    def update_tree(self):
        if NewMenu.current_file is not None:
            if self.old_file is not NewMenu.current_file:
                threading.Thread(target=self.process_tweets, daemon=True).start()
            self.new_filter = True
            self.max_participants_val = self.max_participants.get()
            self.min_participants_val = self.min_participants.get()
            self.min_turns_val = self.min_turns.get()
            self.max_turns_val = self.max_turns.get()
            self.min_thresval = self.min_thres.get()
            self.max_thresval = self.max_thres.get()
            self.filter_loop = True
        else:
            messagebox.showerror("Error: File not found", "Please select a valid File")

    def valid_convo(self, convo_info):
        valid = True
        if not (self.max_participants_val >= convo_info['participants'] >= self.min_participants_val):
            valid = False
        if not (self.max_turns_val >= convo_info['turns'] >= self.min_turns_val):
            valid = False
        for tweet_sent in convo_info['sentiment']:
            if not(self.max_thresval >= tweet_sent['compound'] >= self.min_thresval):
                valid = False
        return valid

    def authenticate(self):
        with io.open('credentials.txt', 'r', encoding='utf8') as file:
            credentials = [x.split('\n') for x in file]
            # Authenticate to Twitter
            auth = tweepy.OAuthHandler(credentials[0][0], credentials[1][0])
            auth.set_access_token(credentials[2][0], credentials[3][0])
            self.twitter = tweepy.API(auth)  # test authentication


if __name__ == "__main__":
    root = tk.Tk()  # Create root window
    NewMenu(root)  # Create menu
    tweet_queue = queue.Queue()
    # Configure grid
    rows = 0
    while rows < 50:
        root.rowconfigure(rows, weight=1)
        root.columnconfigure(rows, weight=1)
        rows += 1
    app = MainWindow(root)
    app.grid(row=0, column=0, rowspan=50, columnspan=50, padx=10, pady=10, sticky="nsew")
    root.geometry("1000x500")
    root.mainloop()  # Call event loop
