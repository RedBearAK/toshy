# Toshy README

## Make your Linux keyboard act like a 'Tosh!

Toshy is a config file for the `keyszer` Python-based keymapper for Linux, which was forked from `xkeysnail`. The Toshy config is not strictly a fork, but was based in the beginning entirely on the config file for Kinto.sh by Ben Reaves (https://github.com/rbreaves/kinto or https://kinto.sh). Without Kinto, Toshy would not exist.  Using Toshy will feel basically the same as using Kinto, just with some new features and some problems solved.  

The purpose of Toshy is to match, as closely as possible, the behavior of keyboard shortcuts in macOS when working on similar applications in Linux. General system-wide shortcuts such as Cmd+Q/W/A/Z/X/C/V and so on are relatively easy to mimic by just moving the modifier key locations, with `modmaps`. A lot of shortcuts in Linux just use `Ctrl` in the place of where macOS would use `Cmd`. But many other shortcut combos from macOS applications have to be remapped onto entirely different shortcut combos in the Linux equivalent application. This is done using application-specific `keymaps`, that only become active when you are using the specified application or window.  

## Toshifying an Application

If an app that you use frequently in Linux has some shortcut behavior that still doesn't match what you'd expect from the same application (or a similar application) in macOS, after Toshy's general remapping of the modifier keys, you can add a keymap that matches the app's "class" and/or "name/title" window attributes, to make that application behave as expected. By adding it to the default config file, every user will benefit!  

To do this, on X11 you need the tool `xprop` which lets you retrieve the window attributes by clicking on the window with the mouse. Use this command to get only the relevant attributes:  

```sh
xprop WM_CLASS _NET_WM_NAME
```

The mouse cursor will change to a cross shape. Click on the window in question and the attributes will appear in the terminal.  

## Windows Support

Toshy has no Windows version, unlike the Kinto.sh project. I was trying to solve a number of issues and add features to the Linux version of Kinto, so that's all I'm focused on for Toshy. The Windows version of Kinto works great. Go check it out if you need Mac-like keyboard shortcuts on Windows. I also contribute to Kinto on the Windows side.  

## Keyboard Types

Four different keyboard types are supported by Toshy (Windows/PC, Mac/Apple, IBM and Chromebook), just as in Kinto. But Toshy does its best to automatically treat each keyboard device as the correct type in real-time, as you use it, rather than requiring you to change the keyboard type from a menu. This means that you _should_ be able to use an Apple keyboard connected to a PC laptop, or an IBM keyboard connected to a MacBook, and shortcut combos on both the external and internal keyboards should work as expected, with the modifier keys appearing to be in the correct place to "Act like a 'Tosh".  

## Option-key Special Characters

Toshy includes a complete implementation of the macOS Option-key special characters, including all the "dead key" accent keys, from two keyboard layouts. The standard US keyboard layout, and the "ABC Extended" layout (which is still a US keyboard layout otherwise). This adds up to somewhere over 600 special characters being available, between the two layouts. It works just the same way it does on macOS, when you hold the Option or Shift+Option keys. For example, Option+E, then Shift+E, gets you an "E" with Acute accent: É.  

The special characters may not work as expected unless you add a bit of "throttle" delay to the macro output. This is a new `keyszer` API function that inserts timing delays in the output of combos that involve modifier keys. There is a general problem with Linux keymappers using `libinput` in a lot of situations, especially in virtual machines, with the modifier key presses being misinterpreted as occuring at a slightly different time, leading to problems with macro output. A slight delay will usually clear this right up, but a virtual machine environment may need a few dozen milliseconds to achieve macro stability. In fact it's not just macros, but many shortcuts in general may seem very flaky or unusuble in a VM, and this will impact the Option-key special characters, since it uses Unicode macro sequences.  

A dedicated Unicode processing function was added to `keyszer` that made it possible to bring the Option-key special characters to Linux, where previously I could only add it to the Windows version of Kinto using AutoHotkey.  

If you're curious about what characters are available and how to access them, the fully documented lists for each layout are available here:  

https://github.com/RedBearAK/optspecialchars

It's important to understand that your actual keyboard layout will have no effect on the layout used by the Option-key special character scheme. The keymapper generally has no idea what your keyboard layout is, and has a tendency to treat your keyboard as if it is always a US layout. This is a problem that needs a solution. I haven't found even so much as a way to reliably detect the active keyboard layout. So currently Toshy works best with a US layout.  

The other problem is that the Unicode entry shortcut only seems to work if you have `ibus` or `fcitx` (unconfirmed) set up as your input manager. If not, the special characters (or any other Unicode character sequence) will only work correctly in GTK apps, which seem to have the built-in ability to understand the Shift+Ctrl+U shortcut that invokes Unicode character entry.  

There's no simple way around this, since the keymapper is only designed to send key codes from a virtual keyboard. Unlike AutoHotkey in Windows, which can just "send" a character pasted in an AHK script to an application (although there are potential problems with that if the AHK file encoding is wrong). 

## General improvements over Kinto's config

 1. Multi-user support: I believe some changes I've made will facilitate proper multi-user support on the same system. Even in the case of the user invoking a "Switch User" feature in their desktop environment, where the first user's desktop is still running in the background while another user is logged into their own desktop and using the screen (and physical keyboard). This is a very convenient feature even if you aren't actually sharing your computer with another person. There are many reasons why you might want to log into a different user's desktop to test something. Currently this absolutely requires `systemd` and `loginctl`.  

 1. The Option-key special characters, as described above. Two different layouts are available.  

 1. Automatic categorizing of the keyboard type of the current keyboard device. No more switching of keyboard types from the tray icon menu, or re-running the installer, or being asked to press a certain key on the keyboard during install.  

 1. 

## Requirements

- Linux (no Windows support planned, use Kinto for Windows)
- `keyszer` (keymapper for Linux, forked from `xkeysnail`)
- X11 (Wayland support in `keyszer` is possible in the future)
- systemd (but you can just run the config from terminal or shell script)
- dbus-python (for the tray indicator app)

## Installation

This section will be changing.  

Basically, follow the instructions to install `keyszer`.  

https://github.com/joshgoebel/keyszer

Then, put the "toshy" folder in your `~/.config` folder.  

Point `keyszer` at the Toshy config file:  

```sh
keyszer -w -c ~/.config/toshy/toshy_config.py
```

Technically, that's the least that needs to be done to get it working.  
