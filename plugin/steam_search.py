# -*- coding: utf-8 -*-
import json
import os
import re
import webbrowser
from pathlib import Path

from helper import STEAM_PATH
import vdf
from flox import Flox

DEFAULT_DRIVE = "C:"
SYSTEM_DRIVE = os.environ.get("SYSTEMDRIVE", DEFAULT_DRIVE)
STEAM_FOLDER = STEAM_PATH or os.path.join(
    f"{SYSTEM_DRIVE}\\", "Program Files (x86)", "Steam"
)
LIBRARIES_CONFIG = os.path.join(STEAM_FOLDER, "config", "libraryfolders.vdf")
LIBRARIES_STEAMAPPS = os.path.join(STEAM_FOLDER, "steamapps", "libraryfolders.vdf")
EXE_FILTER = ["installer", "help", "skse64_loader.exe"]


class SteamSearch(Flox):
    def __init__(self):
        self._steam_folder = None
        self._steam_libraries = None
        self._library_paths = None
        self._steam_folder = STEAM_FOLDER
        self.games = []
        super().__init__()

    @property
    def steam_folder(self):
        if self._steamfolder is None:
            self._steam_folder = self.settings.get("steam_folder", STEAM_FOLDER)
        return self._steam_folder

    @property
    def library_paths(self):
        if self._library_paths is None:
            steam_libraries = (
                LIBRARIES_CONFIG
                if Path(LIBRARIES_CONFIG).exists()
                else LIBRARIES_STEAMAPPS
            )
            library_paths = [self._steam_folder]
            try:
                library_folders = vdf.load(open(steam_libraries, "r"))
            except FileNotFoundError:
                pass
            else:
                if library_folders.get("libraryfolders"):
                    libraries_key = "libraryfolders"
                else:
                    libraries_key = "LibraryFolders"
                for item in library_folders[libraries_key].keys():
                    if item.isdigit():
                        try:
                            library_paths.append(
                                library_folders[libraries_key][item]["path"]
                            )
                        except TypeError:
                            library_paths.append(library_folders[libraries_key][item])

            self._library_paths = library_paths
        return self._library_paths

    def load_games(self):
        for path in self.library_paths:
            for manifest in Path(path, "steamapps").glob("*.acf"):
                self.add_manifest(manifest, path)

    def find_icon(self, install_dir, name):
        first_exe = None
        game_files = Path(install_dir).glob("**/*.exe")
        for file in game_files:
            if file.name.lower() not in EXE_FILTER:
                if first_exe is None:
                    first_exe = file
                if str(file.name).lower().startswith(name[0].lower()):
                    return str(file)

        return str(first_exe)

    def add_manifest(self, file, path):
        try:
            manifest = vdf.load(open(file))
        except (SyntaxError, UnicodeDecodeError):
            self.logger.debug(f"Error loading {path}, {file}")
            pass
        else:
            install_dir = Path(path).joinpath(
                "steamapps", "common", manifest["AppState"]["installdir"]
            )
            self.games.append(
                {
                    "id": manifest["AppState"]["appid"],
                    "name": manifest["AppState"]["name"],
                    "install_dir": str(install_dir),
                }
            )

    def grab_icon(self, id):
        game_icon = "./icon/steam-icon.png"
        icon_name = f"{id}_icon.jpg"
        icon_path = os.path.join(self._steam_folder, "appcache", "librarycache", icon_name)
        if os.path.exists(icon_path):
            return icon_path
        return game_icon

    def query(self, query):
        self.load_games()
        q = query.lower()
        pattern = ".*?".join(q)
        regex = re.compile(pattern)
        for game in self.games:
            match = regex.search(game["name"].lower())
            if match:
                icon = self.grab_icon(game["id"])
                self.add_item(
                    title=game["name"],
                    subtitle=game["install_dir"],
                    icon=icon,
                    method="launch_game",
                    parameters=[game["id"]],
                )

    def launch_game(self, game_id):
        webbrowser.open("steam://rungameid/{}".format(game_id))


if __name__ == "__main__":
    SteamSearch()
