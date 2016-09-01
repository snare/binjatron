from binaryninja import *
import voltron
from threading import Thread
from voltron.core import Client
from voltron.plugin import api_request

log = voltron.setup_logging()
client = None


def sync(view):
    global client
    if not client:
        print("Starting synchronisation with Voltron")

        def build_requests():
            return [api_request('registers', registers=['pc'], block=True)]

        def callback(results):
            if client and len(results) and results[0].registers:
                view.file.navigate(view.file.view, results[0].registers.values()[0])

        client = Client(build_requests=build_requests, callback=callback)
        client.start()


def stop(*args):
    global client
    if client:
        print("Stopping synchronisation with Voltron")
        client.stop()
        client = None


PluginCommand.register("Sync with Voltron", "", sync)
PluginCommand.register("Stop syncing with Voltron", "", stop)
