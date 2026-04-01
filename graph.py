from __future__ import annotations
import csv
from collections import deque, Counter
from typing import Any
import math
import itertools
import struct
import os

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
    popularity: float
    year: float
    genre: str
    dance: float
    energy: float
    key: float
    loud: float
    mode: float
    speech: float
    acoustic: float
    instrument: float
    live: float
    valence: float
    tempo: float
    duration: float
    time_signature: float
    neighbours: dict[str, float]

    def __init__(self, artist, name, popularity, year, genre, dance, energy, key, loud, mode, speech, acoustic,
                 instrument, live, valence, tempo, duration, time_signature):
        self.name = f"{name} - {artist}"
        self.artist = artist
        self.popularity = float(popularity)
        self.year = float(year)
        self.genre = genre
        self.dance = float(dance)
        self.energy = float(energy)
        self.key = float(key)
        self.loud = float(loud)
        self.mode = float(mode)
        self.speech = float(speech)
        self.acoustic = float(acoustic)
        self.instrument = float(instrument)
        self.live = float(live)
        self.valence = float(valence)
        self.tempo = float(tempo)
        self.duration = float(duration)
        self.time_signature = float(time_signature)
        self.neighbours = {}

    def get_features(self) -> list[float]:
        return [
            self.popularity, self.year, self.dance, self.energy, self.key, self.loud,
            self.mode, self.speech, self.acoustic, self.instrument,
            self.live, self.valence, self.tempo, self.duration, self.time_signature
        ]


def _calculate_song_distance_sq(song1: _Song, song2: _Song) -> float:
    genre_dist_sq = 0.0 if song1.genre == song2.genre else 1.0
    return (
            (song1.popularity - song2.popularity) ** 2 +
            (song1.year - song2.year) ** 2 +
            (song1.key - song2.key) ** 2 +
            (song1.loud - song2.loud) ** 2 +
            (song1.tempo - song2.tempo) ** 2 +
            (song1.duration - song2.duration) ** 2 +
            (song1.time_signature - song2.time_signature) ** 2 +
            (song1.dance - song2.dance) ** 2 +
            (song1.energy - song2.energy) ** 2 +
            (song1.mode - song2.mode) ** 2 +
            (song1.speech - song2.speech) ** 2 +
            (song1.acoustic - song2.acoustic) ** 2 +
            (song1.instrument - song2.instrument) ** 2 +
            (song1.live - song2.live) ** 2 +
            (song1.valence - song2.valence) ** 2 +
            genre_dist_sq
    )


class Graph:
    _songs: dict[Any, _Song]
    _year_range: list[float]
    _key_range: list[float]
    _loudness_range: list[float]
    _tempo_range: list[float]
    _duration_range: list[float]
    _time_sig_range: list[float]
    genres: set[str]
    parent_genres: list[str]
    threshold: float

    def __init__(self, dataset: str, threshold: float, build_edges: bool = True):
        self._songs = {}
        self._year_range = []
        self._key_range = []
        self._loudness_range = []
        self._tempo_range = []
        self._duration_range = []
        self._time_sig_range = []
        self.genres = set()
        self.threshold = threshold
        self.parent_genres = [
            "Pop", "Rock", "Electronic/Dance", "Hip-Hop/Soul", "Metal/Punk",
            "Jazz/Blues", "Classical/Acoustic", "Folk/Country", "World/Regional", "Mood/Other"
        ]

        self._load_songs(dataset)

        if build_edges:
            self._make_connections()
            self._save_state()

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
                song_data[2] = float(song_data[2]) / 100

                original_genre = song_data[4]
                song_data[4] = PARENT_GENRE_MAPPING.get(original_genre, "Mood/Other")

                new_song = _Song(*song_data)
                self._songs[new_song.name] = new_song
                curr_song = self._songs[new_song.name]

                years.append(curr_song.year)
                keys.append(curr_song.key)
                louds.append(curr_song.loud)
                tempos.append(curr_song.tempo)
                durations.append(curr_song.duration)
                time_sigs.append(curr_song.time_signature)

        self._year_range = [min(years), max(years)]
        self._key_range = [min(keys), max(keys)]
        self._loudness_range = [min(louds), max(louds)]
        self._tempo_range = [min(tempos), max(tempos)]
        self._duration_range = [min(durations), max(durations)]
        self._time_sig_range = [min(time_sigs), max(time_sigs)]

        for song in self._songs.values():
            self._process_song_data(song)

    def _make_connections(self):
        threshold_sq = self.threshold ** 2

        for song1, song2 in itertools.combinations(list(self._songs.values()), 2):
            dist_sq = _calculate_song_distance_sq(song1, song2)
            if dist_sq < threshold_sq:
                exact_dist = math.sqrt(dist_sq)
                song1.neighbours[song2.name] = exact_dist
                song2.neighbours[song1.name] = exact_dist

    def _process_song_data(self, song: _Song):
        song.year = normalize(song.year, self._year_range)
        song.key = normalize(song.key, self._key_range)
        song.loud = normalize(song.loud, self._loudness_range)
        song.tempo = normalize(song.tempo, self._tempo_range)
        song.duration = normalize(song.duration, self._duration_range)
        song.time_signature = normalize(song.time_signature, self._time_sig_range)

    def _save_state(self) -> None:
        song_names = list(self._songs.keys())
        name_to_idx = {name: i for i, name in enumerate(song_names)}

        with open("graph.bin", "wb") as f:
            for i, name in enumerate(song_names):
                song = self._songs[name]
                for neighbor, dist in song.neighbours.items():
                    if name < neighbor:
                        binary_data = struct.pack('iif', i, name_to_idx[neighbor], dist)
                        f.write(binary_data)

    def load_save(self):
        song_names = list(self._songs.keys())
        edge_size = struct.calcsize('iif')

        with open("graph.bin", "rb") as f:
            while chunk := f.read(edge_size):
                u_idx, v_idx, dist = struct.unpack('iif', chunk)
                u_name, v_name = song_names[u_idx], song_names[v_idx]

                self._songs[u_name].neighbours[v_name] = dist
                self._songs[v_name].neighbours[u_name] = dist

    def add_song(self, song: _Song) -> None:
        self._process_song_data(song)

        threshold_sq = self.threshold ** 2

        for i in self._songs.values():
            dist_sq = _calculate_song_distance_sq(song, i)

            if dist_sq < threshold_sq:
                exact_dist = math.sqrt(dist_sq)
                song.neighbours[i.name] = exact_dist
                i.neighbours[song.name] = exact_dist

        self._songs[song.name] = song

    def recommend(self, songs: list[_Song], num_req: int = 10) -> list[tuple[float, _Song]]:
        if not songs:
            return []

        num_seeds = len(songs)

        genres = [song.genre for song in songs]
        most_common_genre = Counter(genres).most_common(1)[0][0]

        seed_features = [song.get_features() for song in songs]

        avg_features = [sum(col) / num_seeds for col in zip(*seed_features)]

        avg_song = _Song(
            "Master", "Centroid",
            avg_features[0],
            avg_features[1],
            most_common_genre,
            *avg_features[2:]
        )

        queue = deque([(seed.name, 0) for seed in songs])
        visited = set(seed.name for seed in songs)

        candidates = []
        curr_depth = 0
        threshold_sq = self.threshold ** 2

        while queue:
            curr_name, depth = queue.popleft()

            if depth > curr_depth:
                if len(candidates) >= num_req:
                    break
                curr_depth = depth

            curr_song = self._songs[curr_name]

            for neighbor_name in curr_song.neighbours:
                if neighbor_name not in visited:
                    visited.add(neighbor_name)
                    queue.append((neighbor_name, depth + 1))

                    neighbor_song = self._songs[neighbor_name]

                    dist_sq = _calculate_song_distance_sq(avg_song, neighbor_song)

                    if dist_sq < threshold_sq:
                        candidates.append((dist_sq, neighbor_song))

        candidates.sort(key=lambda x: x[0])

        top_matches = []
        for dist_sq, song in candidates[:num_req]:
            top_matches.append((math.sqrt(dist_sq), song))

        return top_matches

    def get_song(self, name: str) -> _Song | None:
        return self._songs.get(name)


def make_graph() -> Graph:
    dataset_file = "spotify_15k.csv"
    threshold = 0.75

    if os.path.exists("graph.bin"):
        print("Found save")
        graph = Graph(dataset_file, threshold, build_edges=False)
        graph.load_save()
    else:
        print("Binary file not found. Generating new graph.")
        graph = Graph(dataset_file, threshold)
        print("Graph generated and saved!")

    return graph


if __name__ == '__main__':
    graph = Graph("spotify_20k.csv", 0.7)
