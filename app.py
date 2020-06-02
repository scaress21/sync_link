import pandas as pd
import numpy as np
import requests
from bs4 import BeautifulSoup
import pickle
from flask import Flask, request, Response, render_template, jsonify

#Get Master from Deezer
def gather_deezer(song_s, artist_s):
        master_info = {}
        try:

            deez_url = f'https://api.deezer.com/search?q=artist:\"{artist_s}\" track:\"{song_s}\"'
            deezer_q = requests.get(deez_url)
            track = str(deezer_q.json()['data'][0]['id'])

            deezer_track = requests.get('https://api.deezer.com/track/' + track)
            data = deezer_track.json()


            master_info['Master'] = 'Master Info from Deezer'
            master_info['Recording Title'] = data['title']
            master_info['Artist'] = data['artist']['name']
            master_info['Album Title'] = data['album']['title']
            master_info['ISRC'] =  data['isrc']
            master_info['Release Date'] = data['release_date']
            master_info['Is Explicit?']= data['explicit_lyrics']
            master_info['BPM'] = data['bpm']
            master_info['Deezer Track ID'] = data['id']
            master_info['Link to Album on Deezer'] = data['album']['link']

            master_info['Album Art']= data['album']['cover_medium']
            master_df = pd.DataFrame([master_info])
            master_df.set_index('Master', inplace = True)


            return master_df.T

        except:
            return 'Could not find on Deezer.'



#Helper functions to clean import pub
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

#Pub Info from Lyric Freak
def gather_lyricfreak(search):
    pub_info = {}

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

        if  soup_2.find('div', {'class' : 'lf-hero__subtitle'}):
            album = soup_2.find('div', {'class' : 'lf-hero__subtitle'}).text
            pub_info['Album'] = album.split('album:\n')[1].strip().split(' ')[0]

        #Putting it into the dictionary
        pub_info['Publishing'] = 'Publishing Info from Lyric Freak'
        pub_info['Composition Title'] = clean_title(title)
        pub_info['Performed By'] = artist
        pub_info['Writers'] = writer.replace('Songwriters: ', '')
        pub_info['Publishers'] = clean_pub(pub)

        pub_df = pd.DataFrame([pub_info])

        pub_df.set_index('Publishing', inplace = True)

        return pub_df.T

    except:
        return f'Could not find on Lyric Freak.'

#Genius Lyric Embed
def gather_genius(search):
    from credentials import genius
    header = {'Authorization' : f'Bearer {genius}'}

    res = requests.get('https://api.genius.com/search?q=' + search, headers = header)


    song = res.json()['response']['hits'][0]['result']['api_path']
    res2 = requests.get('https://api.genius.com' + song, headers = header)
    embed = res2.json()['response']['song']['embed_content']

    return embed

from credentials import s_key, ss_key

#Spotify auth
def auth(key, sec):

    authorize = 'https://accounts.spotify.com/api/token'
    param = {
    "Content-Type": "application/x-www-form-urlencoded",
    'grant_type' : 'client_credentials'
    }
    res = requests.post(authorize, auth = (s_key, ss_key), data = param)
    token = res.json()['access_token']

    return token

#Spotify search
def get_spotify(search):
    spotify_info = {}

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

        spotify_info['Artist'] = results['tracks']['items'][0]['artists'][0]['name']
        spotify_info['Song Title'] = results['tracks']['items'][0]['name']
        uri = results['tracks']['items'][0]['id']
        album_id = results['tracks']['items'][0]['album']['id']
        embed = f'<iframe src="https://open.spotify.com/embed/album/{album_id}" width="300" height="380" frameborder="0" allowtransparency="true" allow="encrypted-media"></iframe>'

        res_2 = requests.get(f'https://api.spotify.com/v1/audio-features/{uri}', headers = header)

        results_2 = res_2.json()

        spotify_info['Spotify'] = 'Spotify Audio Features'
        spotify_info['Danceeability'] = results_2['danceability']
        spotify_info['Energy'] = results_2['energy']
        spotify_info['Key'] = results_2['key']
        spotify_info['Loudness'] = results_2['loudness']
        spotify_info['Mode'] = results_2['mode']
        spotify_info['Speechiness'] = results_2['speechiness']
        spotify_info['Acousticness'] = results_2['acousticness']
        spotify_info['Instrumentalness'] = results_2['instrumentalness']
        spotify_info['Liveness'] = results_2['liveness']
        spotify_info['Valence'] = results_2['valence']
        spotify_info['Tempo'] = results_2['tempo']
        spotify_info['Time Signature'] = results_2['time_signature']

    except:
        return 'Could not find on Spotify.'

    spotify_df = pd.DataFrame([spotify_info])

    spotify_df.set_index('Spotify', inplace = True)

    return spotify_df.T, embed


features = ['year', 'explicit',
       'n_writers', 'n_pub',
       's_dance', 's_energy', 's_key', 's_loudness', 's_mode',
       's_speech', 's_acoustic', 's_inst', 's_live', 's_valence', 's_tempo',
       's_time_sig']

#Sync Score
def sync_score(mast, pub, spot):
    cvec = pickle.load(open('./model/cvec.pkl', 'rb'))
    rf = pickle.load(open('./model/rf.pkl', 'rb'))


    pred_df = {}
    pred_df['year'] = mast.iloc[4, 0][:4]
    pred_df['explicit'] = int(mast.iloc[5, 0])
    pred_df['n_writers'] = len(pub.iloc[2, 0].split(','))
    pred_df['n_pub'] = len(pub.iloc[3, 0].split(','))


    pred_df['s_dance'] = spot.iloc[2, 0]
    pred_df['s_energy'] = spot.iloc[3, 0]
    pred_df['s_key']= spot.iloc[4, 0]
    pred_df['s_loudness']= spot.iloc[5, 0]
    pred_df['s_mode']= spot.iloc[6, 0]
    pred_df['s_speech']= spot.iloc[7, 0]
    pred_df['s_acoustic']= spot.iloc[8, 0]
    pred_df['s_inst']= spot.iloc[9, 0]
    pred_df['s_live']= spot.iloc[10, 0]
    pred_df['s_valence'] = spot.iloc[11, 0]
    pred_df['s_tempo'] = spot.iloc[12, 0]
    pred_df['s_time_sig'] = spot.iloc[13, 0]

    pred_df['text'] = mast.iloc[1, 0].lower() + " " + pub.iloc[2, 0] + " " + pub.iloc[3, 0]

    to_predict = pd.DataFrame([pred_df])
    vec = cvec.transform(to_predict['text'])
    x_text = pd.DataFrame(vec.toarray(),
                 columns=cvec.get_feature_names())
    X = pd.concat([x_text, to_predict[features]], axis = 1)
    score =  rf.predict_proba(X)[0][1]

    if score >= .50:
        return 'Syncable'

    else:
        return 'Not very syncable'

#Put it all together
def get_all(artist, title):
    master = gather_deezer(title, artist)

    if type(master) != str:
        title = master.iloc[0, 0].lower()
        artist = master.iloc[1, 0].lower()
        title_display = master.iloc[0, 0]
        artist_display = master.iloc[1, 0]
        search_new = title + ' ' + artist
        artwork = master.iloc[9, 0]

        genius_lyrics = gather_genius(search_new)

        publishing = gather_lyricfreak(search_new)

        spotify, embed = get_spotify(search_new)

        if (type(publishing != str)) and (type(spotify != str)):
            score = sync_score(master, publishing, spotify)
        else:
            score = 'Not enough info for Sync Score'

    else:
        title_display = "None"
        artist_display = "None"
        master =  "None"
        publishing = "None"
        genius_lyrics = "None"
        spotify = "None"
        score = "None"
        embed = "None"
        artwork = 'None'

    if master.iloc[5, 0] == False:
        master.iloc[5, 0] = 'No'
    else:
        master.iloc[5, 0] = 'Yes'

    return artwork, title_display, artist_display, master, publishing, genius_lyrics, spotify, score, embed


app = Flask('myApp')

@app.route('/')

def form():
    return render_template('form.html')

@app.route('/submit')

def submit():
    user_input = request.args

    art, title_display, artist_display, master, publishing, genius_lyrics, spotify, score, embed = get_all(user_input['artist'], user_input['title'])
    try:
        return render_template('results.html', master = master.iloc[0:8, :].to_html(), pub = publishing.to_html(), spot = spotify.to_html(), title_display = title_display, artist_display = artist_display, artwork=art, lyrics=genius_lyrics, embed = embed, score=score)
    except:
        return "Could not find"

if __name__ == '__main__':
    app.run(debug = True)
