import os
import sys
import subprocess
import heapq
import twitter
import ConfigParser
from RepeatedTimer import RepeatedTimer as set_interval

config = ConfigParser.SafeConfigParser()
config.read('settings.cfg')

credentials = dict(config.items('credentials'))
top_since = long(config.get('since', 'top'))
mentions_since = long(config.get('since', 'mentions'))


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

T = twitter.Api(**credentials)
points = [
    (17, 77), (44, 77), (77, 77), (119, 77),
    (159, 82), (196, 82), (228, 82), (260, 82)
]
last_text = ''
q = PriorityQueue()


def make_tat():
    if len(q):
        text = q.pop()
    else:
        latest = T.GetUser(screen_name='knuckle_tat').GetStatus()
        text = latest.text

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
        command.extend(['-draw', 'text %i,%i %s' % (p[0], p[1], t)])
    command.append(out_image)
    subprocess.call(command)
    return text, out_image


def post_tat(text, image):
    T.PostMedia(text, image)


def get_top():
    global q
    tweets = T.GetSearch("from:knuckle_tat", result_type='recent',
                         include_entities=False, count=100)
    top = [
        {"text": t.text, "faves": t.favorite_count, "rts": t.retweet_count}
        for t in tweets if t.favorite_count or t.retweet_count
    ]
    for t in top:
        q.push(**t)
    sys.stdout.write("Current queue length: %i\n" % len(q))
    sys.stdout.flush()


def make_and_post():
    global last_text
    new_tat = make_tat()
    if new_tat[0] != last_text:
        post_tat(*new_tat)
        sys.stdout.write("DONE!\n")
    else:
        sys.stdout.write("DUPE! Not sending.\n")
    try:
        os.remove(new_tat[1])
    except IOError as e:
        sys.stderr.write(e.message)
        sys.stdout.write("Couldn't delete generated image.\n")
    sys.stdout.flush()

if __name__ == '__main__':
    print "Running from console..."
    get_top()
    make_and_post()
    top_timer = set_interval(60*210, get_top)
    post_timer = set_interval(60*60, make_and_post)
