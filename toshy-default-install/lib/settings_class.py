import os
import time
import sqlite3
# import threading
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

from keyszer.lib.logger import debug, error



class Settings:
    def __init__(self, config_dir_path: str = '..') -> None:
        # settings defaults
        self.config_dir_path    = config_dir_path
        self.db_file_path = os.path.join(config_dir_path, 'toshy_user_preferences.sqlite')
        self.forced_numpad      = True      # Default: True
        self.media_arrows_fix   = False     # Default: False
        self.Caps2Cmd           = False     # Default: False
        self.Caps2Esc_Cmd       = False     # Default: False
        self.Enter2Ent_Cmd      = False     # Default: False
        self.ST3_in_VSCode      = False     # Default: False
        self.multi_lang         = False     # Default: False
        self.gui_dark_theme     = True      # Default: True
        # create the database file and save default settings if necessary
        if not os.path.isfile(self.db_file_path):
            self.save_settings()
        self.load_settings()

    def watch_database(self):
        # initialize observer to watch for database changes
        self.event_handler = FileSystemEventHandler()
        self.event_handler.on_modified = self.on_database_modified
        self.observer = Observer()
        self.observer.schedule(self.event_handler, path=self.config_dir_path, recursive=False)
        self.observer.start()

    def on_database_modified(self, event):
        time.sleep(0.01)       # pause briefly here to prevent repeat "bounce"
        if event.src_path == self.db_file_path:
            debug(f'User preferences database modified... loading new settings...')
            self.load_settings()

    def save_settings(self):
        db_connection = sqlite3.connect(self.db_file_path)
        db_cursor = db_connection.cursor()
        db_cursor.execute('''CREATE TABLE IF NOT EXISTS config_preferences
                (name TEXT PRIMARY KEY, value TEXT)''')
        # Define the SQL query as a string variable
        sql_query = "INSERT OR REPLACE INTO config_preferences (name, value) VALUES (?, ?)"
        # Execute the SQL query with different parameters
        db_cursor.execute(sql_query, ('forced_numpad',      str(self.forced_numpad)))
        db_cursor.execute(sql_query, ('media_arrows_fix',   str(self.media_arrows_fix)))
        db_cursor.execute(sql_query, ('multi_lang',         str(self.multi_lang)))
        db_cursor.execute(sql_query, ('Caps2Cmd',           str(self.Caps2Cmd)))
        db_cursor.execute(sql_query, ('Caps2Esc_Cmd',       str(self.Caps2Esc_Cmd)))
        db_cursor.execute(sql_query, ('Enter2Ent_Cmd',      str(self.Enter2Ent_Cmd)))
        db_cursor.execute(sql_query, ('ST3_in_VSCode',      str(self.ST3_in_VSCode)))
        db_cursor.execute(sql_query, ('gui_dark_theme',     str(self.gui_dark_theme)))
        # Commit changes to the database
        db_connection.commit()
        db_connection.close()

    def load_settings(self):
        db_connection = sqlite3.connect(self.db_file_path)
        db_cursor = db_connection.cursor()
        db_cursor.execute("SELECT * FROM config_preferences")
        rows = db_cursor.fetchall()
        for row in rows:
            # Convert the string value to a Python boolean correctly
            setting_value = row[1].lower() == 'true'
            if True is False: pass  # dummy first `if` line so other rows line up
            elif row[0] == 'forced_numpad':     self.forced_numpad = setting_value
            elif row[0] == 'media_arrows_fix':  self.media_arrows_fix = setting_value
            elif row[0] == 'multi_lang':        self.multi_lang = setting_value
            elif row[0] == 'Caps2Cmd':          self.Caps2Cmd = setting_value
            elif row[0] == 'Caps2Esc_Cmd':      self.Caps2Esc_Cmd = setting_value
            elif row[0] == 'Enter2Ent_Cmd':     self.Enter2Ent_Cmd = setting_value
            elif row[0] == 'ST3_in_VSCode':     self.ST3_in_VSCode = setting_value
            elif row[0] == 'gui_dark_theme':    self.gui_dark_theme = setting_value
        db_connection.close()

    def __str__(self):
        return f"""(CG) Current settings:
        db_file_path      = {self.db_file_path}
        forced_numpad     = {self.forced_numpad}
        media_arrows_fix  = {self.media_arrows_fix}
        multi_lang        = {self.multi_lang}
        Caps2Cmd          = {self.Caps2Cmd}
        Caps2Esc_Cmd      = {self.Caps2Esc_Cmd}
        Enter2Ent_Cmd     = {self.Enter2Ent_Cmd}
        ST3_in_VSCode     = {self.ST3_in_VSCode}
        gui_dark_theme    = {self.gui_dark_theme}
    """
