import time

start = time.time()

import os
import sys

import logging
import argparse
import subprocess

import gi
from fuzzywuzzy import fuzz

gi.require_version("Gtk", "3.0")

from gi.repository import Gtk
from gi.repository import Gdk


end = time.time()

logging.basicConfig(encoding='utf-8', level=logging.DEBUG)

logging.debug(f"It took {end - start} seconds to import modules")

screen = Gdk.Screen.get_default()
screen_w = screen.get_width()
screen_h = screen.get_height()


MAX_ITEMS_LENGTH = 100
DEFAULT_WIDTH = int(screen_w * 0.3)
DEFAULT_HEIGTH = int(screen_h * 0.9)
WINDOW_TITLE = "py-gtk3-launcher"

UI_FILE_PATH = "ui.glade"
LOCK_PATH = "/tmp/pygtklauncher.lock"


def take(it, l):
    for _ in range(l):
        yield next(it)


def is_running_already():
    return os.path.isfile(LOCK_PATH)


def create_lock_file():
    with open(LOCK_PATH, "w"):
        return


def get_milliseconds():
    return time.time() * 1000


def calculate_items(all_items, user_filter, case_insensitive=False):
    def get_sorting_key(item):
        return item[1]

    items = ([item[0]]
             for item in all_items if user_filter in item[0])

    if case_insensitive:
        items = ([item[0], fuzz.ratio(user_filter.lower(), item[0].lower())]
                 for item in items)
    else:
        items = ([item[0], fuzz.ratio(user_filter, item[0])]
                 for item in items)

    sorted_items = sorted(items, key=get_sorting_key, reverse=True)

    return sorted_items[0:50]


def run_command(cmd, *args):
    Gtk.main_quit()
    subprocess.Popen(cmd)


def echo_command(cmd, *args):
    print(cmd)
    Gtk.main_quit()


def get_executables():
    path_env = os.environ.get("PATH")
    paths = path_env.split(":")

    for path in paths:
        if not os.path.exists(path):
            continue

        try:
            for dir in os.scandir(path):
                if dir.is_file():
                    yield [f"{path}/{dir.name}"]

        except FileNotFoundError as e:
            logging.error(f"Error: {e}")
            continue


class App:
    def __init__(self, items, ui_path=UI_FILE_PATH):
        self.items = items
        self.builder = Gtk.Builder()
        self.builder.add_from_file(ui_path)

        self.executables = items

        self.window = self.builder.get_object("window")
        self.item_list = self.builder.get_object("list_store")
        self.entry = self.builder.get_object("search_input")
        self.tree = self.builder.get_object("tree_view")
        self.selection = self.tree.get_selection()

        self.tree.set_model = self.item_list
        self.tree.append_column(Gtk.TreeViewColumn("Path", Gtk.CellRendererText(), text=0))

        self.window.connect("destroy", Gtk.main_quit)
        self.window.connect("event-after", self.on_event_after)
        self.entry.connect("key-press-event", self.on_text_input)
        self.tree.connect("button-press-event", self.on_tree_click_event)
        self.selection.connect("changed", self.on_selection_change)

        self.alt_pressed = False
        self.last_keyboard_event_t = None

        start = time.time()
        for executable in self.executables[0:50]:
            self.item_list.append(executable)
        end = time.time()

        logging.debug(f"It took {end - start} seconds to append executables to gtk item list")

        self.window.set_keep_above(True)

        start = time.time()
        screen = self.window.get_screen()
        end = time.time()

        logging.debug(f"It took {end - start} seconds to get all availabe screens")

        start = time.time()
        self.window.resize(screen.get_width() * 0.3, screen.get_height() * 0.9)
        end = time.time()

        logging.debug(f"It took {end - start} seconds to resize app window")

    def show(self):
        start = time.time()
        self.window.show_all()
        end = time.time()

        logging.debug(f"It took {end - start} seconds to show gtk window")

        Gtk.main()
        

    def on_text_input(self, widget, event, *args, **kwargs):
        user_input = self.entry.get_text()

        self.item_list.clear()

        if len(user_input) < 1:
            for executable in self.executables[0:50]:
                self.item_list.append(executable)
        else:
            items = calculate_items(self.executables, user_input)

            for item in items:
                self.item_list.append([item[0]])

        self.selected_row = None
        self.tree.set_cursor(0)

    def on_selection_change(self, *args, **kwargs):
        (model, pathlist) = self.selection.get_selected_rows()

        if len(pathlist) < 1:
            return

        path = pathlist[0]

        tree_iter = model.get_iter(path)

        value = model.get_value(tree_iter, 0)

        self.selected_row = value

    def on_tree_click_event(self, widget, event, *args, **kwargs):
        logging.debug("GtkTree click event")

    def on_event_after(self, widget, event, *args, **kwargs):
        ESC_KEY = 65307
        ENTER_KEY = 65293
        ALT_KEY = 65513

        if event.type == Gdk.EventType.KEY_RELEASE:
            if event.keyval == ALT_KEY:
                logging.debug("Alt key released")
                self.alt_pressed = False
                return

        if not hasattr(event, "keyval"):
            return

        if event.keyval == ESC_KEY:
            Gtk.main_quit()

        elif event.keyval == ALT_KEY:
            self.alt_pressed = True

        elif event.keyval == ENTER_KEY:

            if self.alt_pressed:
                command = self.entry.get_text()

            elif self.selected_row is not None:
                command = self.selected_row

            else:
                command = self.entry.get_text()

            if len(command) < 1:
                return

            echo_command(command)


def main():
    if is_running_already():
        logging.error("Running already, bye")
        Gtk.main_quit()
        sys.exit(1)

    parser = argparse.ArgumentParser(description="")
    parser.add_argument("--ui", default=UI_FILE_PATH)

    args = parser.parse_args()

    logging.error(f"ARGS: {args.ui}")

    try:
        start = time.time()
        create_lock_file()
        end = time.time()

        logging.debug(f"It took {end - start} seconds to create look file")

        start = time.time()
        items = [(line.rstrip("\n"), ) for line in sys.stdin.readlines()]
        end = time.time()

        logging.debug(f"It took {end - start} seconds to read input from stdin")

        start = time.time()
        app = App(items=items, ui_path=args.ui)
        end = time.time()

        logging.debug(f"It took {end - start} seconds to instantiate App class")

        app.show()
    except Exception as e:
        logging.error(f"Error: {e}")

    finally:
        logging.error(f"Removing lock file: {LOCK_PATH}")
        os.remove(LOCK_PATH)
        Gtk.main_quit()
        sys.exit(0)


if __name__ == "__main__":
    main()
