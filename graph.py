from __future__ import annotations
import csv
from typing import Any
import math
import itertools

PARENT_GENRE_MAPPING = {
    'pop': 'Pop', 'indie-pop': 'Pop', 'power-pop': 'Pop', 'k-pop': 'Pop',
    'cantopop': 'Pop', 'pop-film': 'Pop',

    'rock': 'Rock', 'alt-rock': 'Rock', 'hard-rock': 'Rock', 'psych-rock': 'Rock',
    'rock-n-roll': 'Rock', 'ska': 'Rock', 'singer-songwriter': 'Rock', 'songwriter': 'Rock',

    'electronic': 'Electronic/Dance', 'dance': 'Electronic/Dance', 'electro': 'Electronic/Dance',
    'house': 'Electronic/Dance', 'techno': 'Electronic/Dance', 'edm': 'Electronic/Dance',
    'trance': 'Electronic/Dance', 'dubstep': 'Electronic/Dance', 'drum-and-bass': 'Electronic/Dance',
    'chicago-house': 'Electronic/Dance', 'detroit-techno': 'Electronic/Dance',
    'progressive-house': 'Electronic/Dance', 'minimal-techno': 'Electronic/Dance',
    'deep-house': 'Electronic/Dance', 'garage': 'Electronic/Dance', 'breakbeat': 'Electronic/Dance',
    'club': 'Electronic/Dance', 'hardstyle': 'Electronic/Dance', 'party': 'Electronic/Dance',
    'groove': 'Electronic/Dance', 'chill': 'Electronic/Dance',

    'hip-hop': 'Hip-Hop/Soul', 'soul': 'Hip-Hop/Soul', 'funk': 'Hip-Hop/Soul',
    'trip-hop': 'Hip-Hop/Soul', 'dub': 'Hip-Hop/Soul',

    'metal': 'Metal/Punk', 'heavy-metal': 'Metal/Punk', 'death-metal': 'Metal/Punk',
    'black-metal': 'Metal/Punk', 'metalcore': 'Metal/Punk', 'hardcore': 'Metal/Punk',
    'grindcore': 'Metal/Punk', 'punk': 'Metal/Punk', 'punk-rock': 'Metal/Punk',
    'emo': 'Metal/Punk', 'goth': 'Metal/Punk', 'industrial': 'Metal/Punk',

    'jazz': 'Jazz/Blues', 'blues': 'Jazz/Blues',

    'classical': 'Classical/Acoustic', 'opera': 'Classical/Acoustic', 'piano': 'Classical/Acoustic',
    'acoustic': 'Classical/Acoustic', 'new-age': 'Classical/Acoustic', 'ambient': 'Classical/Acoustic',

    'country': 'Folk/Country', 'folk': 'Folk/Country',

    'samba': 'World/Regional', 'tango': 'World/Regional', 'salsa': 'World/Regional',
    'forro': 'World/Regional', 'sertanejo': 'World/Regional', 'dancehall': 'World/Regional',
    'afrobeat': 'World/Regional', 'spanish': 'World/Regional', 'french': 'World/Regional',
    'swedish': 'World/Regional', 'german': 'World/Regional', 'indian': 'World/Regional',

    'comedy': 'Mood/Other', 'show-tunes': 'Mood/Other', 'sleep': 'Mood/Other',
    'sad': 'Mood/Other', 'romance': 'Mood/Other', 'guitar': 'Mood/Other'
}


def normalize(value, r):
    return (float(value) - r[0]) / (r[1] - r[0]) if r[1] != r[0] else 0.0


class _Song:
    artist: str
    name: str
    popularity: str | float
    year: str | float
    genre: str | float
    dance: str | float
    energy: str | float
    key: str | float
    loud: str | float
    mode: str | float
    speech: str | float
    acoustic: str | float
    instrument: str | float
    live: str | float
    valence: str | float
    tempo: str | float
    duration: str | float
    time_signature: str | float

    neighbours: dict[_Song, float]

    def __init__(self, artist,
                 name,
                 popularity,
                 year,
                 genre,
                 dance,
                 energy,
                 key,
                 loud,
                 mode,
                 speech,
                 acoustic,
                 instrument,
                 live,
                 valence,
                 tempo,
                 duration,
                 time_signature):
        self.name = name
        self.artist = artist
        self.popularity = popularity
        self.year = year
        self.genre = genre
        self.dance = dance
        self.energy = energy
        self.key = key
        self.loud = loud
        self.mode = mode
        self.speech = speech
        self.acoustic = acoustic
        self.instrument = instrument
        self.live = live
        self.valence = valence
        self.tempo = tempo
        self.duration = duration
        self.time_signature = time_signature

        self.neighbours = {}


def _calculate_song_distance(song1: _Song, song2: _Song) -> float:
    genre_dist_sq = 0.0 if song1.genre == song2.genre else 1.0

    return math.sqrt(
        (song1.year - song2.year) ** 2 + (song1.key - song2.key) ** 2 + (song1.loud - song2.loud) ** 2 + (
                    song1.tempo - song2.tempo) ** 2 + (song1.duration - song2.duration) ** 2 + (
                    song1.time_signature - song2.time_signature) ** 2 + genre_dist_sq)


class _Graph:
    _songs: dict[Any, _Song]
    _year_range: list[float]
    _key_range: list[float]
    _loudness_range: list[float]
    _tempo_range: list[float]
    _duration_range: list[float]
    _time_sig_range: list[float]
    genres: set[str]
    parent_genres: list[str]

    def __init__(self, dataset: str):
        self._songs = {}
        self._year_range = []
        self._key_range = []
        self._loudness_range = []
        self._tempo_range = []
        self._duration_range = []
        self._time_sig_range = []
        self.genres = set()
        self.threshold = 0.5

        self._load_songs(dataset)
        self._make_connections()

    def _load_songs(self, dataset: str):
        years = []
        keys = []
        louds = []
        tempos = []
        durations = []
        time_sigs = []

        with open(dataset, 'r', encoding='utf-8') as songs:
            reader = csv.reader(songs)
            next(reader, None)

            for song_data in reader:
                song_data.pop(0)
                song_data.pop(2)
                song_data[2] = float(song_data[2]) / 100

                original_genre = song_data[4]
                song_data[4] = PARENT_GENRE_MAPPING.get(original_genre, "Mood/Other")

                self._songs[song_data[1]] = _Song(*song_data)
                curr_song = self._songs[song_data[1]]
                self.genres.add(curr_song.genre)

                years.append(float(curr_song.year))
                keys.append(float(curr_song.key))
                louds.append(float(curr_song.loud))
                tempos.append(float(curr_song.tempo))
                durations.append(float(curr_song.duration))
                time_sigs.append(float(curr_song.time_signature))

        self._year_range = [min(years), max(years)]
        self._key_range = [min(keys), max(keys)]
        self._loudness_range = [min(louds), max(louds)]
        self._tempo_range = [min(tempos), max(tempos)]
        self._duration_range = [min(durations), max(durations)]
        self._time_sig_range = [min(time_sigs), max(time_sigs)]

        for song in self._songs.values():
            self._process_song_data(song)

    def _make_connections(self):
        songs_list = list(self._songs.values())

        for song1, song2 in itertools.combinations(songs_list, 2):
            dist = _calculate_song_distance(song1, song2)

            if dist < self.threshold:
                song1.neighbours[song2] = dist
                song2.neighbours[song1] = dist

    def _process_song_data(self, song: _Song):
        song.year = normalize(song.year, self._year_range)
        song.key = normalize(song.key, self._key_range)
        song.loud = normalize(song.loud, self._loudness_range)
        song.tempo = normalize(song.tempo, self._tempo_range)
        song.duration = normalize(song.duration, self._duration_range)
        song.time_signature = normalize(song.time_signature, self._time_sig_range)


if __name__ == '__main__':
    graph = _Graph("spotify_data.csv")
