"""
voltron_breakpoint.py

A plugin for Binary Ninja to allow setting and deleting of breakpoints in a
debugger via Voltron's API.

Install per instructions here:
https://github.com/Vector35/binaryninja-api/tree/master/python/examples

Once installed, right click on an instruction in the binary view to set a
breakpoint in the debugger. Voltron's breakpoints view will update immediately
to reflect the new breakpoint. A comment is added in Binary Ninja to show that
there is a breakpoint at the selected address.
"""

from binaryninja import *
import voltron
from voltron.core import Client

client = Client()
vers = None


def set_breakpoint(view, address):
    global vers
    if not vers:
        vers = client.perform_request("version")

    # build a breakpoint set command for the debugger
    if 'lldb' in vers.host_version:
        cmd = "breakpoint set -a 0x{:x}".format(address)
    elif 'gdb' in vers.host_version:
        cmd = "break *0x{:x}".format(address)
    else:
        raise Exception("Debugger host version {} not supported".format(vers.host_version))

    # send it
    res = client.perform_request("command", command=cmd, block=False)
    if res.is_error:
        raise Exception("Failed to set breakpoint: {}".format(res))

    # update the voltron views
    res = client.perform_request("command", command="voltron update", block=False)

    # add a comment in binja
    func = view.get_function_at(view.platform, view.get_previous_function_start_before(address))
    if func:
        comment = func.get_comment_at(address)
        func.set_comment(address, comment + " [breakpoint]")


def delete_breakpoint(view, address):
    global vers
    if not vers:
        vers = client.perform_request("version")

    # get a list of breakpoints from the debugger and find the one we're after
    res = client.perform_request("breakpoints")
    bp_id = None
    if res.is_success:
        for bp in res.breakpoints:
            for location in bp['locations']:
                if address == location['address']:
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

    # remove the breakpoint comment in binja
    func = view.get_function_at(view.platform, view.get_previous_function_start_before(address))
    if func:
        comment = func.get_comment_at(address)
        func.set_comment(address, comment.replace(" [breakpoint]", ""))


PluginCommand.register_for_address("Set breakpoint", "", set_breakpoint)
PluginCommand.register_for_address("Delete breakpoint", "", delete_breakpoint)
