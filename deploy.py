"""
A simple flask application built for a webapp that provides
.mp3 files with metadata.
The heart of this webapp is based on musictools - A library specifically
built for this webapp. Musictools handles downloading the music from youtube
and handles metadata by searching from spotify and attaching using mutagen.
spotify requests are handled by spotipy
youtube downloading is handled by youtube-dl
Tests for this flask app are mostly trivial (I know testing is important)
musictools is the core application and it is tested.
I am very sorry for the pathetic html code in the templates. I'm not a 
frontend person.
"""

import sys
import logging
import os
import binascii
from musictools import musictools
from flask_sqlalchemy import SQLAlchemy
from flask import Flask, render_template, request, \
                  url_for, send_file, after_this_request

##########################################################################
############################# Configurations #############################
##########################################################################

app = Flask(__name__)

app.secret_key = binascii.hexlify(os.urandom(24))

file_handler = logging.StreamHandler()
file_handler.setLevel(logging.WARNING)
app.logger.addHandler(file_handler)

app.config['SQLALCHEMY_DATABASE_URI'] = os.environ['DATABASE_URL'] 
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False


##########################################################################
############################# Database ###################################
##########################################################################

db = SQLAlchemy(app)

class Visit(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    count = db.Column(db.Integer)
    song_name = db.Column(db.String)

    def __init__(self):
        self.count = 0


##########################################################################
########################## Flask Routes ##################################
##########################################################################

@app.route('/')
def index():
    """
    Home page, with a form that accepts song name as query
    and searches song on youtube.com
    """

    v = Visit.query.first()

    return render_template('index.html', count=v.count, song_name=v.song_name)


@app.route('/songlist/', methods=['POST'])
def songlist():
    """
    Searches query on youtube.com and displays on webpage.
    Music titles are represented as radio buttons allowing
    the user to choose 1 song to download.
    """

    song_name = request.form['songname']
    youtube_list = musictools.get_song_urls(song_name) # youtube_list is an ordered dict

    return render_template('form_action.html', youtube_list=youtube_list[:5])


@app.route('/process/', methods=['POST'])
def process():
    """
    Process the query and download song on server
    and call download_song method to handle downloading
    and metadata extraction & attaching.
    """
    print('Started process')
    sys.stdout.flush()
    if not os.path.exists('/tmp'):
        os.mkdir('/tmp')

    input_title = request.form['title']
    input_url = request.form['url']
    file_path, result = download_song(input_title, input_url)

    @after_this_request
    def write_to_db(response):
        v = Visit.query.first()
        v.count += 1             # Increment number of downloaded songs
        v.song_name = '{} - {}'.format(result['artist'], result['song']) 
        db.session.commit()

        return response

    return render_template('process.html', path=file_path, result=result)


@app.route('/download/<path>/<song>/', methods=['POST', 'GET'])
def download(path=None, song=None):
    """
    Explicitly delete song from server after user downloads it,
    (Heroku does this automatically after request expires or if user doesn't
    respond)
    """

    @after_this_request # Delete music file after request
    def delete_file(response):
        os.remove(os.path.join('tmp', path))
        return response

    return send_file(os.path.join('tmp',path), as_attachment=True, attachment_filename=str(song+'.mp3'))


@app.route('/about')
def about():
    """
    As the name suggests, a standard about page with
    details on the website
    """
    return render_template('about.html')

@app.route('/help')
def help():
    """
    As the name suggests, a standard help page 
    """
    return render_template('help.html')

@app.route('/caution')
def caution():
    """
    As the name suggests, a standard help page 
    """
    return render_template('caution.html')


##########################################################################
########################## Download Methods ##############################
##########################################################################

def download_song(input_title, input_url):
    """
    Method to use musictools to download song
    and add metadata, return details about song
    to display on webpage
    'tmp/' is a location where heroku allows storage for a single request.
    (tmp cannot be used for permanent storage)
    """

    musictools.download_song(input_url, input_title, dl_directory='tmp/')
    artist, album, song_title, albumart = musictools.get_metadata(input_title)
    album_src = musictools.add_albumart(input_title + '.mp3', song_title, albumart)
    musictools.add_metadata(input_title + '.mp3', song_title, artist, album)


    result = {
        'artist': artist,
        'album' : album,
        'song' : song_title,
        'art': album_src,
    } # Details to display on webpage


    return input_title + '.mp3', result


if __name__ == '__main__':
    app.run(debug=True) # For locally running the application

