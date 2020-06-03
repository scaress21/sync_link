import pandas as pd
import numpy as np
import requests
from bs4 import BeautifulSoup
import pickle
import musicbrainzngs
from flask import Flask, request, Response, render_template, jsonify

#Get Spotify Master and Audio Features
#First, Authorize
def auth(key, sec):
    from credentials import s_key, ss_key
    authorize = 'https://accounts.spotify.com/api/token'
    param = {
    "Content-Type": "application/x-www-form-urlencoded",
    'grant_type' : 'client_credentials'
    }
    res = requests.post(authorize, auth = (s_key, ss_key), data = param)
    token = res.json()['access_token']

    return token

def get_spotify(search):
    from credentials import s_key, ss_key

    spotify_info = {}
    audio = {}

    token = auth(s_key, ss_key)

    try:

        #Search parameters with the song plugged in
        params = {
        'q' : search,
        'type': 'track',
        'limit' : 5
        }

        #Header for authorization
        header = {'Authorization' : f'Bearer {token}'}

        #Search endpoint
        spotify_search = 'https://api.spotify.com/v1/search'

        #Make the request
        res = requests.get(spotify_search, headers = header, params = params)
        status = res.status_code

        results = res.json()

        spotify_info['Song Title'] = results['tracks']['items'][0]['name']
        spotify_info['Artist'] = results['tracks']['items'][0]['artists'][0]['name']
        spotify_info['Album'] = results['tracks']['items'][0]['album']['name']
        spotify_info['ISRC'] = results['tracks']['items'][0]['external_ids']['isrc']
        spotify_info['Release Date'] = results['tracks']['items'][0]['album']['release_date']
        spotify_info['Is Explicit?'] = results['tracks']['items'][0]['explicit']
        spotify_info['Track ID on Site'] = results['tracks']['items'][0]['id']
        spotify_info['Master'] = 'Spotify'


        isrc = results['tracks']['items'][0]['external_ids']['isrc']
        uri = results['tracks']['items'][0]['id']
        album_id = results['tracks']['items'][0]['album']['id']
        embed = f'<iframe src="https://open.spotify.com/embed/album/{album_id}" width="300" height="380" frameborder="0" allowtransparency="true" allow="encrypted-media"></iframe>'
        art = results['tracks']['items'][0]['album']['images'][1]['url']

        res_2 = requests.get(f'https://api.spotify.com/v1/audio-features/{uri}', headers = header)

        results_2 = res_2.json()

        audio['Spotify'] = 'Spotify Audio Features'
        audio['Danceability'] = results_2['danceability']
        audio['Energy'] = results_2['energy']
        audio['Key'] = results_2['key']
        audio['Loudness'] = results_2['loudness']
        audio['Mode'] = results_2['mode']
        audio['Speechiness'] = results_2['speechiness']
        audio['Acousticness'] = results_2['acousticness']
        audio['Instrumentalness'] = results_2['instrumentalness']
        audio['Liveness'] = results_2['liveness']
        audio['Valence'] = results_2['valence']
        audio['Tempo'] = results_2['tempo']
        audio['Time Signature'] = results_2['time_signature']

        res_3 = requests.get(f'https://api.spotify.com/v1/albums/{album_id}', headers = header)


        results_3 = res_3.json()
        spotify_info['Album UPC'] = results_3['external_ids']['upc']
        spotify_info['Label'] = results_3['label']

    except:
        return 'Could not find on Spotify.'


    search_term = spotify_info['Song Title'] + ' ' + spotify_info['Artist']

    return spotify_info, audio, embed, art, isrc, search_term

#Next, get pub from MusicBrainz
def get_musbrn(rec_isrc):
    musicbrainzngs.set_useragent('sync_link', '1.0', contact='synclink.io')
    result = musicbrainzngs.get_recordings_by_isrc(rec_isrc)

    try:
        mbid = result['isrc']['recording-list'][0]['id']

        result_2 = musicbrainzngs.get_recording_by_id(mbid, includes=['work-level-rels', 'work-rels'])
        title = result_2['recording']['title']


        work_id = result_2['recording']['work-relation-list'][0]['work']['id']

    except:
        mbid = result['isrc']['recording-list'][1]['id']

        result_2 = musicbrainzngs.get_recording_by_id(mbid, includes=['work-level-rels', 'work-rels'])
        title = result_2['recording']['title']


        work_id = result_2['recording']['work-relation-list'][0]['work']['id']


    result_3 = musicbrainzngs.get_work_by_id(work_id,
                                          includes=['annotation', 'aliases',
                                                   'artist-rels', 'label-rels',  'work-rels'])

    writer = []
    for i in result_3['work']['artist-relation-list']:
        if i['type'] == 'writer':
            writer.append(i['artist']['name'])

    n_writer = len(writer)

    pub = []
    for i in result_3['work']['label-relation-list']:
        if i['type'] == 'publishing':
            pub.append(i['label']['name'])

    n_pub = len(pub)

    result_4 = requests.get(f'https://musicbrainz.org/ws/2/work/{work_id}?fmt=json')
    iswc = result_4.json()['iswcs']

    if len(iswc) == 0:
        iswc = "-"

    pub = {
        'Composition Title' : title,
        'Writers' : ', '.join(writer),
        'Publishers' : ', '.join(pub),
        'ISWC' : ''.join(iswc),
        'Publishing' : 'MusicBrainz'
    }



    return pub, n_pub, n_writer

#Gather lyrics from lyrics
def gather_genius(search):
    from credentials import genius
    header = {'Authorization' : f'Bearer {genius}'}

    res = requests.get('https://api.genius.com/search?q=' + search, headers = header)


    song = res.json()['response']['hits'][0]['result']['api_path']
    res2 = requests.get('https://api.genius.com' + song, headers = header)
    embed = res2.json()['response']['song']['embed_content']

    return embed

#Score the model
features = ['year', 'explicit',
       'n_writers', 'n_pub',
       's_dance', 's_energy', 's_key', 's_loudness', 's_mode',
       's_speech', 's_acoustic', 's_inst', 's_live', 's_valence', 's_tempo',
       's_time_sig']

def sync_score(mast, pub, audio, publishers, writers):
    cvec = pickle.load(open('./model/cvec.pkl', 'rb'))
    rf = pickle.load(open('./model/rf.pkl', 'rb'))


    pred_df = {
    'year' : mast['Release Date'][:4],
    'explicit' : int(mast['Is Explicit?']),
    'n_writers' : writers,
    'n_pub' : publishers,
    's_dance' : audio['Danceability'],
    's_energy' : audio['Energy'],
    's_key' : audio['Key'],
    's_loudness' : audio['Loudness'],
    's_mode' : audio['Mode'],
    's_speech' : audio['Speechiness'],
    's_acoustic' : audio['Acousticness'],
    's_inst' : audio['Instrumentalness'],
    's_live': audio['Liveness'],
    's_valence' : audio['Valence'],
    's_tempo': audio['Tempo'],
    's_time_sig' : audio['Time Signature']
        }
    pred_df['text'] = mast['Artist'].lower() + " " + pub['Writers'] + " " + pub['Publishers']



    to_predict = pd.DataFrame([pred_df])
    vec = cvec.transform(to_predict['text'])
    x_text = pd.DataFrame(vec.toarray(),
                 columns=cvec.get_feature_names())
    X = pd.concat([x_text, to_predict[features]], axis = 1)
    score =  rf.predict_proba(X)[0][1]

    if score >= .20:
        return 'Syncable'

    else:
        return 'Not very syncable'

#More master info from Deezer
def get_deezer(song_s, artist_s):


    try:
        deez_url = f'https://api.deezer.com/search?q=artist:\"{artist_s}\" track:\"{song_s}\"'
        deezer_q = requests.get(deez_url)
        track = str(deezer_q.json()['data'][0]['id'])

        deezer_track = requests.get('https://api.deezer.com/track/' + track)
        data = deezer_track.json()

        al = str(data['album']['id'])
        deezer_album = requests.get('https://api.deezer.com/album/' + al)
        album = deezer_album.json()

        master_info = {'Song Title': data['title'],
                         'Artist': data['artist']['name'],
                         'Album': data['album']['title'],
                         'ISRC': data['isrc'],
                         'Release Date': data['release_date'],
                         'Is Explicit?': data['explicit_lyrics'],
                         'Track ID on Site': data['id'],
                         'Master': 'Deezer',
                         'Album UPC': album['upc'],
                         'Label': album['label']}
    except:

        master_info = {'Song Title': '-',
                     'Artist': '-',
                     'Album': '-',
                     'ISRC': '-',
                     'Release Date': '-',
                     'Is Explicit?': '-',
                     'Track ID on Site': '-',
                     'Master': 'Not Found on Deezer',
                     'Album UPC': '-',
                     'Label': '-'}




    return master_info

#More pub from LyricsFreak
def clean_title(song):
    song = song.replace('About', '').replace('Lyrics', '').replace('lyrics', '')
    try:
        song = song.split('–')[1]
    except:
        pass
    song = song.strip()
    return song

def clean_pub(string):
    try:
        string = string.split('©')[1]
        string = string.split('Lyrics')[0]
        if ', Inc.' in string:
            string = string.replace(', Inc.', '')
        if '\\n' in string:
            string = string.replace('\\n', '')
    except:
        pass
    return string.strip()

def gather_lyricfreak(search):

    try:
        base = 'https://www.lyricsfreak.com/search.php?q='
        query = search.replace('-', '').replace(' ', '%20')
        res = requests.get(base + query)
        soup = BeautifulSoup(res.content, 'lxml')
        song = soup.find('a', {'class': 'song'})
        url = song['href']

        res_2 = requests.get('https://www.lyricsfreak.com' + url)
        soup_2 = BeautifulSoup(res_2.content, 'lxml')

        title = soup_2.find('h2').text
        artist = soup_2.find('a', {'class' : 'song-page-conthead-link'}).text


        writer_pub = soup_2.find_all('div', {'class' : 'meta_l'})
        writer = writer_pub[0].text
        pub = writer_pub[1].text

        #Putting it into the dictionary
        pub_dict = {'Composition Title': clean_title(title),
             'Writers': writer.replace('Songwriters: ', ''),
             'Publishers': clean_pub(pub),
             'ISWC': '-',
             'Publishing': 'LyricsFreak'}

    except:
        pub_dict = {'Composition Title': '-',
             'Writers': '-',
             'Publishers': '-',
             'ISWC': '-',
             'Publishing': 'LyricsFreak'}

    return pub_dict

#Helper to combine the master/pub info
def to_df(spot, deez, mb, lf):
    master = pd.DataFrame([spot, deez]).set_index('Master')
    publishing = pd.DataFrame([mb, lf]).set_index('Publishing')

    #Clean up the explicit field to convent boolean
    exp_dict = {False : 'No', True : 'Yes'}

    master['Is Explicit?'] = master['Is Explicit?'].map(exp_dict)

    return master.T, publishing.T

#Put it all together
def get_all(artist, title):
    search = artist.lower() + ' ' + title.lower()

    #Check Spotify and get ISRC
    spot, audio, embed, art, isrc, search_new = get_spotify(search)

    #Also check Deezer
    deez = get_deezer(title, artist)

    #Get Pub info from Music Brainz
    mb, publishers, writers = get_musbrn(isrc)

    #And Pub from LyricsFreak
    lf = gather_lyricfreak(search_new)

    #Lyrics from Genius
    lyrics = gather_genius(search_new)

    #Get the Score
    score = sync_score(spot, mb, audio, publishers, writers)

    #Title/Artist to display
    title_display = spot['Song Title']
    artist_display = spot['Artist']

    master, publishing = to_df(spot, deez, mb, lf)

    return art, title_display, artist_display, master, publishing, lyrics, audio, score, embed

app = Flask('myApp')

@app.route('/')

def form():
    return render_template('form.html')

@app.route('/submit')

def submit():
    try:
        user_input = request.args

        art, title_display, artist_display, master, publishing, genius_lyrics, spotify, score, embed = get_all(user_input['artist'], user_input['title'])

        return render_template('results.html', master = master.iloc[0:10, :].to_html(), pub = publishing.to_html(), title_display = title_display, artist_display = artist_display, artwork=art, lyrics=genius_lyrics, embed = embed, score=score)
    except:
        return render_template('no_results.html')

@app.route('/no_results')

def no_results():
    return render_template('no_results.html')

@app.route('/resources')

def resources():
    return render_template('resources.html')

if __name__ == '__main__':
    app.run(debug = True)
