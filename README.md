# binjatron

Binary Ninja plugin for [Voltron](https://github.com/snare/voltron) integration.

Features:

- Synchronise the selected instruction in Binary Ninja with the instruction pointer in the debugger
- Mark breakpoints that are set in the debugger in Binary Ninja
- Set and delete breakpoints in the debugger from Binary Ninja

## Installation

Binjatron requires [Voltron](https://github.com/snare/voltron), which is a framework to talk to various debuggers (GDB, LLDB, WinDbg and VDB) and build common UI views for them. Firstly, Voltron must be installed and working with your debugger of choice. An install script is provided that covers most use cases for GDB/LLDB on macOS and Linux, and [manual installation instructions](https://github.com/snare/voltron/wiki/Installation) are provided for other cases.

Voltron must also be installed into the same Python version that Binary Ninja is using, which will depend on which platform you are on. This may or may not be the same Python version that your debugger is using. On macOS, for example, BN uses the system's default version of Python 2.7, and so does LLDB, so installing using Voltron's `install.sh` is sufficient. There's more information [here](https://github.com/snare/voltron/wiki/Installation) that may be useful in determining into which Python version you should be installing Voltron. 

Windows/WinDbg users will need to follow the [manual install instructions](https://github.com/snare/voltron/wiki/Installation) to install Voltron and get it working with WinDbg. They'll also need to install Voltron into BN's embedded Python installation.

Once Voltron is installed, install the Binjatron plugin per the instructions on the [Binary Ninja API repo](https://github.com/Vector35/binaryninja-api/tree/master/python/examples).

If you're having issues getting it working, please open an [issue on GitHub](https://github.com/snare/binjatron).

## Usage

Binjatron installs menu items `Sync with Voltron` and `Stop syncing with Voltron` for synchronising the currently selected instruction with the instruction pointer in a debugger using [Voltron](https://github.com/snare/voltron). It also synchronises breakpoints, and marks any instructions that have breakpoints set in the debugger by highlighting them.

Right clicking anywhere in the binary view and selecting `Sync with Voltron` will start the Voltron client in a background thread within Binary Ninja to watch Voltron for updates.

If you set a breakpoint in your inferior (here using the test inferior included with Voltron loaded in both Binary Ninja and LLDB, with a breakpoint set at `main` in LLDB) and run it, when the debugger stops at the breakpoint the address at which the breakpoint is set will be selected in Binary Ninja.

The current instruction pointer in the debugger will also be highlighted in BN (in red by default). When the debugger is stepped, or continued and another breakpoint is hit, the instruction at the new instruction pointer will be highlighted.

![binjatron](http://i.imgur.com/NQuKhfD.png)

This plugin also installs the menu items `Set breakpoint` and `Delete breakpoint` for setting and deleting breakpoints in GDB or LLDB from within BN. Right clicking on an instruction in the binary view and selecting `Set breakpoint` will set a new breakpoint in the debugger, and right-clicking an instruction where a breakpoint has been set and selecting `Delete breakpoint` will delete the breakpoint in the debugger.

## Configuration

The only configuration for Binjatron is the colours used to highlight the instruction pointer and breakpoints. These colours can be set by creating a configuration file at `~/.binjatron.conf` containing something like this:

    bp_colour: 1
    pc_colour: 4

The numbers there refer to the indices into the `Highlight instruction` submenu in BN (right click an instruction to see it).