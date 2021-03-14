import os
import subprocess

import gi

gi.require_version("Gtk", "3.0")

from gi.repository import Gtk
from gi.repository import Gdk

MAX_ITEMS_LENGTH = 100


def run_command(cmd, *args):
    Gtk.main_quit()
    p = subprocess.Popen(cmd)

    # os.system(cmd)
    # os.execl(path, *args)


def get_executables():
    path_env = os.environ.get("PATH")
    paths = path_env.split(":")

    for path in paths:
        try:
            for dir in os.scandir(path):
                if dir.is_file():
                    yield [f"{path}/{dir.name}", dir.name]

        except FileNotFoundError as e:
            print(f"Error: {e}")
            continue


class MyWindow(Gtk.Window):
    def __init__(self):
        Gtk.Window.__init__(self, title=__name__)

        self.set_size_request(400, 400)

        self.connect("event-after", self.on_event_after)

        self.vbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6)
        self.add(self.vbox)

        self.entry = Gtk.Entry()
        self.entry.connect("key-press-event", self.on_text_input)

        self.vbox.pack_start(self.entry, False, True, 0)

        self.hbox = Gtk.Box(spacing=6)
        self.vbox.pack_start(self.hbox, True, True, 0)

        self.executables = list(get_executables())

        self.item_list = Gtk.ListStore(str, str)

        for executable in self.executables[0:MAX_ITEMS_LENGTH]:
            self.item_list.append(executable)

        self.tree = Gtk.TreeView(model=self.item_list)
        self.tree.connect("button-press-event", self.on_tree_click_event)

        self.selection = self.tree.get_selection()
        self.selection.connect("changed", self.on_selection_change)

        self.hbox.pack_start(self.tree, True, True, 0)

        self.renderer = Gtk.CellRendererText()
        self.column = Gtk.TreeViewColumn("Path", self.renderer, text=0)
        self.tree.append_column(self.column)

    def on_tree_click_event(self, widget, event, *args, **kwargs):
        print("GtkTree click event")

    def on_event_after(self, widget, event, *args, **kwargs):
        ESC_KEY = 65307
        ENTER_KEY = 65293

        if not hasattr(event, "keyval"):
            return

        if event.keyval == ESC_KEY:
            print("ESC KEY PRESSED")
            Gtk.main_quit()

        elif event.keyval == ENTER_KEY:
            print("ENTER KEY PRESSED")
            (model, pathlist) = self.selection.get_selected_rows()

            if len(pathlist) > 0:
                for path in pathlist:
                    tree_iter = model.get_iter(path)
                    value = model.get_value(tree_iter, 0)

                run_command(value, " ")
            else:
                user_input = self.entry.get_text()

                if len(user_input) < 1:
                    return

                # (user_cmd, user_cmd_args) = user_input.split(" ")

                # print(len(user_cmd_args))

                # if len(user_cmd_args) < 1:
                    # user_cmd_args = " "

                # run_command(user_cmd, user_cmd_args)

                run_command(user_input)

    def on_selection_change(self, *args, **kwargs):
        print("on_selection_change")

        (model, pathlist) = self.selection.get_selected_rows()

        if len(pathlist) < 1:
            return

        path = pathlist[0]

        tree_iter = model.get_iter(path)

        value = model.get_value(tree_iter, 0)

        print(f"self.entry.set_text({value})")
        self.entry.set_text(value)
        self.update_list = False

    def on_text_input(self, widget, event, *args, **kwargs):
        user_input = self.entry.get_text()
        rows_count = 0

        self.item_list.clear()

        if len(user_input) < 1:
            for executable in self.executables[0:MAX_ITEMS_LENGTH]:
                self.item_list.append(executable)
        else:
            for executable in self.executables:
                if rows_count >= MAX_ITEMS_LENGTH:
                    break

                if user_input in executable[0]:
                    self.item_list.append(executable)
                    rows_count += 1


if __name__ == "__main__":
    win = MyWindow()
    win.connect("destroy", Gtk.main_quit)
    win.show_all()
    Gtk.main()
