#! /usr/bin/python2
# -*- coding: utf-8 -*-

import os
import sys
import re
import subprocess
import heapq
from twitter import Twitter, OAuth
import ConfigParser
from RepeatedTimer import RepeatedTimer as set_interval

global top_since
global mentions_since

config = ConfigParser.SafeConfigParser()
config.read('settings.cfg')
re_mention = r'(?<![A-Z0-9])[0-9A-Z\?\!\.\-\/\$\%\&\@\#\*\(\)\:\;\_]{8}'
credentials_dict = dict(config.items('credentials'))
credentials = [
    credentials_dict.get('access_token_key'),
    credentials_dict.get('access_token_secret'),
    credentials_dict.get('consumer_key'),
    credentials_dict.get('consumer_secret')
        ]
top_since = config.getint('since', 'top')
mentions_since = config.getint('since', 'mentions')


# Slightly modified version of code from:
# David Beazley and Brian K. Jones.
# Python Cookbook (3rd Edition). O'Reilly Media.
class PriorityQueue:
    def __init__(self):
        self._queue = []
        self._index = 0

    def __len__(self):
        return len(self._queue)

    def push(self, text, faves, rts):
        heapq.heappush(self._queue, (-rts, -faves, self._index, text))
        self._index += 1

    def pop(self):
        return heapq.heappop(self._queue)[-1]

T = Twitter(auth=OAuth(*credentials))
points = [
    (17, 77), (44, 77), (77, 77), (119, 77),
    (159, 82), (196, 82), (228, 82), (260, 82)
]
q = PriorityQueue()


def make_tat(text=None):
    if text:
        text = text
    elif len(q):
        text = q.pop()
    else:
        latest = T.users.show(screen_name='knuckle_tat').get('status')
        text = latest.get('text')

    letters = text.replace(' ', '')
    sys.stdout.write(letters + '...')
    sys.stdout.flush()

    tat = zip(points, letters)
    out_image = 'next_tat.png'

    command = ['convert']
    command.append('knuckles.jpg')
    command.extend(['-fill', 'black'])
    command.extend(['-font', 'loveletter-typewriter.ttf'])
    command.extend(['-pointsize', '32'])
    for p, t in tat:
        command.extend(['-draw', 'text %i,%i \'%s\'' % (p[0], p[1], t)])
    command.append(out_image)
    subprocess.call(command)
    return text, out_image

def upload_images(*imgs):
    T_up = Twitter(domain='upload.twitter.com', auth=OAuth(*credentials))
    media_ids = []
    for img in imgs:
        with open(img, "rb") as imagefile:
            imagedata = imagefile.read()
        media_ids.append(T_up.media.upload(media=imagedata)["media_id_string"])
    return media_ids

def post_tat(text, image, reply_to=None):
    media_ids = upload_images(image)
    T.statuses.update(status=text, media_ids=",".join(media_ids), in_reply_to_status_id=str(reply_to))
    #print "Would tweet: \n",text,"  ",image,"  ",reply_to,"\n\n"

def get_top():
    global q
    global top_since
    tweets = T.search.tweets(q="from:knuckle_tat", result_type='recent',
                         include_entities=False, count=200, since_id=top_since).get('statuses')
    top = [
        {"text": t.get('text'), "faves": t.get('favorite_count'), "rts": t.get('retweet_count')}
        for t in tweets if t.get('favorite_count') or t.get('retweet_count')
    ]

    if len(top):
        for t in top:
            q.push(**t)
        top_since = long(tweets[0].get('id')) + 1
        config.set('since', 'top', str(top_since))
        with open('settings.cfg', 'wb') as configfile:
            config.write(configfile)
        sys.stdout.write("Current queue length: %i\n" % len(q))
        sys.stdout.flush()
    else:
        sys.stdout.write("Adding nothing to queue.\n")
        sys.stdout.flush()

def do_mentions():
    global q
    global mentions_since
    mentions = T.statuses.mentions_timeline(
        include_entities=False, count=200, since_id=mentions_since
    )
    sys.stdout.write("Found " + str(len(mentions)) + " mentions...\n")
    sys.stdout.flush()
    for m in mentions:
        if m.get('in_reply_to_status_id') and m.get('in_reply_to_screen_name') == 'knuckle_tat':
            #Get the status with that id, generate
            tweet = T.statuses.show(id=m.get('in_reply_to_status_id'))
            sys.stdout.write("They replied to knuckle_tat!\n")
            sys.stdout.flush()
            text = tweet.get('text') + " for @" + m.get('user').get('screen_name')
            make_and_post(text, m.get('id'))
        else:
            text = m.get('text').replace(' ','')
            found = re.search(re_mention, text)
            if found:
                text = (text[found.start():found.end()] +
                        " for @" + m.get('user').get('screen_name'))
                sys.stdout.write("They want us to make one!\n")
                sys.stdout.flush()
                make_and_post(text, m.get('id'))
    if len(mentions):
        mentions_since = long(mentions[0].get('id')) + 1
        config.set('since', 'mentions', str(mentions_since))
        with open('settings.cfg', 'wb') as configfile:
            config.write(configfile)


def make_and_post(text=None, reply_to=None):
    new_tat = make_tat(text)
    post_tat(*new_tat,reply_to=reply_to)
    sys.stdout.write("DONE!\n")
    sys.stdout.flush()
    try:
        os.remove(new_tat[1])
    except IOError as e:
        sys.stderr.write(e.message)
        sys.stdout.write("Couldn't delete generated image.\n")
    sys.stdout.flush()

if __name__ == '__main__':
    print "Running from console..."
    global mentions_since
    global top_since
    get_top()
    mentions_since = top_since
    # do_mentions()
    # make_and_post()
    mention_timer = set_interval(60*3, do_mentions)
    top_timer = set_interval(60*60*4, get_top)
    post_timer = set_interval(60*60*8, make_and_post)
