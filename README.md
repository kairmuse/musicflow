# 🎵 MusicFlow - Material Design 3 Music Player

Un'applicazione Python moderna per la gestione e riproduzione di musica con interfaccia Material Design 3 di Google.

## ✨ Caratteristiche

- 🎶 **Riproduzione musica locale** - Supporta MP3, WAV, FLAC, OGG, M4A
- ☁️ **Streaming e download** - Scarica musica da YouTube Music per ascolto offline
- 📱 **Material Design 3** - Interfaccia moderna e intuitiva seguendo le linee guida Google
- 📥 **Importazione playlist** - Importa playlist da:
  - Spotify
  - YouTube Music
- 🎵 **Gestione playlist** - Crea e organizza le tue playlist
- 📚 **Libreria musicale** - Database SQLite per la gestione della musica
- 🔍 **Ricerca e filtri** - Trova facilmente le tue canzoni

## 🔧 Requisiti di Sistema

- **Python 3.8+**
- **FFmpeg** (necessario per la conversione audio)
- **Git** (per clonare il repository)

### Installazione di FFmpeg

#### Windows:
```bash
# Con winget
winget install FFmpeg

# O scarica da: https://ffmpeg.org/download.html
```

#### macOS:
```bash
brew install ffmpeg
```

#### Linux (Ubuntu/Debian):
```bash
sudo apt-get install ffmpeg
```

#### Linux (Fedora/RHEL):
```bash
sudo dnf install ffmpeg
```

## 📦 Installazione

### 1. Clona il repository
```bash
git clone <repository-url>
cd musicflow
```

### 2. Crea un ambiente virtuale
```bash
# Windows
python -m venv venv
venv\Scripts\activate

# macOS/Linux
python3 -m venv venv
source venv/bin/activate
```

### 3. Installa le dipendenze
```bash
pip install -r requirements.txt
```

### 4. Configurazione API (Opzionale ma consigliato)

#### Per Spotify:
1. Vai a https://developer.spotify.com/
2. Crea un'app e ottieni `Client ID` e `Client Secret`
3. Crea un file `.env` nella directory principale:
```
SPOTIFY_CLIENT_ID=tuo_client_id
SPOTIFY_CLIENT_SECRET=tuo_client_secret
```

#### Per YouTube Music:
- L'app utilizza `yt-dlp` che non richiede autenticazione ufficiale
- Per maggiore stabilità, installa ffmpeg (vedi sopra)

## 🚀 Utilizzo

### Avvia l'applicazione
```bash
python music_player_app.py
```

### Funzioni principali

#### 📚 Libreria
- **Aggiungi Cartella**: Seleziona una cartella con file audio per caricarli nella libreria
- **Aggiorna**: Ricarica la libreria e rileva nuovi file
- **Doppio click**: Riproduci la canzone selezionata

#### 🎵 Playlist
- **Nuova Playlist**: Crea una nuova playlist personalizzata
- **Carica Playlist**: Seleziona una playlist per vederne le canzoni
- **Aggiungi Canzoni**: Trascina o seleziona canzoni per aggiungerle

#### 📥 Importa
- **Spotify**: Incolla l'URL di una playlist Spotify per importarla
- **YouTube Music**: Incolla l'URL di una playlist YouTube Music per importarla e scaricarla

#### ▶️ Controlli Riproduzione
- **Play/Pausa**: Avvia o metti in pausa la riproduzione
- **Precedente/Successivo**: Naviga tra le canzoni
- **Volume**: Regola il livello di volume
- **Progress bar**: Mostra il tempo attuale e totale

## 🎨 Material Design 3

L'applicazione implementa completamente le specifiche Material Design 3 di Google:

- **Colori primari**: Viola (#6F00D2) e derivati
- **Contrasti**: Conformi agli standard WCAG
- **Tipografia**: Font moderni con gerarchia visiva
- **Componenti**: Button, Card, TextField secondo le linee guida
- **Animazioni**: Transizioni fluide tra gli stati

## 📂 Struttura del Database

L'app utilizza SQLite con le seguenti tabelle:

### songs
```sql
- id (PRIMARY KEY)
- title
- artist
- album
- duration
- file_path (UNIQUE)
- downloaded (boolean)
- date_added (timestamp)
```

### playlists
```sql
- id (PRIMARY KEY)
- name (UNIQUE)
- description
- source (local, spotify, youtube)
- date_created (timestamp)
```

### playlist_songs
```sql
- playlist_id (FOREIGN KEY)
- song_id (FOREIGN KEY)
```

## 🛠️ Moduli Principali

### `MusicDatabase`
Gestisce tutte le operazioni del database SQLite:
- `add_song()` - Aggiunge una canzone
- `get_all_songs()` - Recupera tutte le canzoni
- `create_playlist()` - Crea una nuova playlist
- `add_song_to_playlist()` - Aggiunge una canzone a una playlist

### `SpotifyImporter`
Importa playlist da Spotify usando le API ufficiali:
- `authenticate()` - Effettua l'autenticazione OAuth
- `get_playlist_tracks()` - Recupera i brani di una playlist

### `YouTubeMusicImporter`
Importa e scarica playlist da YouTube Music:
- `get_playlist_videos()` - Recupera i video da una playlist
- `download_audio()` - Scarica l'audio di un video

### `AudioMetadataReader`
Legge i metadati dai file audio:
- `read_metadata()` - Estrae ID3 tags e informazioni

### `MusicPlayer`
Interfaccia principale dell'applicazione con:
- Gestione della libreria
- Controlli di riproduzione
- Gestione playlist
- Importazione streaming

## ⚙️ Configurazione Avanzata

### Cartelle di download
Per cambiare la cartella di download per YouTube Music, modifica in `music_player_app.py`:
```python
YouTubeMusicImporter.download_audio(video_id, output_path="my_downloads")
```

### Formato audio
Per cambiare il formato di download (default: MP3):
```python
'preferredcodec': 'mp3',  # Cambia in: opus, vorbis, aac, m4a
'preferredquality': '192',  # Qualità in kbps
```

### Database personalizzato
Per usare un database diverso:
```python
db = MusicDatabase(db_path="my_music.db")
```

## 🐛 Risoluzione Problemi

### Problema: "ModuleNotFoundError: No module named 'PyQt6'"
**Soluzione**: Assicurati di aver attivato l'ambiente virtuale e di aver installato i requisiti:
```bash
pip install -r requirements.txt
```

### Problema: Nessun suono durante la riproduzione
**Soluzione**: Controlla che pygame.mixer sia inizializzato correttamente:
```bash
python -c "import pygame; pygame.mixer.init(); print('OK')"
```

### Problema: Non riesco a importare da Spotify
**Soluzione**: 
1. Verifica di aver configurato le credenziali API
2. Controlla che l'URL sia corretto (deve essere un URL di playlist pubblica)
3. Verifica la connessione internet

### Problema: YouTube Music non scarica
**Soluzione**:
1. Verifica che `yt-dlp` sia aggiornato:
```bash
pip install --upgrade yt-dlp
```
2. Assicurati che FFmpeg sia installato correttamente
3. Controlla che l'URL sia valido

## 🔐 Privacy e Sicurezza

- Le credenziali API sono memorizzate localmente nel file `.env`
- Il database è memorizzato localmente (`music_library.db`)
- Non vengono raccolti dati utente
- Le credenziali Spotify non vengono mai trasmesse in chiaro

## 📝 Licenza

Questo progetto è fornito come-è per uso educativo e personale.

## 🤝 Contributi

Se desideri migliorare l'app, puoi:
1. Aggiungere nuove sorgenti di streaming
2. Implementare la sincronizzazione del cloud
3. Migliorare l'interfaccia grafica
4. Aggiungere funzioni di ricerca avanzata

## 📞 Supporto

Per problemi e domande:
1. Controlla la sezione "Risoluzione Problemi"
2. Verifica i log dell'applicazione
3. Controlla la documentazione delle librerie utilizzate

## 🚀 Roadmap Futuri

- [ ] Integrare Apple Music
- [ ] Sincronizzazione cloud
- [ ] Equalizzatore audio
- [ ] Visualizzatore audio
- [ ] Barra di ricerca avanzata
- [ ] Tema scuro/chiaro dinamico
- [ ] Supporto per podcast
- [ ] Integrazione Discord (Rich Presence)
- [ ] Export playlist in formato M3U/PLS
- [ ] Statistiche di ascolto

## 📚 Risorse Utili

- [Material Design 3 - Google](https://m3.material.io/)
- [PyQt6 Documentation](https://www.riverbankcomputing.com/static/Docs/PyQt6/)
- [Spotipy Documentation](https://spotipy.readthedocs.io/)
- [yt-dlp Documentation](https://github.com/yt-dlp/yt-dlp)
- [Pygame Documentation](https://www.pygame.org/)

---

**Sviluppato con ❤️ per gli amanti della musica**
