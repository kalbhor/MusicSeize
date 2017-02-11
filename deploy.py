"""
A simple flask application built for a webapp that provides
.mp3 files with metadata. 

The heart of this webapp is based on musictools - A library specifically
built for this webapp. Musictools handles downloading the music from youtube
and handles metadata by searching from spotify and attaching using mutagen.

spotify requests are handled by spotify-dl
youtube downloading is handled by youtube-dl
"""

import sys
import logging
import os
import binascii
from musictools.MusicNow import MusicNow
from musictools.MusicRepair import MusicRepair
from flask import Flask, render_template, request, \
                  url_for, send_file, after_this_request

# Initialize the Flask application
app = Flask(__name__)
app.secret_key = binascii.hexlify(os.urandom(24))
app.logger.addHandler(logging.StreamHandler(sys.stdout))
app.logger.setLevel(logging.ERROR)

def download_song(input_title, input_url):
    """
    Method to use musictools to download song
    and add metadata, return details about song
    to display on webpage

    'tmp/' is a location where heroku allows storage for a single request.
    (tmp cannot be used for permanent storage)
    """
    song = MusicNow()
    song.download_song(input_url, input_title, location = 'tmp/')
    artist, album, song_title, albumart, error = MusicRepair.get_details_spotify(input_title)
    album_src = MusicRepair.add_albumart('tmp/'+input_title + '.mp3', song_title, albumart)
    MusicRepair.add_details('tmp/'+input_title + '.mp3', song_title, artist, album)

    result = {
    'artist': artist,
    'album' : album,
    'song' : song_title,
    'art': album_src,
    } # Details to display on webpage

    return input_title + '.mp3', song_title, result

# Define a route for the default URL, which loads the form
@app.route('/')
def index():
    """
    Home page, with a form that accepts song name as query
    and searches song on youtube.com
    """
    return render_template('index.html')

@app.route('/about')
def about():
    """
    As the name suggests, a standard about page with 
    details on the website
    """
    return render_template('about.html')

@app.route('/songlist/', methods=['POST'])
def songlist():
    """
    Searches query on youtube.com and displays on webpage.
    Uses MusicNow from MusicTools. Music titles are represented 
    as radio buttons allowing the user to choose 1 song to download
    """
    song_name = request.form['songname']
    song = MusicNow()
    youtube_list = song.get_url(song_name) # youtube_list is an ordered dict
    titles = list(youtube_list.keys())
    urls = list(youtube_list.values())

    return render_template('form_action.html', titles=titles, urls=urls)


@app.route('/process/', methods=['POST'])
def process():
    """
    Process the query and download song on server
    and call download_song method to handle downloading
    and metadata extraction & attaching.
    """
    if not os.path.exists('/tmp'):
        os.mkdirs('/tmp')
    input_title = request.form['title']
    input_url = request.form['url']
    file_path, song_title, result = download_song(input_title, input_url)

    return render_template('process.html', path=file_path, song=song_title, result=result)

@app.route('/download/<path>/<song>/', methods=['POST','GET'])
def download(path=None, song=None):
    """
    Explicitly delete song from server after user downloads it,
    (Heroku does this automatically after request expires or if user doesn't 
    respond)
    """
    @after_this_request
    def delete_file(response):
        try:
            os.remove(os.path.join('tmp','{}'.format(path)))
        except Exception as e:
            print(e)
        return response

    return send_file('tmp/'+path, as_attachment=True, attachment_filename=song+'.mp3')


if __name__=='__main__':
    app.run() # For locally running the application


