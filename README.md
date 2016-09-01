# Binary Ninja plugins

## voltron_breakpoint.py

Installs menu items `Set breakpoint` and `Delete breakpoint` for setting and deleting breakpoints in [Binary Ninja](http://binary.ninja) via the [Voltron](https://github.com/snare/voltron) API.

Right clicking on an instruction in the binary view and selecting `Set breakpoint` will set a new breakpoint in the debugger, and add a comment in Binary Ninja to indicate that there is a breakpoint set at this address.

Right clicking on an instruction in the binary view where a breakpoint has been set and selecting `Delete breakpoint` will remove the breakpoint in the debugger and clear the comment.

When breakpoints are set or deleted, the Voltron breakpoints view will be updated.