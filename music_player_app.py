import sys
import os
import sqlite3
import json
from pathlib import Path
from typing import List, Dict, Optional
import threading
import time

from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QListWidget, QListWidgetItem, QLabel, QPushButton, QSlider,
    QLineEdit, QTabWidget, QFileDialog, QProgressBar, QMessageBox,
    QDialog, QComboBox, QSpinBox, QTextEdit
)
from PyQt6.QtCore import Qt, QTimer, pyqtSignal, QThread, QSize
from PyQt6.QtGui import QIcon, QPixmap, QFont, QColor
from PyQt6.QtMultimedia import QMediaPlayer, QAudioOutput
from PyQt6.QtCore import QUrl

import pygame
import requests
from pathlib import Path


class MaterialColors:
    """Material Design 3 Color Palette"""
    PRIMARY = "#6F00D2"
    ON_PRIMARY = "#FFFFFF"
    PRIMARY_CONTAINER = "#EADDFF"
    ON_PRIMARY_CONTAINER = "#21005D"
    
    SECONDARY = "#625B71"
    TERTIARY = "#7D5260"
    
    BACKGROUND = "#FFFBFE"
    SURFACE = "#FFFBFE"
    SURFACE_VARIANT = "#E7E0EC"
    
    ERROR = "#B3261E"
    OUTLINE = "#79747E"
    OUTLINE_VARIANT = "#CAC4D0"


class MusicDatabase:
    """Gestione database SQLite per musica locale"""
    
    def __init__(self, db_path="music_library.db"):
        self.db_path = db_path
        self.init_db()
    
    def init_db(self):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS songs (
                id INTEGER PRIMARY KEY,
                title TEXT,
                artist TEXT,
                album TEXT,
                duration INTEGER,
                file_path TEXT UNIQUE,
                downloaded BOOLEAN,
                date_added TIMESTAMP
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS playlists (
                id INTEGER PRIMARY KEY,
                name TEXT UNIQUE,
                description TEXT,
                source TEXT,
                date_created TIMESTAMP
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS playlist_songs (
                playlist_id INTEGER,
                song_id INTEGER,
                FOREIGN KEY(playlist_id) REFERENCES playlists(id),
                FOREIGN KEY(song_id) REFERENCES songs(id)
            )
        ''')
        
        conn.commit()
        conn.close()
    
    def add_song(self, title, artist, album, duration, file_path, downloaded=False):
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO songs (title, artist, album, duration, file_path, downloaded, date_added)
                VALUES (?, ?, ?, ?, ?, ?, datetime('now'))
            ''', (title, artist, album, duration, file_path, downloaded))
            conn.commit()
            conn.close()
            return True
        except sqlite3.IntegrityError:
            return False
    
    def get_all_songs(self):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('SELECT id, title, artist, album, duration, file_path FROM songs')
        songs = cursor.fetchall()
        conn.close()
        return songs
    
    def create_playlist(self, name, description="", source="local"):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO playlists (name, description, source, date_created)
            VALUES (?, ?, ?, datetime('now'))
        ''', (name, description, source))
        conn.commit()
        playlist_id = cursor.lastrowid
        conn.close()
        return playlist_id
    
    def add_song_to_playlist(self, playlist_id, song_id):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO playlist_songs (playlist_id, song_id)
            VALUES (?, ?)
        ''', (playlist_id, song_id))
        conn.commit()
        conn.close()
    
    def get_playlist_songs(self, playlist_id):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('''
            SELECT s.id, s.title, s.artist, s.album, s.duration, s.file_path
            FROM songs s
            JOIN playlist_songs ps ON s.id = ps.song_id
            WHERE ps.playlist_id = ?
        ''', (playlist_id,))
        songs = cursor.fetchall()
        conn.close()
        return songs


class SpotifyImporter:
    """Importa playlist da Spotify"""
    
    def __init__(self, client_id, client_secret):
        self.client_id = client_id
        self.client_secret = client_secret
        self.token = None
        self.authenticate()
    
    def authenticate(self):
        """Autentica con le API Spotify"""
        auth_url = "https://accounts.spotify.com/api/token"
        
        auth_data = {
            'grant_type': 'client_credentials',
            'client_id': self.client_id,
            'client_secret': self.client_secret,
        }
        
        try:
            response = requests.post(auth_url, data=auth_data)
            response.raise_for_status()
            self.token = response.json()['access_token']
            return True
        except Exception as e:
            print(f"Spotify auth error: {e}")
            return False
    
    def get_playlist_tracks(self, playlist_id):
        """Recupera i brani da una playlist Spotify"""
        if not self.token:
            return []
        
        headers = {'Authorization': f'Bearer {self.token}'}
        url = f'https://api.spotify.com/v1/playlists/{playlist_id}/tracks'
        
        tracks = []
        try:
            response = requests.get(url, headers=headers)
            response.raise_for_status()
            data = response.json()
            
            for item in data.get('items', []):
                track = item['track']
                tracks.append({
                    'title': track['name'],
                    'artist': ', '.join([artist['name'] for artist in track['artists']]),
                    'album': track['album']['name'],
                    'duration': track['duration_ms'] // 1000,
                    'spotify_id': track['id']
                })
            
            return tracks
        except Exception as e:
            print(f"Error fetching Spotify playlist: {e}")
            return []


class YouTubeMusicImporter:
    """Importa playlist da YouTube Music"""
    
    @staticmethod
    def get_playlist_videos(playlist_url):
        """Recupera i video da una playlist YouTube Music"""
        # Nota: Richiede yt-dlp
        try:
            import yt_dlp
            
            ydl_opts = {
                'quiet': True,
                'no_warnings': True,
                'extract_flat': 'in_playlist',
            }
            
            videos = []
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(playlist_url, download=False)
                
                for entry in info.get('entries', []):
                    videos.append({
                        'title': entry.get('title', 'Unknown'),
                        'video_id': entry.get('id'),
                        'duration': entry.get('duration', 0),
                        'uploader': entry.get('uploader', 'Unknown')
                    })
            
            return videos
        except Exception as e:
            print(f"Error fetching YouTube Music playlist: {e}")
            return []
    
    @staticmethod
    def download_audio(video_id, output_path="downloads"):
        """Scarica l'audio da un video YouTube"""
        try:
            import yt_dlp
            
            Path(output_path).mkdir(exist_ok=True)
            
            ydl_opts = {
                'format': 'bestaudio/best',
                'postprocessors': [{
                    'key': 'FFmpegExtractAudio',
                    'preferredcodec': 'mp3',
                    'preferredquality': '192',
                }],
                'outtmpl': os.path.join(output_path, '%(title)s.%(ext)s'),
                'quiet': False,
            }
            
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                ydl.download([f'https://www.youtube.com/watch?v={video_id}'])
            
            return True
        except Exception as e:
            print(f"Error downloading YouTube audio: {e}")
            return False


class AudioMetadataReader:
    """Legge i metadati dei file audio locali"""
    
    @staticmethod
    def read_metadata(file_path):
        """Estrae i metadati da un file audio"""
        try:
            from mutagen.easyid3 import EasyID3
            from mutagen.wave import WAVE
            from mutagen.oggtheora import OggTheora
            
            try:
                audio = EasyID3(file_path)
                return {
                    'title': audio.get('title', ['Unknown'])[0],
                    'artist': audio.get('artist', ['Unknown'])[0],
                    'album': audio.get('album', ['Unknown'])[0],
                    'duration': int(audio.info.length) if audio.info else 0
                }
            except:
                # Fallback: usa il nome del file
                filename = Path(file_path).stem
                return {
                    'title': filename,
                    'artist': 'Unknown',
                    'album': 'Unknown',
                    'duration': 0
                }
        except:
            return None


class MusicPlayer(QMainWindow):
    """Applicazione principale Music Player con Material Design 3"""
    
    def __init__(self):
        super().__init__()
        self.setWindowTitle("MusicFlow - Material Design 3")
        self.setGeometry(100, 100, 1000, 700)
        
        # Inizializza pygame mixer per audio
        pygame.mixer.init()
        
        # Database
        self.db = MusicDatabase()
        
        # Stato del player
        self.current_song = None
        self.is_playing = False
        self.current_playlist = None
        self.playlist_songs = []
        self.current_song_index = 0
        
        # Timer per aggiornare la posizione
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_position)
        
        self.init_ui()
        self.apply_material_theme()
        self.load_local_library()
    
    def init_ui(self):
        """Inizializza l'interfaccia utente"""
        main_widget = QWidget()
        self.setCentralWidget(main_widget)
        
        layout = QVBoxLayout()
        
        # Header
        header = self.create_header()
        layout.addWidget(header)
        
        # Tab widget
        self.tabs = QTabWidget()
        
        # Tab 1: Library
        library_tab = self.create_library_tab()
        self.tabs.addTab(library_tab, "📚 Libreria")
        
        # Tab 2: Playlists
        playlist_tab = self.create_playlist_tab()
        self.tabs.addTab(playlist_tab, "🎵 Playlist")
        
        # Tab 3: Importa
        import_tab = self.create_import_tab()
        self.tabs.addTab(import_tab, "📥 Importa")
        
        layout.addWidget(self.tabs)
        
        # Player Controls
        controls = self.create_player_controls()
        layout.addWidget(controls)
        
        main_widget.setLayout(layout)
    
    def create_header(self):
        """Crea l'header dell'applicazione"""
        header = QWidget()
        layout = QHBoxLayout()
        
        title = QLabel("🎶 MusicFlow")
        title_font = QFont()
        title_font.setPointSize(24)
        title_font.setBold(True)
        title.setFont(title_font)
        
        layout.addWidget(title)
        layout.addStretch()
        
        # Info brano corrente
        self.song_info = QLabel("Seleziona una canzone...")
        self.song_info.setStyleSheet(f"color: {MaterialColors.OUTLINE};")
        layout.addWidget(self.song_info)
        
        header.setLayout(layout)
        header.setStyleSheet(f"background-color: {MaterialColors.PRIMARY_CONTAINER}; padding: 15px;")
        
        return header
    
    def create_library_tab(self):
        """Crea il tab della libreria"""
        widget = QWidget()
        layout = QVBoxLayout()
        
        # Pulsanti di controllo
        button_layout = QHBoxLayout()
        
        add_folder_btn = QPushButton("+ Aggiungi Cartella")
        add_folder_btn.clicked.connect(self.add_music_folder)
        button_layout.addWidget(add_folder_btn)
        
        refresh_btn = QPushButton("🔄 Aggiorna")
        refresh_btn.clicked.connect(self.refresh_library)
        button_layout.addWidget(refresh_btn)
        
        button_layout.addStretch()
        layout.addLayout(button_layout)
        
        # Lista canzoni
        self.song_list = QListWidget()
        self.song_list.itemDoubleClicked.connect(self.play_selected_song)
        layout.addWidget(self.song_list)
        
        widget.setLayout(layout)
        return widget
    
    def create_playlist_tab(self):
        """Crea il tab delle playlist"""
        widget = QWidget()
        layout = QVBoxLayout()
        
        # Controlli playlist
        button_layout = QHBoxLayout()
        
        new_playlist_btn = QPushButton("+ Nuova Playlist")
        new_playlist_btn.clicked.connect(self.create_new_playlist)
        button_layout.addWidget(new_playlist_btn)
        
        button_layout.addStretch()
        layout.addLayout(button_layout)
        
        # Lista playlist
        self.playlist_list = QListWidget()
        self.playlist_list.itemClicked.connect(self.load_playlist)
        layout.addWidget(QLabel("Playlist:"))
        layout.addWidget(self.playlist_list)
        
        # Canzoni nella playlist selezionata
        layout.addWidget(QLabel("Canzoni:"))
        self.playlist_songs_list = QListWidget()
        self.playlist_songs_list.itemDoubleClicked.connect(self.play_selected_song)
        layout.addWidget(self.playlist_songs_list)
        
        widget.setLayout(layout)
        return widget
    
    def create_import_tab(self):
        """Crea il tab per l'importazione"""
        widget = QWidget()
        layout = QVBoxLayout()
        
        # Spotify Section
        spotify_label = QLabel("🎵 Importa da Spotify")
        spotify_font = QFont()
        spotify_font.setBold(True)
        spotify_label.setFont(spotify_font)
        layout.addWidget(spotify_label)
        
        spotify_layout = QHBoxLayout()
        spotify_layout.addWidget(QLabel("Playlist URL:"))
        self.spotify_url = QLineEdit()
        self.spotify_url.setPlaceholderText("https://open.spotify.com/playlist/...")
        spotify_layout.addWidget(self.spotify_url)
        
        spotify_btn = QPushButton("Importa Spotify")
        spotify_btn.clicked.connect(self.import_spotify_playlist)
        spotify_layout.addWidget(spotify_btn)
        layout.addLayout(spotify_layout)
        
        # YouTube Music Section
        yt_label = QLabel("▶️ Importa da YouTube Music")
        yt_label.setFont(spotify_font)
        layout.addWidget(yt_label)
        
        yt_layout = QHBoxLayout()
        yt_layout.addWidget(QLabel("Playlist URL:"))
        self.yt_url = QLineEdit()
        self.yt_url.setPlaceholderText("https://music.youtube.com/playlist?list=...")
        yt_layout.addWidget(self.yt_url)
        
        yt_btn = QPushButton("Importa YouTube Music")
        yt_btn.clicked.connect(self.import_youtube_playlist)
        yt_layout.addWidget(yt_btn)
        layout.addLayout(yt_layout)
        
        # Progress bar
        self.import_progress = QProgressBar()
        self.import_progress.setVisible(False)
        layout.addWidget(self.import_progress)
        
        layout.addStretch()
        widget.setLayout(layout)
        return widget
    
    def create_player_controls(self):
        """Crea i controlli del player"""
        widget = QWidget()
        layout = QVBoxLayout()
        
        # Progress bar
        progress_layout = QHBoxLayout()
        self.current_time_label = QLabel("0:00")
        self.progress_slider = QSlider(Qt.Orientation.Horizontal)
        self.progress_slider.sliderMoved.connect(self.seek_song)
        self.total_time_label = QLabel("0:00")
        
        progress_layout.addWidget(self.current_time_label)
        progress_layout.addWidget(self.progress_slider)
        progress_layout.addWidget(self.total_time_label)
        layout.addLayout(progress_layout)
        
        # Button controls
        button_layout = QHBoxLayout()
        
        self.play_btn = QPushButton("▶️ Play")
        self.play_btn.clicked.connect(self.toggle_play)
        button_layout.addWidget(self.play_btn)
        
        prev_btn = QPushButton("⏮️ Precedente")
        prev_btn.clicked.connect(self.previous_song)
        button_layout.addWidget(prev_btn)
        
        next_btn = QPushButton("⏭️ Successivo")
        next_btn.clicked.connect(self.next_song)
        button_layout.addWidget(next_btn)
        
        # Volume control
        button_layout.addWidget(QLabel("🔊 Volume:"))
        self.volume_slider = QSlider(Qt.Orientation.Horizontal)
        self.volume_slider.setMaximum(100)
        self.volume_slider.setValue(70)
        self.volume_slider.setMaximumWidth(100)
        self.volume_slider.sliderMoved.connect(self.change_volume)
        button_layout.addWidget(self.volume_slider)
        
        layout.addLayout(button_layout)
        widget.setLayout(layout)
        widget.setStyleSheet(f"background-color: {MaterialColors.SURFACE_VARIANT}; padding: 10px;")
        
        return widget
    
    def apply_material_theme(self):
        """Applica il tema Material Design 3"""
        style = f"""
            QMainWindow {{
                background-color: {MaterialColors.BACKGROUND};
            }}
            QPushButton {{
                background-color: {MaterialColors.PRIMARY};
                color: {MaterialColors.ON_PRIMARY};
                border: none;
                padding: 8px 16px;
                border-radius: 8px;
                font-weight: bold;
            }}
            QPushButton:hover {{
                background-color: #7F1AE2;
            }}
            QPushButton:pressed {{
                background-color: #5F00C2;
            }}
            QLineEdit {{
                border: 1px solid {MaterialColors.OUTLINE_VARIANT};
                border-radius: 8px;
                padding: 8px;
                background-color: {MaterialColors.SURFACE};
            }}
            QListWidget {{
                border: 1px solid {MaterialColors.OUTLINE_VARIANT};
                border-radius: 8px;
                background-color: {MaterialColors.SURFACE};
            }}
            QTabWidget::pane {{
                border: 1px solid {MaterialColors.OUTLINE_VARIANT};
            }}
            QTabBar::tab {{
                background-color: {MaterialColors.SURFACE_VARIANT};
                padding: 8px 16px;
                margin-right: 2px;
            }}
            QTabBar::tab:selected {{
                background-color: {MaterialColors.PRIMARY};
                color: {MaterialColors.ON_PRIMARY};
            }}
            QLabel {{
                color: {MaterialColors.OUTLINE};
            }}
        """
        self.setStyleSheet(style)
    
    def add_music_folder(self):
        """Aggiunge una cartella di musica alla libreria"""
        folder = QFileDialog.getExistingDirectory(self, "Seleziona cartella musica")
        if folder:
            self.scan_music_folder(folder)
            self.refresh_library()
    
    def scan_music_folder(self, folder):
        """Scansiona una cartella per file audio"""
        audio_extensions = {'.mp3', '.wav', '.flac', '.ogg', '.m4a'}
        count = 0
        
        for file_path in Path(folder).rglob('*'):
            if file_path.suffix.lower() in audio_extensions:
                metadata = AudioMetadataReader.read_metadata(str(file_path))
                if metadata:
                    self.db.add_song(
                        metadata['title'],
                        metadata['artist'],
                        metadata['album'],
                        metadata['duration'],
                        str(file_path)
                    )
                    count += 1
        
        QMessageBox.information(self, "Successo", f"Aggiunte {count} canzoni alla libreria!")
    
    def load_local_library(self):
        """Carica la libreria locale"""
        self.refresh_library()
    
    def refresh_library(self):
        """Aggiorna la lista delle canzoni"""
        self.song_list.clear()
        songs = self.db.get_all_songs()
        
        for song_id, title, artist, album, duration, file_path in songs:
            item_text = f"{title} - {artist}"
            item = QListWidgetItem(item_text)
            item.setData(Qt.ItemDataRole.UserRole, (song_id, file_path))
            self.song_list.addItem(item)
    
    def play_selected_song(self, item):
        """Riproduci la canzone selezionata"""
        data = item.data(Qt.ItemDataRole.UserRole)
        if data:
            song_id, file_path = data
            self.play_song(file_path, item.text())
    
    def play_song(self, file_path, song_name):
        """Riproduci una canzone"""
        try:
            pygame.mixer.music.load(file_path)
            pygame.mixer.music.play()
            self.is_playing = True
            self.current_song = file_path
            self.play_btn.setText("⏸️ Pausa")
            self.song_info.setText(song_name)
            
            # Avvia il timer per aggiornare il progresso
            self.timer.start(100)
        except Exception as e:
            QMessageBox.critical(self, "Errore", f"Non posso riprodurre il file: {e}")
    
    def toggle_play(self):
        """Attiva/disattiva la riproduzione"""
        if self.is_playing:
            pygame.mixer.music.pause()
            self.is_playing = False
            self.play_btn.setText("▶️ Play")
        else:
            if pygame.mixer.music.get_busy():
                pygame.mixer.music.unpause()
            self.is_playing = True
            self.play_btn.setText("⏸️ Pausa")
    
    def next_song(self):
        """Riproduci la canzone successiva"""
        if self.song_list.count() > 0:
            current_index = self.song_list.row(self.song_list.currentItem())
            next_index = (current_index + 1) % self.song_list.count()
            self.song_list.setCurrentRow(next_index)
            self.play_selected_song(self.song_list.item(next_index))
    
    def previous_song(self):
        """Riproduci la canzone precedente"""
        if self.song_list.count() > 0:
            current_index = self.song_list.row(self.song_list.currentItem())
            prev_index = (current_index - 1) % self.song_list.count()
            self.song_list.setCurrentRow(prev_index)
            self.play_selected_song(self.song_list.item(prev_index))
    
    def change_volume(self, value):
        """Cambia il volume"""
        pygame.mixer.music.set_volume(value / 100)
    
    def update_position(self):
        """Aggiorna la posizione della canzone"""
        if pygame.mixer.music.get_busy():
            # Aggiorna i label dei tempi
            pass
    
    def seek_song(self, position):
        """Vai a una posizione specifica"""
        # Nota: pygame non supporta il seek nativo, potrebbe richiedere alternativa
        pass
    
    def create_new_playlist(self):
        """Crea una nuova playlist"""
        dialog = QDialog(self)
        dialog.setWindowTitle("Nuova Playlist")
        layout = QVBoxLayout()
        
        layout.addWidget(QLabel("Nome Playlist:"))
        name_input = QLineEdit()
        layout.addWidget(name_input)
        
        layout.addWidget(QLabel("Descrizione:"))
        desc_input = QTextEdit()
        desc_input.setMaximumHeight(60)
        layout.addWidget(desc_input)
        
        create_btn = QPushButton("Crea")
        create_btn.clicked.connect(lambda: self.save_playlist(
            name_input.text(),
            desc_input.toPlainText(),
            dialog
        ))
        layout.addWidget(create_btn)
        
        dialog.setLayout(layout)
        dialog.exec()
    
    def save_playlist(self, name, description, dialog):
        """Salva una nuova playlist"""
        if name.strip():
            self.db.create_playlist(name, description)
            self.refresh_playlists()
            dialog.accept()
        else:
            QMessageBox.warning(self, "Errore", "Inserisci un nome per la playlist")
    
    def refresh_playlists(self):
        """Aggiorna la lista delle playlist"""
        self.playlist_list.clear()
        # Implementare il caricamento delle playlist dal database
    
    def load_playlist(self, item):
        """Carica una playlist"""
        # Implementare il caricamento della playlist selezionata
        pass
    
    def import_spotify_playlist(self):
        """Importa una playlist da Spotify"""
        url = self.spotify_url.text()
        if not url:
            QMessageBox.warning(self, "Errore", "Inserisci un URL Spotify")
            return
        
        QMessageBox.information(
            self,
            "Info",
            "Per completare l'importazione da Spotify,\nè necessario configurare le credenziali API."
        )
    
    def import_youtube_playlist(self):
        """Importa una playlist da YouTube Music"""
        url = self.yt_url.text()
        if not url:
            QMessageBox.warning(self, "Errore", "Inserisci un URL YouTube Music")
            return
        
        self.import_progress.setVisible(True)
        
        # Esegui l'importazione in un thread separato
        def import_thread():
            try:
                videos = YouTubeMusicImporter.get_playlist_videos(url)
                # Aggiungi i video al database
                QMessageBox.information(
                    self,
                    "Successo",
                    f"Trovati {len(videos)} video. Desideri scaricarli?"
                )
            except Exception as e:
                QMessageBox.critical(self, "Errore", f"Errore nell'importazione: {e}")
            finally:
                self.import_progress.setVisible(False)
        
        thread = threading.Thread(target=import_thread)
        thread.daemon = True
        thread.start()


def main():
    app = QApplication(sys.argv)
    player = MusicPlayer()
    player.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
