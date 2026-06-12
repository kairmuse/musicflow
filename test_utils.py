#!/usr/bin/env python3
"""
Script di test per MusicFlow
Verifica che tutte le componenti funzionino correttamente
"""

import unittest
import os
import sys
import tempfile
from pathlib import Path

# Aggiungi il directory root al path
sys.path.insert(0, os.path.dirname(__file__))

from utils import (
    ConfigManager, PlaylistManager, TimeFormatter, 
    FileHelper, Logger
)


class TestConfigManager(unittest.TestCase):
    """Test del ConfigManager"""
    
    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.env_file = os.path.join(self.temp_dir, ".env")
        self.config = ConfigManager(self.env_file)
    
    def test_load_config(self):
        """Test caricamento configurazione"""
        self.assertIsNotNone(self.config.config)
        self.assertIn('spotify_client_id', self.config.config)
    
    def test_get_set_config(self):
        """Test get e set di configurazione"""
        self.config.set('test_key', 'test_value')
        self.assertEqual(self.config.get('test_key'), 'test_value')
    
    def test_get_default(self):
        """Test get con valore di default"""
        value = self.config.get('nonexistent', 'default')
        self.assertEqual(value, 'default')


class TestPlaylistManager(unittest.TestCase):
    """Test del PlaylistManager"""
    
    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.songs = [
            {
                'title': 'Song 1',
                'artist': 'Artist 1',
                'album': 'Album 1',
                'duration': 180,
                'file_path': '/path/to/song1.mp3'
            },
            {
                'title': 'Song 2',
                'artist': 'Artist 2',
                'album': 'Album 2',
                'duration': 200,
                'file_path': '/path/to/song2.mp3'
            }
        ]
    
    def test_export_m3u(self):
        """Test esportazione M3U"""
        m3u_file = os.path.join(self.temp_dir, 'test.m3u')
        result = PlaylistManager.export_playlist(
            self.songs,
            m3u_file,
            format='m3u'
        )
        
        self.assertTrue(result)
        self.assertTrue(os.path.exists(m3u_file))
        
        with open(m3u_file, 'r') as f:
            content = f.read()
            self.assertIn('#EXTM3U', content)
            self.assertIn('Song 1', content)
    
    def test_export_pls(self):
        """Test esportazione PLS"""
        pls_file = os.path.join(self.temp_dir, 'test.pls')
        result = PlaylistManager.export_playlist(
            self.songs,
            pls_file,
            format='pls'
        )
        
        self.assertTrue(result)
        self.assertTrue(os.path.exists(pls_file))
        
        with open(pls_file, 'r') as f:
            content = f.read()
            self.assertIn('[playlist]', content)
            self.assertIn('NumberOfEntries=2', content)
    
    def test_import_m3u(self):
        """Test importazione M3U"""
        m3u_file = os.path.join(self.temp_dir, 'import_test.m3u')
        
        with open(m3u_file, 'w') as f:
            f.write("#EXTM3U\n")
            f.write("#EXTINF:180,Artist 1 - Song 1\n")
            f.write("/path/to/song1.mp3\n")
            f.write("#EXTINF:200,Artist 2 - Song 2\n")
            f.write("/path/to/song2.mp3\n")
        
        songs = PlaylistManager.import_m3u(m3u_file)
        self.assertEqual(len(songs), 2)
        self.assertEqual(songs[0]['file_path'], '/path/to/song1.mp3')


class TestTimeFormatter(unittest.TestCase):
    """Test del TimeFormatter"""
    
    def test_seconds_to_hms(self):
        """Test conversione secondi a HH:MM:SS"""
        # Meno di un'ora
        self.assertEqual(TimeFormatter.seconds_to_hms(0), "0:00")
        self.assertEqual(TimeFormatter.seconds_to_hms(60), "1:00")
        self.assertEqual(TimeFormatter.seconds_to_hms(125), "2:05")
        self.assertEqual(TimeFormatter.seconds_to_hms(3661), "1:01:01")
    
    def test_seconds_to_hms_negative(self):
        """Test conversione con secondi negativi"""
        self.assertEqual(TimeFormatter.seconds_to_hms(-100), "00:00")
    
    def test_hms_to_seconds(self):
        """Test conversione HH:MM:SS a secondi"""
        self.assertEqual(TimeFormatter.hms_to_seconds("0:00"), 0)
        self.assertEqual(TimeFormatter.hms_to_seconds("1:00"), 60)
        self.assertEqual(TimeFormatter.hms_to_seconds("2:05"), 125)
        self.assertEqual(TimeFormatter.hms_to_seconds("1:01:01"), 3661)
    
    def test_conversione_bidirezionale(self):
        """Test conversione bidirezionale"""
        original = 3661
        hms = TimeFormatter.seconds_to_hms(original)
        back = TimeFormatter.hms_to_seconds(hms)
        self.assertEqual(original, back)


class TestFileHelper(unittest.TestCase):
    """Test del FileHelper"""
    
    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
    
    def test_is_audio_file(self):
        """Test riconoscimento file audio"""
        self.assertTrue(FileHelper.is_audio_file('/path/to/song.mp3'))
        self.assertTrue(FileHelper.is_audio_file('/path/to/song.wav'))
        self.assertTrue(FileHelper.is_audio_file('/path/to/song.flac'))
        self.assertTrue(FileHelper.is_audio_file('/path/to/song.ogg'))
        
        self.assertFalse(FileHelper.is_audio_file('/path/to/image.jpg'))
        self.assertFalse(FileHelper.is_audio_file('/path/to/video.mp4'))
    
    def test_get_audio_files_in_folder(self):
        """Test ricerca file audio in cartella"""
        # Crea file di test
        Path(self.temp_dir, 'song1.mp3').touch()
        Path(self.temp_dir, 'song2.wav').touch()
        Path(self.temp_dir, 'image.jpg').touch()
        
        audio_files = FileHelper.get_audio_files_in_folder(self.temp_dir, recursive=False)
        
        self.assertEqual(len(audio_files), 2)
        self.assertTrue(any('song1.mp3' in f for f in audio_files))
        self.assertTrue(any('song2.wav' in f for f in audio_files))
        self.assertFalse(any('image.jpg' in f for f in audio_files))
    
    def test_get_file_size_mb(self):
        """Test calcolo dimensione file"""
        test_file = os.path.join(self.temp_dir, 'test.txt')
        with open(test_file, 'w') as f:
            f.write('x' * 1024)  # 1 KB
        
        size_mb = FileHelper.get_file_size_mb(test_file)
        self.assertGreater(size_mb, 0)
        self.assertLess(size_mb, 1)  # Meno di 1 MB


class TestLogger(unittest.TestCase):
    """Test del Logger"""
    
    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.log_file = os.path.join(self.temp_dir, 'test.log')
        self.logger = Logger(self.log_file)
    
    def test_log_info(self):
        """Test logging informativo"""
        self.logger.info("Test info message")
        
        self.assertTrue(os.path.exists(self.log_file))
        with open(self.log_file, 'r') as f:
            content = f.read()
            self.assertIn('Test info message', content)
            self.assertIn('[INFO]', content)
    
    def test_log_levels(self):
        """Test diversi livelli di log"""
        self.logger.info("Info")
        self.logger.warning("Warning")
        self.logger.error("Error")
        self.logger.debug("Debug")
        
        with open(self.log_file, 'r') as f:
            content = f.read()
            self.assertIn('[INFO]', content)
            self.assertIn('[WARNING]', content)
            self.assertIn('[ERROR]', content)
            self.assertIn('[DEBUG]', content)


class TestMusicDatabase(unittest.TestCase):
    """Test del MusicDatabase"""
    
    def setUp(self):
        # Usa un database in memoria per i test
        import sqlite3
        from music_player_app import MusicDatabase
        
        self.db = MusicDatabase(':memory:')
    
    def test_add_song(self):
        """Test aggiunta canzone"""
        result = self.db.add_song(
            "Test Song",
            "Test Artist",
            "Test Album",
            180,
            "/path/to/song.mp3"
        )
        self.assertTrue(result)
    
    def test_get_all_songs(self):
        """Test recupero tutte le canzoni"""
        self.db.add_song("Song 1", "Artist 1", "Album 1", 180, "/path1.mp3")
        self.db.add_song("Song 2", "Artist 2", "Album 2", 200, "/path2.mp3")
        
        songs = self.db.get_all_songs()
        self.assertEqual(len(songs), 2)
    
    def test_duplicate_song(self):
        """Test aggiunta canzone duplicata"""
        self.db.add_song("Song", "Artist", "Album", 180, "/path/song.mp3")
        result = self.db.add_song("Song", "Artist", "Album", 180, "/path/song.mp3")
        
        self.assertFalse(result)  # Non dovrebbe aggiungere duplicati
    
    def test_playlist_operations(self):
        """Test operazioni con playlist"""
        playlist_id = self.db.create_playlist("My Playlist", "Test playlist")
        self.assertIsNotNone(playlist_id)
        
        song_id = self.db.add_song("Song", "Artist", "Album", 180, "/path/song.mp3")
        
        # Aggiungi canzone alla playlist
        self.db.add_song_to_playlist(playlist_id, 1)
        
        songs = self.db.get_playlist_songs(playlist_id)
        self.assertEqual(len(songs), 1)


def run_tests(verbose=True):
    """Esegui tutti i test"""
    # Crea suite di test
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    
    # Aggiungi test
    suite.addTests(loader.loadTestsFromTestCase(TestConfigManager))
    suite.addTests(loader.loadTestsFromTestCase(TestPlaylistManager))
    suite.addTests(loader.loadTestsFromTestCase(TestTimeFormatter))
    suite.addTests(loader.loadTestsFromTestCase(TestFileHelper))
    suite.addTests(loader.loadTestsFromTestCase(TestLogger))
    
    # Non aggiungiamo TestMusicDatabase perché richiede import da music_player_app
    
    # Esegui i test
    runner = unittest.TextTestRunner(verbosity=2 if verbose else 1)
    result = runner.run(suite)
    
    # Ritorna il risultato
    return result.wasSuccessful()


if __name__ == '__main__':
    print("=" * 70)
    print("MusicFlow - Test Suite")
    print("=" * 70)
    print()
    
    success = run_tests(verbose=True)
    
    print()
    print("=" * 70)
    if success:
        print("✅ Tutti i test sono passati!")
    else:
        print("❌ Alcuni test non sono passati.")
    print("=" * 70)
    
    sys.exit(0 if success else 1)
