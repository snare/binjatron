# Binary Ninja plugins

## voltron_breakpoint.py

Installs menu items `Set breakpoint` and `Delete breakpoint` for setting and deleting breakpoints in GDB or LLDB from [Binary Ninja](http://binary.ninja) via the [Voltron](https://github.com/snare/voltron) API.

Right clicking on an instruction in the binary view and selecting `Set breakpoint` will set a new breakpoint in the debugger:

![set_breakpoint](http://i.imgur.com/HzxStvG.png)

The Voltron breakpoints view will update to show the new breakpoint:

![bp_view](http://i.imgur.com/ITHf4zU.png)

And a comment will be added in Binary Ninja to indicate that there is a breakpoint set at this address:

![comment_added](http://i.imgur.com/ASI5gt5.png)

Right clicking on an instruction in the binary view where a breakpoint has been set and selecting `Delete breakpoint` will remove the breakpoint in the debugger:

![delete_breakpoint](http://i.imgur.com/Znqx2Lx.png)

And the comment will be removed:

![comment_removed](http://i.imgur.com/omXqgd9.png)

## voltron_sync.py

Installs menu items `Sync with Voltron` and `Stop syncing with Voltron` for synchronising the currently selected instruction with the instruction pointer in a debugger using [Voltron](https://github.com/snare/voltron).

Right clicking anywhere in the binary view and selecting `Sync with Voltron` will start the Voltron client in a background thread within Binary Ninja to watch Voltron for updates:

![sync](http://i.imgur.com/DjGcgqz.png)

If you set a breakpoint in your inferior (here using the test inferior included with Voltron loaded in both Binary Ninja and LLDB, with a breakpoint set at `main` in LLDB) and run it, when the debugger stops at the breakpoint the address at which the breakpoint is set will be selected in Binary Ninja:

![run](http://i.imgur.com/Bhx4Evx.png)

![main_selected](http://i.imgur.com/JZpUNK6.png)

If you then step the debugger, the next instruction will be selected in Binary Ninja:

![step](http://i.imgur.com/Py1Smmn.png)

![next_selected](http://i.imgur.com/j8kY6i0.png)

Setting a breakpoint using the `voltron_breakpoint.py` plugin included here will also work:

![break_binja](http://i.imgur.com/QDWIzOY.png)

Then when the debugger is issued the `continue` command and stops at the new breakpoint:

![continue](http://i.imgur.com/epX9pxD.png)

The Binary Ninja selection will again be updated:

![continue_binja](http://i.imgur.com/R7jegjW.png)
