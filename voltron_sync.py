"""
voltron_sync.py

A plugin for Binary Ninja to synchronise the currently selected instruction with
the instruction pointer in a debugger via Voltron. Also marks addresses with
breakpoints set in the debugger by adding a comment.

Install per instructions here:
https://github.com/Vector35/binaryninja-api/tree/master/python/examples

Documentation here: https://github.com/snare/binja/blob/master/README.md

Note: requires the current version of Voltron from GitHub here:
https://github.com/snare/voltron
"""

from binaryninja import *
import voltron
from threading import Thread
from voltron.core import Client
from voltron.plugin import api_request

log = voltron.setup_logging()
client = None
last_addrs = []


def sync(view):
    global client
    if not client:
        print("Starting synchronisation with Voltron")

        def build_requests():
            return [
                api_request('registers', registers=['pc'], block=True),
                api_request('breakpoints', block=True),
            ]

        def callback(results):
            global last_addrs
            if client and len(results):
                if results[0].registers:
                    view.file.navigate(view.file.view, results[0].registers.values()[0])

                if results[1].breakpoints:
                    addrs = [l['address'] for s in [bp['locations'] for bp in results[1].breakpoints] for l in s]

                    # add comments to all the breakpoints currently set in the debugger
                    for addr in addrs:
                        func = view.get_function_at(view.platform, view.get_previous_function_start_before(addr))
                        if func:
                            comment = func.get_comment_at(addr)
                            func.set_comment(addr, (comment.replace('[breakpoint]', '') + " [breakpoint]").strip())

                    # remove comments from any addresses that had breakpoints the last time we updated, but don't now
                    for addr in set(last_addrs) - set(addrs):
                        func = view.get_function_at(view.platform, view.get_previous_function_start_before(addr))
                        if func:
                            comment = func.get_comment_at(addr)
                            func.set_comment(addr, comment.replace('[breakpoint]', '').strip())

                    # save this set of breakpoint addresses for next time
                    last_addrs = addrs

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
