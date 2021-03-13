import os
import gi

gi.require_version("Gtk", "3.0")
from gi.repository import Gtk

MAX_ITEMS_LENGTH = 100


def run_command(path, *args):
    Gtk.main_quit()
    os.execl(path, *args)


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

        self.vbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6)
        self.add(self.vbox)

        self.entry = Gtk.Entry()
        self.entry.connect("changed", self.on_text_input)
        self.vbox.pack_start(self.entry, False, True, 0)

        self.hbox = Gtk.Box(spacing=6)
        self.vbox.pack_start(self.hbox, True, True, 0)

        self.executables = list(get_executables())

        self.item_list = Gtk.ListStore(str, str)

        for executable in self.executables[0:100]:
            self.item_list.append(executable)

        self.tree = Gtk.TreeView(model=self.item_list)
        self.selection = self.tree.get_selection()
        self.selection.connect("changed", self.on_selection_change)

        self.hbox.pack_start(self.tree, True, True, 0)

        self.renderer = Gtk.CellRendererText()
        self.column = Gtk.TreeViewColumn("Path", self.renderer, text=0)
        self.tree.append_column(self.column)

    def on_selection_change(self, *args, **kwargs):
        (model, pathlist) = self.selection.get_selected_rows()

        if len(pathlist) > 0:
            for path in pathlist:
                tree_iter = model.get_iter(path)
                value = model.get_value(tree_iter, 0)

                run_command(value, " ")
        else:
            user_input = self.entry.get_text()
            (user_cmd, user_cmd_args) = user_input.split(" ")

            print(len(user_cmd_args))

            if len(user_cmd_args) < 1:
                user_cmd_args = " "

            run_command(user_cmd, user_cmd_args)

    def on_text_input(self, *args, **kwargs):
        user_input = self.entry.get_text()

        items = [e for e in self.executables if user_input in e[0]]

        if len(items) > MAX_ITEMS_LENGTH:
            items = items[0:MAX_ITEMS_LENGTH]

        self.item_list.clear()

        for item in items:
            self.item_list.append(item)


if __name__ == "__main__":
    win = MyWindow()
    win.connect("destroy", Gtk.main_quit)
    win.show_all()
    Gtk.main()
