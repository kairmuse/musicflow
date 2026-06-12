# 🛠️ MusicFlow - Guida per Sviluppatori

Questa guida ti aiuta a comprendere l'architettura di MusicFlow e come estenderla.

## 📐 Architettura dell'Applicazione

```
musicflow/
├── music_player_app.py       # Applicazione principale (GUI + logica)
├── utils.py                   # Funzioni helper e utilità
├── requirements.txt           # Dipendenze Python
├── setup.py                   # Configurazione del pacchetto
├── README.md                  # Documentazione utente
├── DEVELOPER.md              # Questa guida
└── .env.example              # Template configurazione
```

## 🏗️ Struttura del Codice

### Componenti Principali

#### 1. **MaterialColors** (Classe statica)
Definisce la palette di colori Material Design 3.

```python
class MaterialColors:
    PRIMARY = "#6F00D2"           # Colore primario
    ON_PRIMARY = "#FFFFFF"        # Testo sul colore primario
    PRIMARY_CONTAINER = "#EADDFF" # Contenitore primario
    # ... altri colori
```

**Come estendere:**
- Modifica i colori per creare un tema personalizzato
- Aggiungi nuovi colori per nuovi componenti

```python
class MaterialColors:
    PRIMARY = "#1f5e78"  # Blu personalizzato
    CUSTOM_COLOR = "#FF6B6B"  # Nuovo colore
```

#### 2. **MusicDatabase** (Gestione dati)
Gestisce tutte le operazioni di database SQLite.

**Metodi disponibili:**
- `add_song()` - Aggiunge una canzone
- `get_all_songs()` - Recupera tutte le canzoni
- `create_playlist()` - Crea una playlist
- `add_song_to_playlist()` - Aggiunge una canzone a una playlist

**Estensione - Aggiungere una nuova tabella:**

```python
def init_db(self):
    # ... codice esistente ...
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS favorites (
            id INTEGER PRIMARY KEY,
            song_id INTEGER UNIQUE,
            date_added TIMESTAMP,
            FOREIGN KEY(song_id) REFERENCES songs(id)
        )
    ''')
    conn.commit()

def add_favorite(self, song_id):
    conn = sqlite3.connect(self.db_path)
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO favorites (song_id, date_added)
        VALUES (?, datetime('now'))
    ''', (song_id,))
    conn.commit()
    conn.close()
```

#### 3. **SpotifyImporter** (API Integration)
Integra con l'API Spotify per l'importazione di playlist.

**Come estendere - Aggiungere supporto per artisti:**

```python
def get_artist_tracks(self, artist_id):
    """Recupera le tracce di un artista"""
    if not self.token:
        return []
    
    headers = {'Authorization': f'Bearer {self.token}'}
    url = f'https://api.spotify.com/v1/artists/{artist_id}/top/tracks'
    
    tracks = []
    try:
        response = requests.get(url, headers=headers, params={'market': 'IT'})
        response.raise_for_status()
        
        for track in response.json()['tracks']:
            tracks.append({
                'title': track['name'],
                'artist': ', '.join([a['name'] for a in track['artists']]),
                'album': track['album']['name'],
                'duration': track['duration_ms'] // 1000,
            })
        return tracks
    except Exception as e:
        print(f"Error: {e}")
        return []
```

#### 4. **YouTubeMusicImporter** (Download Audio)
Scarica musica da YouTube usando yt-dlp.

**Come estendere - Aggiungere supporto per altri formati:**

```python
@staticmethod
def download_audio(video_id, output_path="downloads", format="mp3"):
    """Scarica con formato personalizzato"""
    try:
        import yt_dlp
        
        Path(output_path).mkdir(exist_ok=True)
        
        audio_codec = {
            'mp3': {'key': 'FFmpegExtractAudio', 'preferredcodec': 'mp3', 'preferredquality': '192'},
            'opus': {'key': 'FFmpegExtractAudio', 'preferredcodec': 'opus', 'preferredquality': '128'},
            'm4a': {'key': 'FFmpegExtractAudio', 'preferredcodec': 'm4a', 'preferredquality': '256'},
        }
        
        ydl_opts = {
            'format': 'bestaudio/best',
            'postprocessors': [audio_codec.get(format, audio_codec['mp3'])],
            'outtmpl': os.path.join(output_path, '%(title)s.%(ext)s'),
            'quiet': False,
        }
        
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([f'https://www.youtube.com/watch?v={video_id}'])
        
        return True
    except Exception as e:
        print(f"Error: {e}")
        return False
```

#### 5. **MusicPlayer** (Interfaccia Principale)
La finestra principale dell'applicazione con tutta la GUI.

## 🎨 Come Personalizzare l'Interfaccia

### Cambiare Tema Colori

```python
class MaterialColors:
    PRIMARY = "#0D47A1"  # Blu scuro
    ON_PRIMARY = "#FFFFFF"
    PRIMARY_CONTAINER = "#BBDEFB"
    ON_PRIMARY_CONTAINER = "#0D47A1"
    SECONDARY = "#F57C00"  # Arancione
    # ... altri colori
```

### Aggiungere Nuovi Tab

```python
def init_ui(self):
    # ... codice esistente ...
    
    # Aggiungi nuovo tab
    favorites_tab = self.create_favorites_tab()
    self.tabs.addTab(favorites_tab, "❤️ Preferiti")

def create_favorites_tab(self):
    """Crea il tab dei brani preferiti"""
    widget = QWidget()
    layout = QVBoxLayout()
    
    self.favorites_list = QListWidget()
    self.favorites_list.itemDoubleClicked.connect(self.play_selected_song)
    layout.addWidget(self.favorites_list)
    
    widget.setLayout(layout)
    return widget
```

### Aggiungere Nuovi Pulsanti ai Controlli

```python
def create_player_controls(self):
    # ... codice esistente ...
    
    # Aggiungi nuovo pulsante
    self.favorite_btn = QPushButton("❤️ Preferito")
    self.favorite_btn.clicked.connect(self.toggle_favorite)
    button_layout.addWidget(self.favorite_btn)
```

## 🔧 Aggiungere Nuovi Streamers

### Esempio: Aggiungere Apple Music

```python
class AppleMusicImporter:
    """Importa playlist da Apple Music"""
    
    def __init__(self, token):
        self.token = token
        self.base_url = "https://api.music.apple.com/v1"
    
    def get_playlist_songs(self, playlist_id):
        """Recupera le canzoni da una playlist Apple Music"""
        headers = {
            'Authorization': f'Bearer {self.token}',
            'Music-User-Token': self.token
        }
        
        url = f"{self.base_url}/catalog/{{region}}/playlists/{playlist_id}/tracks"
        
        songs = []
        try:
            response = requests.get(url, headers=headers)
            response.raise_for_status()
            
            for item in response.json()['data']:
                track = item['attributes']
                songs.append({
                    'title': track['name'],
                    'artist': track['artistName'],
                    'album': track['albumName'],
                    'duration': track['durationInMillis'] // 1000,
                })
            
            return songs
        except Exception as e:
            print(f"Error: {e}")
            return []
```

## 📊 Aggiungere Funzionalità Avanzate

### 1. Equalizzatore Audio

```python
class AudioEqualizer:
    """Gestisce l'equalizzazione audio"""
    
    PRESETS = {
        'normal': [0, 0, 0, 0, 0],
        'bass': [8, 6, 4, 2, 0],
        'treble': [0, 2, 4, 6, 8],
        'vocal': [2, 4, 6, 4, 2],
    }
    
    def __init__(self):
        self.preset = 'normal'
        self.bands = self.PRESETS['normal']
    
    def apply_preset(self, preset_name):
        """Applica un preset dell'equalizzatore"""
        if preset_name in self.PRESETS:
            self.bands = self.PRESETS[preset_name]
            self.preset = preset_name
            return True
        return False
    
    def set_band(self, band: int, value: int):
        """Imposta il valore di una banda"""
        if 0 <= band < len(self.bands):
            self.bands[band] = value
            return True
        return False
```

### 2. Sistema di Statistiche

```python
class ListeningStats:
    """Traccia le statistiche di ascolto"""
    
    def __init__(self, db):
        self.db = db
        self.init_stats_table()
    
    def init_stats_table(self):
        """Crea la tabella per le statistiche"""
        conn = sqlite3.connect(self.db.db_path)
        cursor = conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS listening_history (
                id INTEGER PRIMARY KEY,
                song_id INTEGER,
                artist TEXT,
                play_date TIMESTAMP,
                duration_played INTEGER,
                FOREIGN KEY(song_id) REFERENCES songs(id)
            )
        ''')
        conn.commit()
        conn.close()
    
    def log_play(self, song_id, artist, duration_played):
        """Registra un ascolto"""
        conn = sqlite3.connect(self.db.db_path)
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO listening_history 
            (song_id, artist, play_date, duration_played)
            VALUES (?, ?, datetime('now'), ?)
        ''', (song_id, artist, duration_played))
        conn.commit()
        conn.close()
    
    def get_top_artists(self, days=30):
        """Ottiene gli artisti più ascoltati"""
        conn = sqlite3.connect(self.db.db_path)
        cursor = conn.cursor()
        cursor.execute('''
            SELECT artist, COUNT(*) as plays
            FROM listening_history
            WHERE play_date >= datetime('now', '-' || ? || ' days')
            GROUP BY artist
            ORDER BY plays DESC
            LIMIT 10
        ''', (days,))
        results = cursor.fetchall()
        conn.close()
        return results
```

### 3. Sincronizzazione Cloud

```python
class CloudSync:
    """Sincronizza la libreria con il cloud"""
    
    def __init__(self, api_key, user_id):
        self.api_key = api_key
        self.user_id = user_id
        self.base_url = "https://api.musicflow.cloud"
    
    def sync_library(self, songs):
        """Sincronizza la libreria"""
        headers = {
            'Authorization': f'Bearer {self.api_key}',
            'Content-Type': 'application/json'
        }
        
        payload = {
            'user_id': self.user_id,
            'songs': [
                {
                    'title': s['title'],
                    'artist': s['artist'],
                    'album': s['album'],
                    'duration': s['duration']
                }
                for s in songs
            ]
        }
        
        try:
            response = requests.post(
                f"{self.base_url}/sync",
                json=payload,
                headers=headers
            )
            response.raise_for_status()
            return True
        except Exception as e:
            print(f"Sync error: {e}")
            return False
```

## 🧪 Testing

### Test Unitari Semplici

```python
import unittest

class TestMusicDatabase(unittest.TestCase):
    
    def setUp(self):
        self.db = MusicDatabase(":memory:")
    
    def test_add_song(self):
        result = self.db.add_song(
            "Test Song",
            "Test Artist",
            "Test Album",
            180,
            "/path/to/file.mp3"
        )
        self.assertTrue(result)
    
    def test_get_all_songs(self):
        self.db.add_song("Song 1", "Artist 1", "Album 1", 180, "/path1.mp3")
        self.db.add_song("Song 2", "Artist 2", "Album 2", 200, "/path2.mp3")
        
        songs = self.db.get_all_songs()
        self.assertEqual(len(songs), 2)

if __name__ == '__main__':
    unittest.main()
```

## 🚀 Performance Tips

1. **Database**: Usa indici per campi frequentemente cercati
2. **Audio**: Usa codec compressi (MP3, Opus) per ridurre l'uso di RAM
3. **Threading**: Usa thread separati per operazioni lunghe
4. **Caching**: Cache i metadati frequentemente accessibili

## 📚 Risorse Utili

- [PyQt6 Documentation](https://doc.qt.io/)
- [Material Design 3](https://m3.material.io/)
- [SQLite Documentation](https://www.sqlite.org/docs.html)
- [Spotipy Docs](https://spotipy.readthedocs.io/)
- [yt-dlp Guide](https://github.com/yt-dlp/yt-dlp/wiki)

## 💡 Best Practices

1. **Usa le utility**: Sfrutta le funzioni in `utils.py`
2. **Gestione errori**: Sempre try/except per operazioni di rete
3. **Threading**: Non bloccare l'UI
4. **Database**: Sempre chiudi le connessioni
5. **Logging**: Usa il logger per debugging

## 🤝 Contribuire

Se vuoi contribuire al progetto:

1. Fork il repository
2. Crea un branch feature (`git checkout -b feature/AmazingFeature`)
3. Commit i cambiamenti (`git commit -m 'Add AmazingFeature'`)
4. Push al branch (`git push origin feature/AmazingFeature`)
5. Apri una Pull Request

---

**Buona codifica! 🚀**
