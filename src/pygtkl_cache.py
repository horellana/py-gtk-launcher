import os
import queue
import logging
import threading

from inotify_simple import INotify, flags

logging.basicConfig(level=logging.DEBUG)

CACHE_PATH = f"{os.environ['HOME']}/.cache/pygtkl"

q = queue.Queue()


def get_cache():
    path_env = os.environ.get("PATH")
    paths = path_env.split(":")

    result = set()

    for path in paths:
        if not os.path.exists(path):
            continue

        try:
            for dir in os.scandir(path):
                if dir.is_file():
                    result.add(f"{path}/{dir.name}")
        except FileNotFoundError as e:
            logging.error(f"{e}")
            continue

    return result


cache = get_cache()


def handle_inotify_actions():
    while True:
        try:
            item = q.get()
            path = item["path"]
            action = item["action"]

            logging.info(f"Inotify actions handler: {path} - {action}")

            valid_action = True

            if action == "flags.DELETE":
                logging.info(f"Removing {path} from cache")
                cache.remove(path)

            elif action == "flags.CREATE":
                cache.add(path)

            else:
                logging.error(f"Unknown action: \'{action}\'")
                valid_action = False

            if valid_action:
                logging.info("Updating cache")
                with open(CACHE_PATH, "w") as fh:
                    logging.info("Updating cache...")
                    for path in cache:
                        print(path, file=fh)
                    logging.info("Cache updated")

        except Exception as e:
            logging.error(f"{e}")


def init_cache():
    with open(CACHE_PATH, "w") as fh:
        for path in cache:
            print(path, file=fh)


def get_watched_directories():
    return os.environ["PATH"].split(":")


def watch_directory(directory):
    inotify = INotify()
    watch_flags = flags.CREATE | flags.DELETE

    logging.info(f"Starting inotify on directory: {directory}")
    try:
        inotify.add_watch(directory, watch_flags)
    except Exception as e:
        logging.error(f"{e}")
        return

    while True:
        for event in inotify.read():
            for flag in flags.from_mask(event.mask):
                logging.info(f"Event on {directory}: {event.name} - {flag}")
                item = {"path": f"{directory}/{event.name}",
                        "action": str(flag)}

                q.put(item)


def main():
    init_cache()

    for directory in get_watched_directories():
        t = threading.Thread(target=watch_directory, args=(directory,))
        t.start()

    handle_inotify_actions()


if __name__ == "__main__":
    main()
