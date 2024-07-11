import os
import inspect
import sqlite3

from pprint import pprint
from typing import List, Dict, Optional, Tuple, Union
from watchdog.observers import Observer
from watchdog.events import FileSystemEvent, FileSystemEventHandler

import xwaykeyz.lib.logger
from xwaykeyz.lib.logger import debug, error


class Settings:
    def __init__(self, config_dir_path: str = '..') -> None:
        self.config_dir_path        = config_dir_path
        self.prefs_db_file_name     = 'toshy_user_preferences.sqlite'
        self.prefs_db_file_path     = os.path.join(self.config_dir_path, self.prefs_db_file_name)
        self.first_run              = True
        self.last_settings          = None
        self.current_settings       = None
        # Get the name of the module that instantiated the class
        calling_frame               = inspect.stack()[1]
        calling_file_path           = calling_frame.filename
        calling_module              = os.path.split(calling_file_path)[1]
        self.calling_module         = calling_module
        # settings defaults
        self.autostart_tray_icon    = True              # Default: True
        self.gui_dark_theme         = True              # Default: True
        self.override_kbtype        = 'Auto-Adapt'      # Default: 'Auto-Adapt'
            ###  Disable optspec_layout by default for performance, and international keyboard users
        self.optspec_layout         = 'Disabled'        # Default: 'Disabled'
        self.mru_layout             = ('us', 'default') # Default: ('us', 'default')
        self.forced_numpad          = True              # Default: True
        self.media_arrows_fix       = False             # Default: False
        self.multi_lang             = False             # Default: False
        self.Caps2Cmd               = False             # Default: False
        self.Caps2Esc_Cmd           = False             # Default: False
        self.Enter2Ent_Cmd          = False             # Default: False
        self.ST3_in_VSCode          = False             # Default: False
        # Synergy
        self.screen_has_focus       = True  # True if focus is on the screen, False otherwise
        self.synergy_log_path       = os.path.expanduser("~/.local/state/Synergy/synergy.log")
        self.synergy_log_last_pos   = 0  # Keep track of the last read position in the log file
        self.initial_log_read_done  = False
        # Make sure the database and tables are actually existing before trying to load settings
        self.ensure_database_setup()
        # Load user's custom settings from database (defaults will be saved if no DB)
        self.load_settings()

    def ensure_database_setup(self):
        # This will create the database file if it doesn't exist yet
        with sqlite3.connect(self.prefs_db_file_path) as db_connection:
            db_cursor = db_connection.cursor()

            # Function to check if a table exists
            def table_exists(table_name):
                """Utility function to check if a database table exists"""
                query = '''
                    SELECT name FROM sqlite_master WHERE type='table' AND name=?
                '''
                db_cursor.execute(query, (table_name,))
                return db_cursor.fetchone() is not None

            def table_is_empty(table_name):
                """Check if a database table is empty."""
                db_cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
                return db_cursor.fetchone()[0] == 0

            # Create the table for user preferences if it does not exist
            if not table_exists("config_preferences"):
                db_cursor.execute('''
                    CREATE TABLE IF NOT EXISTS config_preferences
                    (
                        name TEXT PRIMARY KEY, 
                        value TEXT
                    )
                    ''')

            if table_is_empty("config_preferences"):
                # Save the default values, only if the table is empty
                self._save_config_preferences(db_cursor)

            # Create the table for Most Recently Used Layouts if it does not exist
            if not table_exists("mru_layouts"):
                db_cursor.execute('''
                    CREATE TABLE IF NOT EXISTS mru_layouts
                    (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        layout_code TEXT,
                        variant_code TEXT,
                        timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
                    )
                    ''')
                # Create a trigger to keep only the 12 most recent records
                db_cursor.execute('''
                    CREATE TRIGGER IF NOT EXISTS trg_afterInsert_trim_MRU_Rows 
                        AFTER INSERT ON mru_layouts
                    BEGIN
                        DELETE FROM mru_layouts 
                        WHERE id IN (
                            SELECT id FROM mru_layouts 
                            ORDER BY timestamp DESC
                            LIMIT -1 OFFSET 12  -- Keeps the newest 12 rows
                        );
                    END;
                ''')

            if table_is_empty("mru_layouts"):
                # Save the default values, only if the table is empty
                self._save_mru_layouts(db_cursor)

    def watch_database(self):
        # initialize observer to watch for database changes
        event_handler = FileSystemEventHandler()
        event_handler.on_modified = self.on_database_modified
        observer = Observer()
        observer.schedule(event_handler, path=self.config_dir_path, recursive=False)
        observer.start()

    def on_database_modified(self, event: Optional[FileSystemEvent]):
        if event.src_path == self.prefs_db_file_path:
            self.load_settings()

    def _save_config_preferences(self, db_cursor: sqlite3.Cursor):
        sql_query = "INSERT OR REPLACE INTO config_preferences (name, value) VALUES (?, ?)"
        settings = [
            ('autostart_tray_icon',     str(self.autostart_tray_icon)),
            ('gui_dark_theme',          str(self.gui_dark_theme)),
            ('override_kbtype',         str(self.override_kbtype)),
            ('optspec_layout',          str(self.optspec_layout)),
            ('forced_numpad',           str(self.forced_numpad)),
            ('media_arrows_fix',        str(self.media_arrows_fix)),
            ('multi_lang',              str(self.multi_lang)),
            ('Caps2Cmd',                str(self.Caps2Cmd)),
            ('Caps2Esc_Cmd',            str(self.Caps2Esc_Cmd)),
            ('Enter2Ent_Cmd',           str(self.Enter2Ent_Cmd)),
            ('ST3_in_VSCode',           str(self.ST3_in_VSCode))
        ]

        for setting_name, setting_value in settings:
            db_cursor.execute(sql_query, (setting_name, setting_value))

    def _save_mru_layouts(self, db_cursor: sqlite3.Cursor):
        sql_query = '''
            INSERT INTO mru_layouts
            (layout_code, variant_code)
            VALUES (?, ?)
        '''
        # self.mru_layout is a tuple, taking care of both fields being inserted
        db_cursor.execute(sql_query, self.mru_layout)

    def save_settings(self):
        with sqlite3.connect(self.prefs_db_file_path) as db_connection:
            db_cursor = db_connection.cursor()
            self._save_config_preferences(db_cursor)
            self._save_mru_layouts(db_cursor)
            debug("Settings saved in database using Settings class method.")

    def load_settings(self):
        
        with sqlite3.connect(self.prefs_db_file_path) as db_connection:
            db_cursor = db_connection.cursor()

            db_cursor.execute("SELECT * FROM config_preferences")

            rows_prefs: List[Tuple[str, str]] = db_cursor.fetchall()
            for row in rows_prefs:
                # Convert the string value to a Python boolean correctly
                setting_value       = row[1].lower() == 'true'
                if True is False: pass  # dummy first `if` line so other rows line up (readability)
                elif row[0] == 'autostart_tray_icon' : self.autostart_tray_icon = setting_value
                elif row[0] == 'gui_dark_theme'      : self.gui_dark_theme      = setting_value
                elif row[0] == 'override_kbtype'     : self.override_kbtype     = row[1]
                elif row[0] == 'optspec_layout'      : self.optspec_layout      = row[1]
                elif row[0] == 'forced_numpad'       : self.forced_numpad       = setting_value
                elif row[0] == 'media_arrows_fix'    : self.media_arrows_fix    = setting_value
                elif row[0] == 'multi_lang'          : self.multi_lang          = setting_value
                elif row[0] == 'Caps2Cmd'            : self.Caps2Cmd            = setting_value
                elif row[0] == 'Caps2Esc_Cmd'        : self.Caps2Esc_Cmd        = setting_value
                elif row[0] == 'Enter2Ent_Cmd'       : self.Enter2Ent_Cmd       = setting_value
                elif row[0] == 'ST3_in_VSCode'       : self.ST3_in_VSCode       = setting_value

            db_cursor.execute('''
                SELECT layout_code, variant_code from mru_layouts 
                ORDER BY timestamp DESC 
                LIMIT 1;
                ''')

            row_mru_layout = db_cursor.fetchone()     # redundant limit since query limited to one row
            if row_mru_layout:
                # Convert MRU Layouts record columns back to a Python tuple
                self.mru_layout     = (row_mru_layout[0], row_mru_layout[1])
            else:
                self.mru_layout     = ('us', 'default')

        # Compare the current settings with the last settings, and 
        # update last_settings if they are different
        self.current_settings = self.get_settings_list()
        if self.last_settings != self.current_settings:
            self.last_settings = self.current_settings
            if not self.first_run:
                debug(f'User preferences database modified... loading new settings...')
                if xwaykeyz.lib.logger.VERBOSE:
                    debug(self, ctx="CG")   # print out the changed settings when verbose logging
            else:
                self.first_run = False

    def get_settings_list(self):
        # get all attributes from the object
        all_attributes = [attr for attr in dir(self) 
                            if not callable(getattr(self, attr)) and 
                            not attr.startswith("__")]

        # Filter attributes further only if a specific attribute should be ignored.
        # Removed earlier list comprehension that limited data types too much.
        filtered_attributes = all_attributes

        # create a list of tuples with attribute name and value pairs
        settings_list = [(attr, getattr(self, attr)) for attr in filtered_attributes]
        return settings_list

    def watch_synergy_log(self):
        log_dir = os.path.dirname(self.synergy_log_path)
        if not os.path.exists(log_dir):
            debug("No Synergy log folder found. No log observer will be engaged.")
        else:
            debug(f"Setting an observer on '{log_dir}'")
            event_handler = FileSystemEventHandler()
            event_handler.on_modified = self.on_synergy_log_modified
            event_handler.on_created = self.on_synergy_log_created
            observer = Observer()
            observer.schedule(event_handler, path=log_dir, recursive=False)
            observer.start()

    def on_synergy_log_modified(self, event: Optional[FileSystemEvent]):
        if event.src_path == self.synergy_log_path:
            self.handle_synergy_log_file_change()

    def on_synergy_log_created(self, event: Optional[FileSystemEvent]):
        if event.src_path == self.synergy_log_path:
            self.handle_synergy_log_file_change()

    def handle_synergy_log_file_change(self):
        lines = []  # prevent UnboundLocalError
        if os.path.exists(self.synergy_log_path):
            with open(self.synergy_log_path, 'r') as f:
                if self.synergy_log_last_pos == 0:
                    # Seek to a position near the end of the file
                    f.seek(0, os.SEEK_END)
                    end_pos = f.tell()
                    f.seek(max(end_pos - 1024, 0))  # Read the last ~1024 bytes
                    if f.tell() != 0:
                        f.readline()  # Skip partial line
                    lines = f.readlines()
                    self.synergy_log_last_pos = f.tell()
                else:
                    f.seek(self.synergy_log_last_pos)
                    lines = f.readlines()
                    self.synergy_log_last_pos = f.tell()  # Update the last read position
                # Track the most recent relevant screen focus state
        if lines:
            most_recent_state = None
            for line in lines:
                line = line.strip()
                if "leaving screen" in line:
                    most_recent_state = False
                elif "entering screen" in line:
                    most_recent_state = True

            if most_recent_state is not None:
                self.screen_has_focus = most_recent_state
                if self.screen_has_focus:
                    debug("Synergy log watcher detected return of screen focus.")
                else:
                    debug("Synergy log watcher detected loss of screen focus.")

    def __str__(self):
        return f"""Current settings:
        ------------------------------------------------------------------------------
        calling_module          = '{self.calling_module}'
        prefs_db_file_path      = '{self.prefs_db_file_path}'
        ------------------------------------------------------------------------------
        autostart_tray_icon     = {self.autostart_tray_icon}
        gui_dark_theme          = {self.gui_dark_theme}
        ------------------------------------------------------------------------------
        override_kbtype         = '{self.override_kbtype}'
        ------------------------------------------------------------------------------
        optspec_layout          = '{self.optspec_layout}'
        mru_layout              = {self.mru_layout}
        ------------------------------------------------------------------------------
        forced_numpad           = {self.forced_numpad}
        media_arrows_fix        = {self.media_arrows_fix}
        multi_lang              = {self.multi_lang}
        Caps2Cmd                = {self.Caps2Cmd}
        Caps2Esc_Cmd            = {self.Caps2Esc_Cmd}
        Enter2Ent_Cmd           = {self.Enter2Ent_Cmd}
        ST3_in_VSCode           = {self.ST3_in_VSCode}
        ------------------------------------------------------------------------------
        """
