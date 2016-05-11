#! /usr/bin/python2
# -*- coding: utf-8 -*-

import os
import sys
import subprocess
from twitter import OAuth, Twitter
import argparse
import ConfigParser
from RepeatedTimer import RepeatedTimer as set_interval

parser = argparse.ArgumentParser(description='Manual @tatsillustrated')
req_group = parser.add_argument_group(title="Required")
req_group.add_argument(
    'text', metavar='TEXTHERE',
    help='Text to put on knuckles'
)

flags_group = parser.add_argument_group(title="Flags")
flags_group.add_argument(
    '-u', '--upload', action='store_const',
    const=True, default=False,
    help='Upload to twitter when done (default: False)'
)
flags_group.add_argument(
    '-c', '--cleanup', action='store_const',
    const=True, default=False,
    help='Delete image file when done (default: False)')

misc_group = parser.add_argument_group(title="Misc Options")
misc_group.add_argument(
    '-o', '--outfile', '--filename',
    default='next_tat.png', metavar='PATH',
    help='Output path/filename (default: next_tat.png)')

args = parser.parse_args()

config = ConfigParser.SafeConfigParser()
config.read('settings.cfg')
credentials_dict = dict(config.items('credentials'))
credentials = [
    credentials_dict.get('access_token_key'),
    credentials_dict.get('access_token_secret'),
    credentials_dict.get('consumer_key'),
    credentials_dict.get('consumer_secret')
        ]
points = [
    (17, 77), (44, 77), (77, 77), (119, 77),
    (159, 82), (196, 82), (228, 82), (260, 82)
]


def make_tat(text=None, out_image=None):
    text = text
    letters = text.replace(' ', '')
    sys.stdout.write(letters + '...')
    sys.stdout.flush()

    tat = zip(points, letters)
    out_image = out_image

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

if __name__ == '__main__':
    if args.upload:
        T = Twitter(auth=OAuth(*credentials))
    text = args.text or 'TEST ING!'
    out_image = args.outfile
    new_tat = make_tat(text, out_image)
    if args.upload:
        media_ids = upload_images(new_tat[1])
        T.statuses.update(status=new_tat[0], media_ids=",".join(media_ids))
    if args.cleanup:
        os.remove(out_image)
    sys.stdout.write("DONE!\n\n")
    sys.stdout.flush()
