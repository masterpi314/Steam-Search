from pathlib import Path
import winreg as reg
from winreg import HKEY_CURRENT_USER, HKEY_LOCAL_MACHINE

import vdf

STEAM_SUB_KEY = r'SOFTWARE\WOW6432Node\Valve\Steam'

DEFAULT_STEAM_PATH = r"c:\Program Files (x86)\Steam"
LIBRARY_CACHE_EXT = '.jpg'
ICON_SUFFIX = '_icon'
HEADER_SUFFIX = '_header'
LIBRARY_SUFFIX = '_library_600x900'
LIBRARY_HERO_SUFFIX = '_library_hero'
STEAMAPPS_FOLDER = 'steamapps'


class Steam(object):

    def __init__(self, steam_path=None):
        self._steam_path = None

    @property
    def steam_path(self):
        if self._steam_path is None:
            with reg.OpenKey(HKEY_LOCAL_MACHINE, STEAM_SUB_KEY) as hkey:
                try:
                    self._steam_path = Path(reg.QueryValueEx(hkey, "InstallPath")[0])
                except FileNotFoundError:
                    pass
        return self._steam_path

    def all_games(self):
        games = []
        for library in self.libraries():
            for game in library.games():
                games.append(game)
        return games

    def libraries(self):
        if self.steam_path is None:
            return []
        libraries = []
        libraries_manifest_path = self.steam_path.joinpath('steamapps', 'libraryfolders.vdf')
        if not libraries_manifest_path.exists():
            return []
        try:
            library_folders = vdf.load(open(libraries_manifest_path, 'r'))
        except FileNotFoundError:
            pass
        else:
            if library_folders.get('libraryfolders'):
                libraries_key = 'libraryfolders'
            else:
                libraries_key = 'LibraryFolders'
            for item in library_folders[libraries_key].keys():
                if item.isdigit():
                    try:
                        library_path = SteamLibrary(self.steam_path, library_folders[libraries_key][item]['path'])
                    except TypeError:
                        library_path = SteamLibrary(self.steam_path, library_folders[libraries_key][item])
                    libraries.append(library_path)
        return libraries

class SteamLibrary(object):

    def __init__(self, steam_path, library_path):
        self._steam_path = steam_path
        self._library_path = Path(library_path)

    def __str__(self):
        return str(self._library_path)

    def __repr__(self):
        return f'<SteamLibrary {self.__str__()}>'

    def games(self):
        games = []
        for manifest in self._library_path.joinpath(STEAMAPPS_FOLDER).glob('*.acf'):
            try:
                _game_manifest = vdf.load(open(manifest, 'r'))
                game = SteamGame(_game_manifest["AppState"]["appid"], _game_manifest["AppState"]["name"], _game_manifest["AppState"]["installdir"], self._steam_path, self._library_path)
            except FileNotFoundError:
                pass
            except SyntaxError:
                continue
            else:
                games.append(game)
        return games
        
class SteamGame(object):
    """Represents a steam game"""
    
    def __init__(self, id, name, installdir, steam_path, library_path):
        self.id = id
        self.name = name.replace('â„¢', '')
        self.installdir = installdir
        self.steam_path = steam_path
        self.library_path = library_path
        self._appcache_path = Path(self.steam_path).joinpath("appcache", "librarycache")

    def icon(self):
        return self._appcache_path.joinpath(f"{self.id}{ICON_SUFFIX}{LIBRARY_CACHE_EXT}")

    def header(self):
        return self._appcache_path.joinpath(f"{self.id}{HEADER_SUFFIX}{LIBRARY_CACHE_EXT}")

    def hero(self):
        return self._reappcache_path.joinpath(f"{self.id}{LIBRARY_HERO_SUFFIX}{LIBRARY_CACHE_EXT}")

    def run_game_url(self):
        return f'steam://rumgameid/{self.id}'

    def install_path(self):
        return self.library_path.joinpath('steamapps', 'common', self.installdir)