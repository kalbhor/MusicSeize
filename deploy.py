from flask import Flask, render_template, request, flash, \
                  url_for, send_file, after_this_request, redirect, \
                  session

from musictools.musicnow import MusicNow
from musictools.MusicRepair import MusicRepair
import sys
import logging
import os
import binascii
from collections import OrderedDict



# Initialize the Flask application
app = Flask(__name__)
app.secret_key = binascii.hexlify(os.urandom(24))
app.logger.addHandler(logging.StreamHandler(sys.stdout))
app.logger.setLevel(logging.ERROR)

def download_song(input_title, input_url):
    song = MusicNow()
    song.download_song(input_url, input_title, 'tmp/')
    artist, album, song_title, albumart, error = MusicRepair.get_details_spotify(input_title)
    print("input: " + input_title)
    print("somg:" + song_title)
    album_src = MusicRepair.add_albumart('tmp/'+input_title + '.mp3', song_title, albumart)
    MusicRepair.add_details('tmp/'+input_title + '.mp3', song_title, artist, album)

    result = {
    'artist': artist,
    'album' : album,
    'song' : song_title,
    'art': album_src,
    }

    return input_title + '.mp3', song_title, result

# Define a route for the default URL, which loads the form
@app.route('/')
def index():
    return render_template('form_submit.html')

@app.route('/songlist/', methods=['POST'])
def songlist():
    song_name = request.form['songname']
    song = MusicNow()
    youtube_list = song.get_url(song_name)
    titles = list(youtube_list.keys())[:7]
    urls = list(youtube_list.values())[:7]

    return render_template('form_action.html', titles=titles, urls=urls)


@app.route('/process/', methods=['POST'])
def process():
    if not os.path.exists('/tmp'):
        os.mkdirs('/tmp')
    input_title = request.form['title']
    input_url = request.form['url']
    file_path, song_title, result = download_song(input_title, input_url)

    return render_template('process.html', path=file_path, song=song_title, result=result)

@app.route('/download/<path>/<song>/', methods=['POST','GET'])
def download(path=None, song=None):
    return send_file('tmp/'+path, as_attachment=True, attachment_filename=song+'.mp3')

if __name__=='__main__':
    app.run()
