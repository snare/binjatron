# Binary Ninja plugins

## voltron_breakpoint.py

Installs menu items `Set breakpoint` and `Delete breakpoint` for setting and deleting breakpoints in GDB or LLDB from [Binary Ninja](http://binary.ninja) via the [Voltron](https://github.com/snare/voltron) API.

Right clicking on an instruction in the binary view and selecting `Set breakpoint` will set a new breakpoint in the debugger.

![set_breakpoint](http://i.imgur.com/HzxStvG.png)

The Voltron breakpoints view will update to show the new breakpoint:

![bp_view](http://i.imgur.com/ITHf4zU.png)

And a comment will be added in Binary Ninja to indicate that there is a breakpoint set at this address.

![comment_added](http://i.imgur.com/ASI5gt5.png)

Right clicking on an instruction in the binary view where a breakpoint has been set and selecting `Delete breakpoint` will remove the breakpoint in the debugger.

![delete_breakpoint](http://i.imgur.com/Znqx2Lx.png)

And the comment will be removed.

![comment_removed](http://i.imgur.com/omXqgd9.png)
