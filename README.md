# binjatron

Binary Ninja plugin for [Voltron](https://github.com/snare/voltron) integration.

Features:

- Mark the current instruction pointer in the debugger in Binary Ninja
- Mark breakpoints that are set in the debugger in Binary Ninja
- Set and delete breakpoints in the debugger from Binary Ninja
- Synchronise code updates made in Binary Ninja with the debugger

Support:

- Everything works in LLDB (except writing memory right now)
- Some features may not work properly in GDB
- Some features may work in WinDbg and VDB but haven't been tested at all

## Installation

**Note: snare has been adding features to Voltron to support Binjatron, and sometimes these features have not made a release yet, so please use the latest version of [Voltron](https://github.com/snare/voltron) from GitHub.**

Binjatron requires [Voltron](https://github.com/snare/voltron), which is a framework to talk to various debuggers (GDB, LLDB, WinDbg and VDB) and build common UI views for them. Firstly, Voltron must be installed and working with your debugger of choice. An install script is provided that covers most use cases for GDB/LLDB on macOS and Linux, and [manual installation instructions](https://github.com/snare/voltron/wiki/Installation) are provided for other cases.

Voltron must also be installed into the same Python version that Binary Ninja is using, which will depend on which platform you are on. This may or may not be the same Python version that your debugger is using. On macOS, for example, BN uses the system's default version of Python 2.7, and so does LLDB, so installing using Voltron's `install.sh` is sufficient. There's more information [here](https://github.com/snare/voltron/wiki/Installation) that may be useful in determining into which Python version you should be installing Voltron. 

Windows/WinDbg users will need to follow the [manual install instructions](https://github.com/snare/voltron/wiki/Installation) to install Voltron and get it working with WinDbg. They'll also need to install Voltron into BN's embedded Python installation.

Once Voltron is installed, install the Binjatron plugin per the instructions on the [Binary Ninja API repo](https://github.com/Vector35/binaryninja-api/tree/master/python/examples).

If you're having issues getting it working, please open an [issue on GitHub](https://github.com/snare/binjatron).

## Usage

Binjatron installs menu items `Voltron: Sync` and `Voltron: Stop syncing` for synchronising data from the debugger with Binary Ninja.

Right clicking anywhere in the binary view and selecting `Sync with Voltron` will start the Voltron client in a background thread within Binary Ninja to watch Voltron for updates.

The current instruction pointer in the debugger will be highlighted in BN (in red by default). When the debugger is stepped, or continued and another breakpoint is hit, the highlighted instruction will be updated. Any breakpoints set in the debugger will be highlighted (in blue by default).

![binjatron](http://i.imgur.com/NQuKhfD.png)

When code is patched in Binary Ninja, the new code will be sent to Voltron and written to the same address in the inferior's memory (this only works with GDB as the backend so far):

![pre_edit](http://i.imgur.com/IxGqOa4.png)

![post_edit](http://i.imgur.com/AjLbqQK.png)

This plugin also installs the menu items `Set breakpoint` and `Delete breakpoint` for setting and deleting breakpoints in GDB or LLDB from within BN. Right clicking on an instruction in the binary view and selecting `Set breakpoint` will set a new breakpoint in the debugger, and right-clicking an instruction where a breakpoint has been set and selecting `Delete breakpoint` will delete the breakpoint in the debugger.

### ASLR support

Binjatron works by highlighting instructions in BN at the instruction pointer and breakpoint addresses from the debugger. Generally when you load a binary into a debugger, ASLR will be disabled, which means that the addresses in the debugger will match those that Binary Ninja knows about. If, for some reason, you need ASLR enabled (e.g. the author does a lot of work attached to live macOS kernels with VMware, which have ASLR enabled), this is a problem because the addresses that the debugger knows about are slid by a random value and will not match those in the copy of the kernel loaded in Binary Ninja.

To work around this, Binjatron provides the ability to set a slide value with the `Set slide from instruction` menu item.

To use this feature, load up your binary in both the debugger and BN and start syncing with Voltron. Now identify the instruction at which the instruction pointer in the debugger is pointing. Right click this instruction, and select `Set slide from instruction`. Binjatron will examine the current instruction pointer in the debugger, and the address at which the selected instruction exists, and calculate the ASLR slide.

Here we can tell which instruction it is because we've set a breakpoint in the debugger:

![set_slide](http://i.imgur.com/UPYSD6Y.png)

Now that the slide has been updated, the current instruction pointer is reflected properly in BN:

![with_slide](http://i.imgur.com/kcnBN8i.png)

**Note:** ASLR support probably only works with LLDB as a back end debugger for now. The code should support GDB, but with some caveats (you will have to have at least run the inferior and hit a breakpoint before you can set the slide, and it won't update the display properly until the next time you step because of limitations with GDB's API). This has not been tested and will not be tested until snare gets around to running BN on Linux, as GDB on macOS doesn't seem to support disabling ASLR.

## Caveats

Setting and deleting breakpoints from Binjatron currently only works with GDB and LLDB. I'll add WinDbg support soon.

ASLR support only works with LLDB for now.

Code updating only works in GDB for now.

## Configuration

The only configuration for Binjatron is the colours used to highlight the instruction pointer and breakpoints. These colours can be set by creating a configuration file at `~/.binjatron.conf` containing something like this:

    bp_colour: 1
    pc_colour: 4

The numbers there refer to the indices into the `Highlight instruction` submenu in BN (right click an instruction to see it).