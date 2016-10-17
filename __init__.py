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

log = voltron.setup_logging()
client = Client()
last_bp_addrs = []
last_pc_addr = 0
last_pc_addr_colour = 0
syncing = False
vers = None
slide = 0

config = ConfigFile('~/.binjatron.conf', defaults=PackageFile('defaults.yaml'), apply_env=True, env_prefix='BTRON')
config.load()


def sync(view):
    global syncing, vers

    def build_requests():
        return [
            api_request('registers', registers=['pc'], block=True),
            api_request('breakpoints', block=True),
        ]

    def callback(results=[], error=None):
        global last_bp_addrs, last_pc_addr, last_pc_addr_colour

        if error:
            log_error("Error synchronising: {}".format(error))
        else:
            if client and len(results):
                if results[1].breakpoints:
                    addrs = [l['address'] - slide for s in [bp['locations'] for bp in results[1].breakpoints] for l in s]

                    # add colours to all the breakpoints currently set in the debugger
                    for addr in addrs:
                        func = view.get_function_at(view.platform, view.get_previous_function_start_before(addr))
                        if func:
                            func.set_user_instr_highlight(func.arch, addr, config.bp_colour)

                    # remove colours from any addresses that had breakpoints the last time we updated, but don't now
                    for addr in set(last_bp_addrs) - set(addrs):
                        func = view.get_function_at(view.platform, view.get_previous_function_start_before(addr))
                        if func:
                            func.set_user_instr_highlight(func.arch, addr, 0)

                    # save this set of breakpoint addresses for next time
                    last_bp_addrs = addrs

                if results[0].registers:
                    # get the current PC from the debugger
                    addr = results[0].registers.values()[0] - slide

                    # find the function where that address is
                    func = view.get_function_at(view.platform, view.get_previous_function_start_before(addr))

                    # update the highlight colour of the previous PC to its saved value
                    func.set_user_instr_highlight(func.arch, last_pc_addr, last_pc_addr_colour)

                    # save the PC and current colour for that instruction
                    last_pc_addr_colour = func.get_instr_highlight(func.arch, addr).color
                    last_pc_addr = addr

                    # update the highlight colour to show the current PC
                    func.set_user_instr_highlight(func.arch, addr, config.pc_colour)

    if not syncing:
        try:
            log_info("Starting synchronisation with Voltron")
            vers = client.perform_request("version")
            client.start(build_requests=build_requests, callback=callback)
            syncing = True
        except:
            log_alert("Couldn't connect to Voltron")
    else:
        log_alert("Already synchronising with Voltron")


def stop(view):
    global syncing, client, slide

    if syncing:
        log_info("Stopping synchronisation with Voltron")

        # clear any colours we've set
        func = view.get_function_at(view.platform, view.get_previous_function_start_before(last_pc_addr))
        func.set_user_instr_highlight(func.arch, last_pc_addr, last_pc_addr_colour)
        for addr in last_bp_addrs:
            func = view.get_function_at(view.platform, view.get_previous_function_start_before(addr))
            func.set_user_instr_highlight(func.arch, addr, 0)

        # stop the voltron client
        client.stop()
        client = Client()

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
        func = view.get_function_at(view.platform, view.get_previous_function_start_before(address))
        if func:
            func.set_user_instr_highlight(func.arch, address, config.bp_colour)
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
        func = view.get_function_at(view.platform, view.get_previous_function_start_before(address))
        if func:
            func.set_user_instr_highlight(func.arch, address, 0)
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


PluginCommand.register("Sync with Voltron", "", sync)
PluginCommand.register("Stop syncing with Voltron", "", stop)
PluginCommand.register_for_address("Set breakpoint", "", set_breakpoint)
PluginCommand.register_for_address("Delete breakpoint", "", delete_breakpoint)
PluginCommand.register_for_address("Set slide from instruction", "", set_slide)
PluginCommand.register("Clear slide", "", clear_slide)
