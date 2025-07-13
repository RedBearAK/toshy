#!/usr/bin/env python3

import os
import sys
import signal
import sqlite3
import tkinter as tk
import xml.etree.ElementTree as ET

# from xkbregistry import rxkb    # not supported on older Linux distros

from tkinter import font
from tkinter import messagebox as MBX
from toshy_common.settings_class import Settings, debug


#########################################################################
def signal_handler(sig, frame):
    if sig in (signal.SIGINT, signal.SIGQUIT):
        # Perform any cleanup code here before exiting
        # traceback.print_stack(frame)
        debug(f'\nSIGINT or SIGQUIT received. Exiting.\n')
        sys.exit(0)

signal.signal(signal.SIGINT,    signal_handler)
signal.signal(signal.SIGQUIT,   signal_handler)
#########################################################################
# Let signal handler be defined and called before other things ^^^^^^^


current_folder_path = os.path.abspath(os.path.dirname(__file__))
cnfg = Settings(current_folder_path)
cnfg.watch_database()
cnfg.load_settings()

print(f"Current mru_layout setting: {cnfg.mru_layout}")



def print_all_records_from_database(cur: sqlite3.Cursor):
    cur.execute("SELECT * FROM LayoutInfo ORDER BY layout_name, variant_name")
    rows = cur.fetchall()
    print("Total Records: ", len(rows))
    for row in rows:
        print(row)


# def compare_databases(cur1: sqlite3.Cursor, cur2: sqlite3.Cursor):
#     cur1.execute("SELECT layout_fullname, layout_name, variant_name, layout_description, layout_brief FROM LayoutInfo ORDER BY layout_fullname, variant_name")
#     rows1 = cur1.fetchall()

#     cur2.execute("SELECT layout_fullname, layout_name, variant_name, layout_description, layout_brief FROM LayoutInfo ORDER BY layout_fullname, variant_name")
#     rows2 = cur2.fetchall()

#     # Simple comparison
#     if rows1 == rows2:
#         print("Databases are identical.")
#     else:
#         print("Differences found between databases.")
#         # For detailed differences, you could use a loop or a more sophisticated method to log specific differences.
#         for row1, row2 in zip(rows1, rows2):
#             if row1 != row2:
#                 print(f"Difference:\n\tFrom DB1: {row1}\n\tFrom DB2: {row2}")


def setup_layout_database():
    run_tmp_dir = os.environ.get('XDG_RUNTIME_DIR', '/tmp')
    db_file_path = os.path.join(run_tmp_dir, 'toshy_layout_info.sqlite')

    if os.path.exists(db_file_path):
        os.remove(db_file_path)     # FOR DEBUGGING, probably can remove this later

    # cnxn = sqlite3.connect(db_file_path)
    cnxn = sqlite3.connect(':memory:')
    cur = cnxn.cursor()

    # Create a table
    cur.execute('''
    CREATE TABLE IF NOT EXISTS LayoutInfo (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        layout_fullname TEXT,
        layout_name TEXT,
        variant_name TEXT,
        layout_description TEXT,
        layout_brief TEXT
    )
    ''')
    cnxn.commit()
    return cnxn, cur


# def parse_xkb_layouts_and_variants_with_xkbregistry(cnxn: sqlite3.Connection, cur: sqlite3.Cursor):
#     ctx = rxkb.Context()

#     # Iterate through all layouts available in the context
#     for layout_fullname, layout in ctx.layouts.items():
#         xkb_layout: rxkb.Layout = layout     # type hint to help out VSCode syntax highlighting
#         layout_name = xkb_layout.name
#         layout_description = xkb_layout.description
#         variant_name = xkb_layout.variant if xkb_layout.variant else None
#         layout_brief = xkb_layout.brief

#         # SQL to insert layout/variant information
#         sql_insert_layout_variant = (
#             'INSERT INTO LayoutInfo ('
#             'layout_fullname, '
#             'layout_name, variant_name, '
#             'layout_description, '
#             'layout_brief'
#             ') VALUES (?, ?, ?, ?, ?)'
#         )
#         try:
#             cur.execute(sql_insert_layout_variant, (layout_fullname,
#                                                     layout_name, variant_name,
#                                                     layout_description,
#                                                     layout_brief))
#         except sqlite3.Error as e:
#             print(f"An error occurred while inserting layout: \n{e}")

#     cnxn.commit()
#     # Check the count of inserted records for verification
#     cur.execute("SELECT COUNT(*) FROM LayoutInfo")
#     print("Total records in LayoutInfo:", cur.fetchone()[0])

#     print_all_records_from_database(cur)


def parse_xkb_layouts_and_variants_from_xml(cnxn: sqlite3.Connection, cur: sqlite3.Cursor):
    # Path to the evdev.xml file
    xkb_config_path = '/usr/share/X11/xkb/rules/evdev.xml'
    tree = ET.parse(xkb_config_path)
    root = tree.getroot()

    # SQL to insert layout/variant information
    sql_insert_layout_variant = (
        'INSERT INTO LayoutInfo ('
        'layout_fullname, layout_name, variant_name, '
        'layout_description, layout_brief'
        ') VALUES (?, ?, ?, ?, ?)'
    )

    # Iterate through all layouts in the XML file
    for layout in root.findall(".//layout"):
        layout_name = layout.find('configItem/name').text
        layout_description = layout.find('configItem/description').text
        layout_brief = layout.find('configItem/shortDescription')
        layout_brief = layout_brief.text if layout_brief is not None else None

        # Base layout has no variant name, so its "fullname" is the same as its "name"
        layout_fullname = layout_name

        # Use None for variant_name to indicate it's the base layout
        cur.execute(sql_insert_layout_variant, (layout_fullname, layout_name, None, layout_description, layout_brief))

        # Process variants if any
        for variant in layout.findall('.//variant'):
            variant_name = variant.find('configItem/name').text
            variant_description = variant.find('configItem/description').text
            variant_brief = variant.find('configItem/shortDescription')
            variant_brief = variant_brief.text if variant_brief is not None else layout_brief

            # Full name for variant
            variant_fullname = layout_name + ("" if variant_name is None else f"({variant_name})")

            # Insert variant with specific variant name
            cur.execute(sql_insert_layout_variant, (variant_fullname, layout_name, variant_name, variant_description, variant_brief))

    cnxn.commit()
    # Optionally print all records for verification
    # print_all_records_from_database(cur)


class LayoutSelector(tk.Tk):
    def __init__(self, db_connection: sqlite3.Connection, cursor: sqlite3.Cursor):
        super().__init__()
        self.cnxn = db_connection
        self.cursor = cursor
        self.title("Toshy Layout Selector")
        self.geometry("600x500")

        # Set up UI components
        self.setup_ui()

        # Load layouts into the listbox
        self.load_layouts()

    def setup_ui(self):

        # Create and pack frames
        self.button_frame = tk.Frame(self, padx=10, pady=10)
        self.button_frame.pack(side=tk.BOTTOM, fill=tk.X)
        self.layout_frame = tk.Frame(self, padx=10, pady=10)
        self.layout_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        # self.variant_frame = tk.Frame(self, padx=10, pady=10)
        # self.variant_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        label_font = font.Font(family="Helvetica", size=12, weight="bold")
        listbox_font = font.Font(family="Helvetica", size=11 , weight="bold")

        # Search entry setup
        self.search_entry_lbl = tk.Label(self.layout_frame, text="Search for Layout", font=label_font)
        self.search_entry_lbl.pack(side=tk.TOP, fill=tk.X)
        self.search_entry = tk.Entry(self.layout_frame, font=listbox_font)
        self.search_entry.pack(side=tk.TOP, fill=tk.X, padx=5, pady=5)
        self.search_entry.bind('<KeyRelease>', self.filter_layouts)

        # Create listboxes with labels
        self.layout_label = tk.Label(self.layout_frame, text="Layout (Variant)", font=label_font)
        # self.variant_label = tk.Label(self.variant_frame, text="Layout Variant", font=label_font)
        self.layout_label.pack(side=tk.TOP, fill=tk.X)
        # self.variant_label.pack(side=tk.TOP, fill=tk.X)

        self.layout_listbox = tk.Listbox(self.layout_frame, font=listbox_font, exportselection=False)
        # self.variant_listbox = tk.Listbox(self.variant_frame, font=listbox_font, exportselection=False)0
        self.layout_listbox.pack(side=tk.TOP, fill=tk.BOTH, expand=True, padx=5, pady=5)
        # self.variant_listbox.pack(side=tk.TOP, fill=tk.BOTH, expand=True, padx=5, pady=5)

        # BETA software warning text
        self.beta_warning_lbl = tk.Label(
            self.button_frame, 
            text='BETA - DIALOG DOES NOTHING MEANINGFUL YET!!!', 
            font=label_font, foreground='red')
        self.beta_warning_lbl.pack(side=tk.LEFT, padx=10, pady=10)

        # Submit button
        self.submit_button = tk.Button(self.button_frame, text="Submit", font=label_font, 
                                        command=self.submit_selection)
        self.submit_button.pack(side=tk.RIGHT, padx=10, pady=10)

        # self.layout_listbox.bind('<<ListboxSelect>>', self.on_layout_select)

    def load_layouts(self):
        query = "SELECT DISTINCT layout_description FROM LayoutInfo ORDER BY layout_description"
        self.cursor.execute(query)
        rows = self.cursor.fetchall()
        if rows:
            for row in rows:
                self.layout_listbox.insert(tk.END, row[0])
        else:
            MBX.showinfo("Database Empty", "No layout data found in the database.")

    def filter_layouts(self, event):
        search_term = self.search_entry.get().strip().lower()
        if search_term:
            query = "SELECT DISTINCT layout_description FROM LayoutInfo WHERE layout_description LIKE ? ORDER BY layout_description"
            self.cursor.execute(query, ('%' + search_term + '%',))
        else:
            query = "SELECT DISTINCT layout_description FROM LayoutInfo ORDER BY layout_description"
            self.cursor.execute(query)
        
        rows = self.cursor.fetchall()
        self.layout_listbox.delete(0, tk.END)  # Clear the current list
        for row in rows:
            self.layout_listbox.insert(tk.END, row[0])

    def on_layout_select(self, event):
        if self.layout_listbox.curselection():
            selected_description = self.layout_listbox.get(self.layout_listbox.curselection()[0])
            self.variant_listbox.delete(0, tk.END)
            query = "SELECT layout_description FROM LayoutInfo WHERE layout_description = ?"
            self.cursor.execute(query, (selected_description,))
            variants = self.cursor.fetchall()

            # Populate the variant listbox
            for row in variants:
                self.variant_listbox.insert(tk.END, row[0])

            # Automatically select the first variant in the list if any variants were added
            if variants:
                self.variant_listbox.selection_set(0)  # Select the first item in the list

    def submit_selection(self):

        if self.layout_listbox.curselection(): # and self.variant_listbox.curselection():

            layout_description = self.layout_listbox.get(self.layout_listbox.curselection()[0])
            # variant_description = self.variant_listbox.get(self.variant_listbox.curselection()[0])

            query = (   'SELECT '
                        'layout_fullname, '
                        'layout_name, '
                        'variant_name, '
                        'layout_brief '
                        'FROM LayoutInfo '
                        'WHERE layout_description = ?'  )
            self.cursor.execute(query, (layout_description,))
            layout_fullname, layout_name, variant_name, layout_brief = self.cursor.fetchone()

            # self.cursor.execute("SELECT layout_name FROM LayoutInfo WHERE layout_description = ?", (layout_description,))
            # layout_name = self.cursor.fetchone()[0]

            # self.cursor.execute("SELECT variant_name FROM LayoutInfo WHERE layout_description = ?", (layout_description,))
            # variant_name = self.cursor.fetchone()[0]

            print()
            output_str = (  f"Layout Description:   '{layout_description}'\n"
                            f"Layout Fullname:      '{layout_fullname}'\n"
                            f"Layout Name:          '{layout_name}'\n"
                            f"Variant Name:         '{variant_name}'\n"
                            f"Layout Brief:         '{layout_brief}'")
            print(output_str)

            new_layout_tup = (layout_name, variant_name)

            cnfg.mru_layout = new_layout_tup
            cnfg.save_settings()

            print()
            print(f"New mru_layout setting: {cnfg.mru_layout}")
            # MBX.showinfo("Selection", output_str)
            print()
            sys.exit(0)

        else:
            MBX.showinfo("Selection Error", "Please select both a layout and a variant.")

    def on_close(self):
        self.destroy()
        self.cnxn.close()  # Close the database connection on exit


if __name__ == '__main__':
    # # Connection for the xkbregistry parsing function
    # cnxn1, cur1 = setup_layout_database()
    # parse_xkb_layouts_and_variants_with_xkbregistry(cnxn1, cur1)

    # # Connection for the XML parsing function
    # cnxn2, cur2 = setup_layout_database()
    # parse_xkb_layouts_and_variants_from_xml(cnxn2, cur2)

    # # Compare databases
    # compare_databases(cur1, cur2)

    # # Close connections
    # cnxn1.close()
    # cnxn2.close()


    cnxn, cur = setup_layout_database()
    parse_xkb_layouts_and_variants_from_xml(cnxn, cur)
    app = LayoutSelector(cnxn, cur)
    app.mainloop()
