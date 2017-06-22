"""
binjatron.py

A plugin for Binary Ninja to integrate Binary Ninja with Voltron.

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
from scruffy import ConfigFile, PackageFile
import sys

log = voltron.setup_logging()
client = Client()
last_bp_addrs = []
last_pc_addr = 0
last_pc_addr_colour = 0
syncing = False
vers = None
slide = 0
notification = None
sync_callbacks = []
mute_errors_after = 3

config = ConfigFile('~/.binjatron.conf', defaults=PackageFile('defaults.yaml'), apply_env=True, env_prefix='BTRON')
config.load()

bp_colour = enums.HighlightStandardColor(config.bp_colour)
pc_colour = enums.HighlightStandardColor(config.pc_colour)
no_colour = enums.HighlightStandardColor(0)

def _get_function(view, address):
    func = view.get_function_at(address)
    if func is None:
        return view.get_function_at(view.get_previous_function_start_before(address))
    return func

def sync(view):
    global syncing, vers, notification

    def build_requests():
        return [
            api_request('registers', registers=['pc'], block=True),
            api_request('breakpoints', block=True),
        ]

    def callback(results=[], error=None):
        global last_bp_addrs, last_pc_addr, last_pc_addr_colour, sync_callbacks, mute_errors_after, syncing

        if error:
            if mute_errors_after > 0:
                log_error("Error synchronising: {}".format(error))
            elif mute_errors_after == 0:
                log_alert("Voltron encountered three sync errors in a row. Muting errors until the next succesful sync.")
                syncing = False
            mute_errors_after -= 1
        else:
            if(mute_errors_after < 0):
                log_info("Sync restored after {} attempts".format(mute_errors_after * -1))
                syncing = True
            mute_errors_after = 3
            if client and len(results):
                if results[1].breakpoints:
                    addrs = [l['address'] - slide for s in [bp['locations'] for bp in results[1].breakpoints] for l in s]

                    # add colours to all the breakpoints currently set in the debugger
                    for addr in addrs:
                        func = _get_function(view, addr)
                        if func:
                            func.set_auto_instr_highlight(addr, bp_colour)

                    # remove colours from any addresses that had breakpoints the last time we updated, but don't now
                    for addr in set(last_bp_addrs) - set(addrs):
                        func = _get_function(view, addr)
                        if func:
                            func.set_auto_instr_highlight(addr, no_colour)

                    # save this set of breakpoint addresses for next time
                    last_bp_addrs = addrs

                elif last_bp_addrs:
                    replace_breakpoints = show_message_box(
                        'New Session',
                        'The Voltron instance currently syncing reports no breakpoints set, but breakpoints have been set in Binary Ninja. Restore these breakpoints?',
                        buttons=enums.MessageBoxButtonSet.YesNoButtonSet)

                    if replace_breakpoints:
                        for addr in set(last_bp_addrs):
                            set_breakpoint(view, addr)
                    else:
                        for addr in set(last_bp_addrs):
                            func = _get_function(view, addr)
                            if func:
                                func.set_auto_instr_highlight(addr, no_colour)
                        last_bp_addrs = []

                if results[0].registers:
                    # get the current PC from the debugger
                    addr = results[0].registers.values()[0] - slide

                    # find the function where that address is
                    func = _get_function(view, addr)

                    if last_pc_addr:
                        # update the highlight colour of the previous PC to its saved value
                        _get_function(view, last_pc_addr).set_auto_instr_highlight(last_pc_addr, last_pc_addr_colour)

                    # save the PC and current colour for that instruction
                    last_pc_addr_colour = func.get_instr_highlight(addr)
                    last_pc_addr = addr

                    # update the highlight colour to show the current PC
                    func.set_auto_instr_highlight(addr, pc_colour)

                    for cb, _ in sync_callbacks:
                        cb(results)
                    sync_callbacks = filter(lambda cbt: not cbt[1], sync_callbacks)

                elif not results[1].breakpoints or (results[0].message == 'No such target'): # Clear the program counter highlight if the program isn't running
                    if last_pc_addr:
                        # update the highlight colour of the previous PC to its saved value
                        _get_function(view, last_pc_addr).set_auto_instr_highlight(last_pc_addr, last_pc_addr_colour)




    if not syncing:
        try:
            log_info("Starting synchronisation with Voltron")

            # register for notifications
            notification = BinjatronNotification(view)
            view.register_notification(notification)

            # Start the client
            vers = client.perform_request("version")
            client.start(build_requests=build_requests, callback=callback)
            syncing = True
        except:
            log_info("Couldn't connect to Voltron")
    else:
        log_info("Already synchronising with Voltron")


def stop(view):
    global syncing, client, slide, notification

    if syncing:
        log_info("Stopping synchronisation with Voltron")

        # clear any colours we've set
        if last_pc_addr:
            func = _get_function(view, last_pc_addr)
            func.set_auto_instr_highlight(last_pc_addr, last_pc_addr_colour)

        for addr in last_bp_addrs:
            func = _get_function(view, addr)
            func.set_auto_instr_highlight(addr, no_colour)

        # stop the voltron client
        client.stop()
        client = Client()

        # unregister notifications
        view.unregister_notification(notification)
        notification = None

        syncing = False
        slide = 0
    else:
        log_alert("Not synchronising with Voltron")


def set_breakpoint(view, address):
    global vers

    try:
        if not vers:
            vers = client.perform_request("version")

        # build a breakpoint set command for the debugger
        if 'lldb' in vers.host_version:
            cmd = "breakpoint set -a 0x{:x}".format(address + slide)
        elif 'gdb' in vers.host_version:
            cmd = "break *0x{:x}".format(address + slide)
        else:
            raise Exception("Debugger host version {} not supported".format(vers.host_version))

        # send it
        res = client.perform_request("command", command=cmd, block=False)
        if res.is_error:
            raise Exception("Failed to set breakpoint: {}".format(res))

        # update the voltron views
        res = client.perform_request("command", command="voltron update", block=False)

        # add colour in binja
        func = _get_function(view, address)
        if func:
            func.set_auto_instr_highlight(address, bp_colour)
    except:
        log_alert("Failed to set breakpoint")


def delete_breakpoint(view, address):
    global vers

    try:
        if not vers:
            vers = client.perform_request("version")

        # get a list of breakpoints from the debugger and find the one we're after
        res = client.perform_request("breakpoints")
        bp_id = None
        if res.is_success:
            for bp in res.breakpoints:
                for location in bp['locations']:
                    if address == location['address'] - slide:
                        bp_id = bp['id']
                        break

        # build a breakpoint delete command for the debugger
        if 'lldb' in vers.host_version:
            cmd = "breakpoint delete {}".format(bp_id)
        elif 'gdb' in vers.host_version:
            cmd = "delete {}".format(bp_id)
        else:
            raise Exception("Debugger host version {} not supported".format(vers.host_version))

        # send it
        res = client.perform_request("command", command=cmd, block=False)
        if res.is_error:
            raise Exception("Failed to delete breakpoint: {}".format(res))

        # update the voltron views
        res = client.perform_request("command", command="voltron update", block=False)

        # remove the breakpoint colour in binja
        func = _get_function(view, address)
        if func:
            func.set_auto_instr_highlight(address, no_colour)
    except:
        log_alert("Failed to delete breakpoint")


def set_slide(view, address):
    global slide

    if 'async' in vers.capabilities:
        # if we're using a debugger that supports async, grab the current PC
        res = client.perform_request("registers", registers=["pc"], block=False)
        pc = res.registers.values()[0]
    else:
        # otherwise we just have to use the last PC we saved
        if last_pc_addr == 0:
            log_alert("Your debugger does not support async API access, and Binary Ninja hasn't received any data from it yet. Please run the `voltron update` command in the debugger, or step the debugger, or let it run until it hits a breakpoint so Binjatron can get the register state.")
        else:
            pc = last_pc_addr

    slide = pc - address

    # if we have an async debugger, we can update now. otherwise we'll have to wait for the user to step again
    if 'async' in vers.capabilities:
        client.update()


def clear_slide(view):
    global slide
    slide = 0

def custom_request(request, args, alert=True):
    """ Allows external code to pass arbitrary commands to the voltron client
    request: type of request - usually 'command'
    args: dict containing keyword arguments for the request
    alert: boolean indicating whether errors should result in a popup or simply
        log to the console. Defaults to True."""
    global vers
    client_result = None
    try:
        if not vers:
            vers = client.perform_request("version")

        if 'lldb' in vers.host_version or 'gdb' in vers.host_version:
            cmd = request
        else:
            raise Exception("Debugger host version {} not supported".format(vers.host_version))

        client_result = client.perform_request(request, **args)
        if client_result.is_error:
            raise Exception("\"" + cmd + "\": {}".format(client_result))

        # update the voltron views
        client.perform_request("command", command="voltron update", block=False)
    except:
        log_info(sys.exc_info()[1])
        if alert:
            log_alert(request + " failed: " + str(args))
        else:
            log_info(request + " failed: " + str(args))

    # Even if we encountered an exception, we return the results so external code can
    # handle the error if necessary.
    return client_result

def register_sync_callback(cb, should_delete=False):
    """ Allows external code to register a callback to be run upon a succesful sync
    cb: function pointer to the callback. Gets `results` as an argument
    should_delete: boolean indicating whether the callback should be removed from
        the list after a single call. Defaults to False. """
    global sync_callbacks
    sync_callbacks.append((cb, should_delete))

def sync_state():
    """ Return the sync state so that external code can determine whether voltron is currently syncing with binjatron """
    return syncing

class BinjatronNotification(BinaryDataNotification):
    def __init__(self, view):
        self.view = view

    def data_written(self, view, offset, length):
        log_info("data_written({:x}, {})".format(offset, length))

        # get the data that was written
        data = view.read(offset, length)

        # write it to memory in the debugger
        res = client.perform_request("write_memory", address=offset + slide, value=data, block=False)
        if not res.is_success:
            log_error("Failed to write memory in debugger: {}".format(res))

        # update the voltron views
        res = client.perform_request("command", command="voltron update", block=False)

    def data_inserted(self, view, offset, length):
        log_info("data_inserted()")

    def data_removed(self, view, offset, length):
        log_info("data_removed()")


PluginCommand.register("Voltron: Sync", "", sync)
PluginCommand.register("Voltron: Stop syncing", "", stop)
PluginCommand.register_for_address("Voltron: Breakpoint set", "", set_breakpoint)
PluginCommand.register_for_address("Voltron: Breakpoint clear", "", delete_breakpoint)
PluginCommand.register_for_address("Voltron: Slide set", "", set_slide)
PluginCommand.register("Voltron: Slide clear", "", clear_slide)
