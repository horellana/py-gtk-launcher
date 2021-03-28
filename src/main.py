import os
import sys
import time
import logging
import subprocess
from functools import cache

import gi
from fuzzywuzzy import fuzz

gi.require_version("Gtk", "3.0")

from gi.repository import Gtk
from gi.repository import Gdk

logging.basicConfig(encoding='utf-8', level=logging.ERROR)

screen = Gdk.Screen.get_default()
screen_w = screen.get_width()
screen_h = screen.get_height()


MAX_ITEMS_LENGTH = 100
DEFAULT_WIDTH = int(screen_w * 0.3)
DEFAULT_HEIGTH = int(screen_h * 0.9)
WINDOW_TITLE = "py-gtk3-launcher"


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

    return list((sorted_items))


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


class MyWindow(Gtk.Window):
    def __init__(self, items=tuple(list(get_executables()))):
        Gtk.Window.__init__(self, title=WINDOW_TITLE)

        self.set_default_size(DEFAULT_WIDTH, DEFAULT_HEIGTH)

        self.connect("event-after", self.on_event_after)

        self.vbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6)
        self.add(self.vbox)

        self.entry = Gtk.Entry()
        self.entry.connect("key-press-event", self.on_text_input)

        self.vbox.pack_start(self.entry, False, True, 0)

        self.executables = items

        logging.debug(f"Found {len(self.executables)} executables")

        self.item_list = Gtk.ListStore(str)

        for executable in self.executables:
            self.item_list.append(executable)

        self.tree = Gtk.TreeView(model=self.item_list)
        self.tree.connect("button-press-event", self.on_tree_click_event)

        self.scroll = Gtk.ScrolledWindow()
        self.scroll.add(self.tree)

        self.vbox.pack_start(self.scroll, True, True, 0)

        self.selection = self.tree.get_selection()
        self.selection.connect("changed", self.on_selection_change)

        self.renderer = Gtk.CellRendererText()
        self.column = Gtk.TreeViewColumn("Path", self.renderer, text=0)

        self.tree.append_column(self.column)

        self.alt_pressed = False
        self.last_keyboard_event_t = None

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
            logging.debug("ESC KEY PRESSED")
            Gtk.main_quit()

        elif event.keyval == ALT_KEY:
            logging.debug("Alt key pressed")
            self.alt_pressed = True

        elif event.keyval == ENTER_KEY:
            logging.debug("ENTER KEY PRESSED")

            if self.alt_pressed:
                command = self.entry.get_text()

            elif self.selected_row is not None:
                command = self.selected_row

            else:
                command = self.entry.get_text()

            if len(command) < 1:
                return

            echo_command(command)
            # run_command(command)

    def on_selection_change(self, *args, **kwargs):
        logging.debug("on_selection_change")

        (model, pathlist) = self.selection.get_selected_rows()

        if len(pathlist) < 1:
            return

        path = pathlist[0]

        tree_iter = model.get_iter(path)

        value = model.get_value(tree_iter, 0)

        self.selected_row = value

    def on_text_input(self, widget, event, *args, **kwargs):
        user_input = self.entry.get_text()

        self.item_list.clear()

        if len(user_input) < 1:
            for executable in self.executables:
                self.item_list.append(executable)
        else:
            items = calculate_items(self.executables, user_input)
            logging.debug(f"{len(items)} after filter")

            for item in items:
                self.item_list.append([item[0]])

        self.selected_row = None
        self.tree.set_cursor(0)


def main():
    items = [(line.rstrip("\n"), )  for line in sys.stdin.readlines()]

    win = MyWindow(items=items)
    win.connect("destroy", Gtk.main_quit)
    win.show_all()
    Gtk.main()


if __name__ == "__main__":
    main()
