# Current status: Stable-ish Beta (Please Read)

WARNING: There is a very annoying "bug" going around where there is a problem with the `xdg-desktop-portal` and `xdg-desktop-portal-gnome` services causing very long delays with launching certain applications (particularly GTK apps like Firefox, but also reportedly Qt apps sometimes) in a Wayland session. Some distros seem to have a fix for this, others have not fixed it yet.  

Symptoms for Toshy are that the systemd services can't start up properly until anywhere from 30 seconds to a minute or more after logging in. They will eventually start, and restarting the services later, after the glitchy desktop portal service times out, works without issue. I've been observing this on KDE in multiple Linux distros. One "fix" is to mask the `xdg-desktop-portal-gnome` service to keep it from clogging things up:  

```
systemctl --user mask xdg-desktop-portal-gnome
```

But you may need to unmask it if you log into a GNOME desktop, in a Wayland session.  

## Main issues you might run into

- KEYBOARD TYPE: The Toshy config file tries to automatically identify the "type" of your keyboard based on some pre-existing lists of keyboard device names, which do not have many entries yet. So your keyboard may be misidentified, leading to modifier keys in the "wrong" place. BE PREPARED to identify the name of your keyboard device (try `toshy-devices` in a terminal) and enter it into the correct list in the config file to fix this problem. There is an editable "custom" list where the entry should be retained even if you reinstall later.  

Go to the FAQ entry for more info:  

[Keyboard Type Not Correct](#my-keyboard-is-not-recognized-as-the-correct-type)  

> Please take the time to FILE AN ISSUE if you encounter this, whether or not you are able to fix it on your own. Include your device name and what type it should be. The goal is to populate the default keyboard name lists so that this becomes a very unusual problem going forward. The bigger goal of Toshy has been to allow a mixed-type environment where you can use any combination of Apple, Windows (PC), IBM or Chromebook keyboards together without thinking about switching types.  

- May have issues installing on distros not on the "tested" list below. Try the `--list-distros` and `--override-distro` options (separately) with the installer, if you think your distro is closely related to one on the list.  

- May seem to run at login, but not do any remapping, needing `toshy-config-verbose-start` in the terminal to troubleshoot. Or, it may just need a restart of the services from the tray icon or with `toshy-services-restart`.  

- May cause the keyboard in some odd circumstances after install/reboot to have no output (default emergency bail out key is F16, which can be changed in the config file before rebooting). If you don't have F16 on your keyboard, you may need to stop and restart the Toshy services from the tray icon menu, or by opening the "Preferences" app from a menu with the mouse.  

- The Wayland+KDE (Plasma) solution is better now. It should be possible to install under some desktop that is not KDE, then log into KDE on the same system and have Toshy working. If you're not having the issue described above.  

- Some distros have no `journal` output for the user services, for unknown reasons. I've seen this on Arcolinux, the RHEL clones.  

- On a dual-init distro like MX Linux, if you install Toshy while using SysVinit it will avoid installing the `systemd` packages and services. If you then switch to `systemd` at the boot screen you'll need to re-run the Toshy installer once under `systemd` to make it work automatically like it does on other distros using `systemd`.  

# Toshy README

• • • • • 
![Toshy app icon inverse grayscale](./assets/toshy_app_icon_rainbow_inverse_grayscale.svg "Toshy app icon inverse grayscale")
• • • • • 
![Toshy app icon inverted](./assets/toshy_app_icon_rainbow_inverse.svg "Toshy app icon inverse")
• • • • • 
![Toshy app icon](./assets/toshy_app_icon_rainbow.svg "Toshy app icon")


## Make your Linux keyboard act like a 'Tosh! <br>(or, What the Heck is This?!?)

Toshy is a config file for the `keyszer` Python-based keymapper for Linux (which was forked from `xkeysnail`). The Toshy config is not strictly a fork of Kinto, but was based in the beginning entirely on the config file for Kinto.sh by Ben Reaves (https://github.com/rbreaves/kinto or https://kinto.sh). Without Kinto, Toshy would not exist.  Using Toshy will feel basically the same as using Kinto, just with some new features and some problems solved.  

The purpose of Toshy is to match, as closely as possible, the behavior of keyboard shortcuts in macOS when working on similar applications in Linux. General system-wide shortcuts such as Cmd+Q/W/A/Z/X/C/V and so on are relatively easy to mimic by just moving the modifier key locations, with `modmaps`. A lot of shortcuts in Linux just use `Ctrl` in the place of where macOS would use `Cmd`. But many other shortcut combos from macOS applications have to be remapped onto entirely different shortcut combos in the Linux equivalent application. This is done using application-specific `keymaps`, that only become active when you are using the specified application or window.  

All of this basic functionality is inherited from Kinto. Toshy just tries to be a bit fancier in implementing it.  

## Toshifying an Application

If an app that you use frequently in Linux has some shortcut behavior that still doesn't match what you'd expect from the same application (or a similar application) in macOS, after Toshy's general remapping of the modifier keys, you can add a keymap that matches the app's "class" and/or "name/title" window attributes, to make that application behave as expected. By adding it to the default config file, every user will benefit!  

To do this, on X11 you need the tool `xprop` which lets you retrieve the window attributes by clicking on the window with the mouse. Use this command to get only the relevant attributes:  

```sh
xprop WM_CLASS _NET_WM_NAME
```

The mouse cursor will change to a cross shape. Click on the window in question and the attributes will appear in the terminal.  

If you're in one of the compatible Wayland environments (GNOME or KDE, so far), you'll have to rely on other tools, or the verbose logging output from `toshy-config-verbose-start`. When a window has the focus and you use a keyboard shortcut that gets remapped by the keymapper config file, you will see additional output in the terminal showing the window's class and name/title. A good shortcut to use for this that usually won't do anything unless the app has a tabbed UI is `Shift+Cmd+Left_Brace` or `Shift+Cmd+Right_Brace` (those are the defined names of the square bracket keys). Utilities like `xprop` will generally have no output in a Wayland session.  

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

## General improvements over Kinto

 1. Moving between different desktop environments and session types (X11/Xorg or Wayland) **_on the same machine_** is MUCH easier, due to the use of an "environment" module that feeds information to the config file about what type of environment it is starting up in. This allows some dynamic remaps specific to each type of Linux desktop environment, and without re-running the installer process (at least that is the goal). It also prompts the keymapper (a special development branch of `keyszer`) to use the correct method to get the window context information for the environment. The keymapper will also prompt the user in verbose logging output if the environment is NOT compatible yet. So if you are like me and enjoy spending time experimenting with different session types and different desktop environments on the same Linux system, Toshy will work much better for that, and will improve over time.  

 1. Multi-user support: I believe some changes I've made will facilitate proper multi-user support on the same system. Even in the case of the user invoking a "Switch User" feature in their desktop environment, where the first user's desktop is still running in the background while another user is logged into their own desktop and using the screen (and physical keyboard). This is a very convenient feature even if you aren't actually sharing your computer with another person. There are many reasons why you might want to log into a different user's desktop to test something. Currently this absolutely requires `systemd` and `loginctl`.  

 1. Certain Linux distros, outside the most popular group of Ubuntus, Arches and Red Hat/Fedora related distros, really did not like the way the Kinto installer messes with the `sudoers` file. The Kinto installer does this to provide the user easier access to certain commands used to control the `xkeysnail` service. Some of these Linux distros would get b0rked quite badly if you ran the Kinto installer on them. A couple I ran into that had this problem were antiX and Gentoo. Strangely, the close relative of antiX, the very popular MX Linux, did not have the same problem with Kinto that antiX had. The Toshy installer does nothing with `sudoers` and uses "user" `systemd` services, or a manual script, and sets up `udev` rules so that the user doesn't need to run anything with `sudo` to make the keymapping work. I've already tested Toshy successfully on antiX. Still looking for a user-friendly Gentoo ISO to use for testing, but I have no reason to believe it won't work just as well, once I figure out the native packages needed.  

 1. A start on Wayland support. Two Wayland+[desktop environment] types are working now: Wayland+GNOME (needs shell extension installed) and Wayland+KDE (Plasma, installs a KWin script that needs to see a window activation event to start functioning). Wayland+sway and Wayland+Hyprland support is theoretically possible. More on that further down.  

 1. The Option-key special characters, as described above. Two different layouts are available. Or it can be completely disabled.  

 1. Automatic categorizing of the keyboard type of the current keyboard device. No more switching of keyboard types from the tray icon menu, or re-running the installer, or being asked to press a certain key on the keyboard during install. Some keyboard devices will need to be added to a Python list in the config to be recognized as the correct type. This will evolve over time from user feedback.  

 1. Changing of some settings on-the-fly, without restarting the keymapper process. The tray icon menu and GUI preferences app will allow quickly enabling or disabling certain features, or changing/disabling the special characters layout. The change takes effect right away. (Adding or changing shortcuts in the config file will still require restarting the keymapper, which I've tried to make as easy as possible.)  

 1. Modmaps with `keyszer` are now concurrent/cascading rather than mutually exclusive. This enables some of the interesting fixes described in the following items.  

 1. Fix for "media" functions on arrow keys. Some laptop keyboards don't have the usual PgUp/PgDn/Home/End navigation functions on the arrow keys, when you hold the `Fn` key. Instead, they have PlayPause/Stop/Back/Forward. A `modmap` in the Toshy config will optionally fix this, making the arrow keys work more like a standard MacBook keyboard. This feature can be enabled from the tray icon or GUI preferences app.  

 1. This one is starting to become less relevant, with most common GTK apps already moving to GTK 4. But apps that use GTK 3 had a really annoying bug where they wouldn't recognize the "navigation" functions on the keypad keys (what the keypad keys do when NumLock is off) if you tried to use them with a modifier key (i.e., as part of a shortcut). Those keys would just get ignored. So if you didn't have the equivalent "real" navigation keys anywhere on your keyboard, there was no way to use shortcuts involving things like PgUp/PgDn/Home/End (on the numeric keypad). A `modmap` in the Toshy config will automatically fix this, if NumLock is off and the "Forced Numpad" feature (below) is disabled.  

 1. "Forced Numpad" feature: On PCs, if the keyboard has a numeric keypad, NumLock is typically off, so the keypad doesn't automatically act as a Numpad, instead providing navigation functions until you turn NumLock on. But if you've used macOS for any length of time, you might have noticed that the numeric keypad is always a numeric keypad, and the "Clear" key sends `Escape` to clear calculator apps. You have to use `Fn+Clear` to disable NumLock and get to the navigation functions. A `modmap` in the Toshy config is enabled by default and makes the numeric keypad always a numeric keypad, and turns the NumLock key into a "Clear" key. This can be disabled in the tray icon menu or GUI preferences app, or temporarily disabled with `Fn+Clear` (on Apple keyboards) or the equivalent of `Option+NumLock` on PC keyboards (usually this is physical `Win+NumLock`).  

 1. Sections of the config file are labeled with ASCII art designed to be readable on a "minimap" or "overview" sidebar view found in many text editors and code editors, to make finding certain parts of the config file a little easier. There's also a "tag" on each section that can be located easily with a `Find` search in any text editor.  

 1. Custom function to make the `Enter` key behave pretty much like it does in the Finder, in most Linux file managers. Mainly what this enables is using the `Enter` key to quickly rename files/folders, while still leaving it usable in text fields like `Find` and the location bar. Not perfect, but works OK in most cases. _[NOTE: If you've never actually used the keyboard to "open" or "run" files/applications from the Finder, you may not realize that the keyboard shortcut for this is just the same keyboard shortcut for opening (or, "drilling down") into folders. It's `Cmd+Down` arrow. The `Enter` key has never "opened" things in the Finder in the history of macOS, as far as I know, unlike the way the `Enter` key has always been used in Windows and Linux file managers.]_  

 1. Evolving fix for the problem of `Cmd+W` unexpectedly failing to close a lot of Linux "child" windows and "dialog" windows (that have no binding to `Ctrl+W` and want either `Escape` or `Alt+F4/Ctrl+Q` to close). This can lead to a bad unconscious habit of hitting `Cmd+W` followed immediately by `Cmd+Q` (which becomes a problem when you're actually using macOS). The list of windows targeted by this pair of keymaps will grow over time, with input from users encountering the issue.  

 1. Fix for shortcut behavior in file save/open dialogs in apps like Firefox, now that WM_NAME (window name/title) is available. This is an addition to the "Finder Mods" that I contributed to Kinto, which are intended to mimic Finder keyboard behavior in most common Linux file manager apps.  

 1. A collection of tab navigation fixes for various apps with a tabbed UI that don't use the mostly standard Ctrl+PgUp/PgDn shortcuts. The goal is to allow `Shift+Cmd+Braces` (the left/right square bracket keys) to perform tab navigation in as many Linux applications (with tabbed UIs) as possible, as it does in most Mac applications with a tabbed UI (Finder, web browsers, and so on). Let me know if you use a Linux app where `Shift+Cmd+Braces` shortcuts are not working for tab navigation while Toshy is enabled. Use `xprop WM_CLASS _NET_WM_NAME` to obtain the window attributes for matching (if you use X11/Xorg).  

 1. Another growing collection of enhancements to various Linux apps to enable shortcuts like `Cmd+comma` (preferences) and `Cmd+I` (get info/properties) to work in more apps.  

 1. A function (`matchProps`) that enables very powerful and complex (or simple) matching on multiple properties at the same time. Application class, window name/title, device name, NumLock and CapsLock LED state can all be combined in any way, and lists can be made of specific combinations of one or more of those properties to match on.  

 1. More that I will add later when I remember...  

## Requirements

- Linux (no Windows support planned, use Kinto for Windows)

    - List of working/tested distros below

- `keyszer` (keymapper for Linux, forked from `xkeysnail`)

    - Automatically installed from custom branch by Toshy installer

- X11/Xorg or Wayland+GNOME or Wayland+KDE (Plasma)

    - Wayland+GNOME requires one of these GNOME Shell extensions‡ (see note):

        - ### Name: 'Xremap' (try this if you have an older GNOME)
        - UUID: `xremap@k0kubun.com`
        - URL: https://extensions.gnome.org/extension/5060/xremap/

        - ### Name: 'Window Calls Extended'
        - UUID: `window-calls-extended@hseliger.eu`
        - URL: https://extensions.gnome.org/extension/4974/window-calls-extended/

        - ### Name: 'Focused Window D-Bus'
        - UUID: `focused-window-dbus@flexagoon.com`
        - URL: https://extensions.gnome.org/extension/5592/focused-window-d-bus/

    - Wayland+KDE has a small glitch where you have to change the focused window once after the KWin script is installed, to get the app-specific remapping to start working. I am trying a solution that uses a pop-up dialog to create a KWin event.

- `systemd` (but you can just manually run the config from terminal, shell script, or tray indicator menu)

- D-Bus, and `dbus-python` (for the tray indicator and GUI app)

‡ Note: It's very easy to search for and install GNOME Shell extensions now, if you install the "Extension Manager" Flatpak application from Flathub. No need to mess around with downloading a zip file from `extensions.gnome.org` and manually installing/enabling in the terminal. Many distros with GNOME need the `AppIndicator and KStatusNotifierItem` extension to make the tray icon appear in the top bar, and if you want to use Wayland you'll need one of the extensions from the list above.  

```sh
flatpak install com.mattjakeman.ExtensionManager
```

... or just:

```sh
flatpak install extensionmanager
```

If it's not found you may need to enable the Flathub repo on your machine. Go to Flathub.org for instructions for your distro.  

When you get it installed, you can just use the "Browse" tab in this application to search for the extensions by name and quickly install them.  

There will be no issue when installing more than one of the compatible extensions. Which might be advisable, to reduce the risk of not having a working extension for a while the next time you upgrade your system in-place and wind up with a newer, temporarily unsupported version of GNOME. I expect at least one of the extensions will always be updated quickly to support the latest GNOME. The branch of `keyszer` installed by Toshy will seamlessly jump to trying the other extensions in case one fails or is disabled/uninstalled for any reason. You just need to have at least one from the list installed and enabled, and when it responds over D-Bus to the query from `keyszer` it will be marked as the "good" one and used from then on, unless it stops responding. Lather, rinse, repeat.  

The `Xremap` GNOME shell extension is the only one that supports older GNOME versions, so it's the only one that will show up when browsing the extensions list from an environment like Zorin OS (GNOME 3.38.x) or the distros based on Red Hat Enterprise Linux (clones like AlmaLinux, Rocky Linux, EuroLinux, etc.) which are still using GNOME 40.x.  

There is a weird bug with searching for the `Xremap` extension on newer versions of GNOME like GNOME 44, where you actually have to use the option "Show Unsupported" from the hamburger menu in order to get it to show up.  

## How to Install

1. Download the latest zip from the big green `Code ˇ` button near the top of the page.  
1. Unzip the archive, and open a terminal in the resulting folder.  
1. Run the `toshy_setup.py` script in the terminal.  

```sh
./toshy_setup.py
```

### Options for installer

The installer has a couple of options available:  

```sh
./toshy_setup.py --show-env
```

This will just show what the installer will see as the environment when you try to install, but won't actually run the full install process.  

```sh
./toshy_setup.py --list-distros
```

This will print out a list of the distros that the Toshy installer theoretically "knows" how to deal with, as far as knowing the correct package manager to use and having a list of package names that would actually work. This can be used with:  

```sh
./toshy_setup.py --override-distro distro_name
```

This option will force the installer to attempt the install for that distro name/type. You can use this if you have a distro that is not on the distro list yet, but you think it is close enough to one of the existing distros in the list that the installer should do the right things. For instance if you have some very Arch-ish or very Debian-ish distro, or something based on Ubuntu (there are many!) that doesn't identify as one of the "known" distros when you use `--show-env` and `--list-distros`, then you can try to make it install using one of the related distro names. This will probably work, if the distro is just a minor variation of its parent distro.  

You don't have to run any of these commands before trying the installer, it will let you know almost immediately if it doesn't know how to install on your distro.  

Other options for the installer:  

```sh
./toshy_setup.py --apply-tweaks
```

Just applies the "desktop tweaks" for the environment, does not do the full install. Might be handy if you have a system with multiple desktop environments.  

```sh
./toshy_setup.py --remove-tweaks
```

Just removes the "desktop tweaks" the installer applied.  

And finally:  

```sh
./toshy_setup.py --fancy-pants
```

This will do the full install, but add various things that I find convenient, fun, or that somehow make the desktop environment behave more like macOS.  

At the moment this installer option will do the following: 

- ALL: Installs "Fantasque Sans Mono noLig" font
    - From a fork with no coding ligatures
    - LargeLineHeight-NoLoopK variant
    - Try it in terminals or code editors
    - May look a bit "heavy" on KDE due to forced "stem darkening" in Qt apps
- GNOME: Makes "Switch applications" the primary task switching style (groups apps like macOS)
- KDE: Installs "Application Switcher" KWin script (groups apps like macOS/GNOME)
- KDE: Disables task switcher option "Show selected window"
- KDE: Sets the task switcher to "Large Icons" (like macOS/GNOME task switcher)
- KDE: Enables task switcher option "Only one window per application" (makes the task switcher dialog show only a single icon for each application, like macOS/GNOME)

## How to Uninstall

This should work now:  

```sh
./toshy_setup.py --uninstall
``` 

Please file an issue if you have some sort of trouble with the uninstall option. If you have a multi-desktop system you may need to run the uninstall procedure while logged into KDE if you ran the installer in KDE, due to the KDE-specific components that get installed for Wayland support.  

## Currently working/tested Linux distros:

This is a list of Linux distributions and desktop variants I've been able to test so far. For those with release versions provided, that is just what I happened to download and test. Older or newer versions of the same distro, within reason, may also work.  

As noted elsewhere in the README, there is no Windows version of Toshy, unlike Kinto.  

### Red Hat and similar distros

- Fedora 36/37/38 (upstream of CentOS Stream and RHEL)

    - Standard GNOME variant tested (Wayland session requires extension)
    - KDE variant tested (X11/Xorg or Wayland+KDE session)

- Ultramarine Linux 38 (Fedora-based)

    - Ultramarine GNOME tested (Wayland session requires extension)

- Nobara 38 (Fedora-based)

    - Tested the usual GNOME desktop variant (X11/Xorg and Wayland)
    - Many Toshy dependencies are pre-installed on Nobara
    - Nobara pre-installs the Extension Manager app. Nice!
    - Enable the AppIndicator extension (pre-installed) for tray icon
    - Install an extension from `Requirements` if using Wayland+GNOME

- [ AlmaLinux / Rocky Linux ] 9.2 (RHEL clones)

    - Tested with "Workstation" installer choice, not "Server with GUI"
    - Default GNOME desktop tested (Wayland session requires extension)
    - KDE Plasma desktop tested (Wayland+KDE supported)
    - Some non-default (but official) repos like CRB will be enabled
    - NB: There is no journal for "user" services, for some reason

- Eurolinux 9.2 (RHEL clone)

    - Tested with "Server with GUI" installer choice
    - Default GNOME desktop tested (Wayland session requires extension)
    - Some non-default (but official) repos like CRB will be enabled
    - NB: There is no journal for "user" services, for some reason

- Other RHEL clones should be supportable

    - Red Hat Enterprise Linux itself? Probably.
    - Try `./toshy_setup.py --override-distro=almalinux` or `=rhel`

- CentOS 7 (RHEL 7 clone) - Partial support:

    - You must first install `python3` to run `toshy_setup.py`
    - systemd "user" services are not supported in CentOS/RHEL 7
    - Auto-start at login with systemd services not available
    - Cmd+Space (Alt+F1) shortcut must be assigned to app launcher menu
    - To manually start Toshy config from tray icon menu:
        - "(Re)Start Toshy Script" option will start Toshy config
        - "Stop Toshy Script" option will stop background Toshy config
    - To manually start Toshy config from terminal:
        - Use `toshy-config-start` or `toshy-config-verbose-start`
        - Use `toshy-config-stop` to stop a background Toshy config

### openSUSE (RPM-based packaging system)

- openSUSE Tumbleweed (rolling release)

    - GNOME desktop works (Wayland session needs extensions, see Requirements)
    - KDE desktop works (X11/Xorg or Wayland)
    - Other desktop choices should work, if session is X11/Xorg

- openSUSE Leap 15.5 (fixed release) **_WORKING!_**

    - GNOME desktop works (Wayland session needs extensions, see Requirements)
    - KDE desktop works (X11/Xorg or Wayland)
    - Other desktop choices should work, if session is X11/Xorg

### Ubuntu variants and Ubuntu-based distros

- Ubuntu official variants tested:

    - Ubuntu 22.04/23.04 (X11/Xorg or Wayland+GNOME, requires extension)
    - Kubuntu 22.04/23.04 (X11/Xorg or Wayland+KDE)
    - Xubuntu 23.04 (X11/Xorg only)
    - Lubuntu 23.04 (X11/Xorg only)
    - Ubuntu Budgie 23.04 (X11/Xorg only)

- Pop!_OS 22.04 LTS (Ubuntu-based)

    - X11/Xorg or Wayland+GNOME (requires extension)

- KDE Neon (based on Ubuntu LTS releases)

    - X11/Xorg or Wayland+KDE session

- Zorin OS 16.2 (Ubuntu-based)

    - X11/Xorg or Wayland+GNOME (requires extension)
    - Wayland+GNOME requires Xremap extension
    - GNOME Shell is still 3.38.x, Xremap extension is the only compatible extension available for pre-GNOME 40.x

- elementary OS 7.0 (Ubuntu-based)

- Linux Mint 21.1/21.2 (Ubuntu-based)

    - Cinnamon desktop
    - Xfce desktop
    - MATE desktop
    - All desktops can be installed on the same Mint system:
    - `sudo apt install mint-meta-mate mint-meta-xfce mint-meta-cinnamon`

- Tuxedo OS 1 (Ubuntu 22.04 LTS variant)

    - X11/Xorg
    - KDE Plasma desktop

### Debian and Debian-based distros

- LMDE 5 (Linux Mint Debian Edition)

- PeppermintOS (Debian-based)

    - New release based on Debian 12 tested
    - Desktop is Xfce4 v4.18

- antiX 22.x (Debian-based, related to MX Linux)

    - Preliminary support, no SysVinit services yet, so no auto-start.
    - Starting only the "config script" from the tray icon menu should work now.
    - Use `toshy-config-start` or `toshy-config-verbose-start` for manual start.
    - Only "rox-icewm" desktop verified/tested.

- MX Linux 21.x (Debian-based, related to antiX)

    - Preliminary support, no SysVinit services yet, so no auto-start.
    - Starting only the "config script" from the tray icon menu should work now.
    - Use `toshy-config-start` or `toshy-config-verbose-start` for manual start.
    - Choosing advanced options and booting with `systemd` will work fine.

- Debian 12 tested and can be made to work:

    - If you gave a root password, your user will NOT be in the `sudo` group!
    - If necessary, add your user to `sudo` group (and reboot!)
        - `su -`
        - `usermod -aG sudo yourusername`
        - Seriously, reboot now!
    - Then, for Wayland+GNOME:
        - Install `flatpak` and the Flathub repo. Instructions here:
            - https://flatpak.org/setup/Debian
        - Do `flatpak install com.mattjakeman.ExtensionManager`
        - Reboot again! So that Flatpak folders are added to path.
        - Install any compatible shell extension with Extension Manager:
            - Xremap
            - Window Calls Extended
            - Focused Window D-Bus
        - Recommended additional extensions:
            - AppIndicator and KStatusNotifier (for tray icon)
            - Logo Menu (enable power options in settings)

### Arch, Arch-based and related distros

- ArcoLinux (Arch-based)

    - ArcoLinuxL ISO (full installer) tested
    - Multiple desktops tested (GNOME, KDE, others)
    - X11/Xorg and Wayland+KDE, Wayland+GNOME
    - `plasma-wayland-session` can be installed
    - See FAQ Re: Application Menu shortcut fix
    - NB: No journal for "user" systemd services, for some reason

- EndeavourOS (Arch-based)

    - Most desktops should work in X11/Xorg
    - GNOME desktop should work in X11/Xorg and Wayland (requires extension)
    - KDE (Plasma) desktop should work in X11/Xorg and Wayland
    - `plasma-wayland-session` can be installed

- Manjaro (Arch-based)

    - GNOME desktop variant tested
    - Xfce desktop variant tested
    - KDE Plasma desktop variant tested
    - `plasma-wayland-session` can be installed
    - See FAQ Re: Application Menu shortcut fix

- Arch in general? (maybe, needs more testing)

    - Installer will try to work on any distro that identifies as `Arch`

## Currently working desktop environments / window managers

- X11/Xorg (all desktop environments)
- Wayland+GNOME (needs shell extension)
- Wayland+KDE (change window focus once to make it work)

If you are in an X11/Xorg login session, the desktop environment or window manager doesn't really matter. The keymapper gets the window class/name/title information directly from the X server with `Xlib`.  

On the other hand, if you are in a Wayland session, it is only possible to obtain the per-application or per-window information (for specific shortcut keymaps) by using solutions that are custom to a limited set of desktop environments (or window managers).  

For Wayland+GNOME this requires at least one of the known compatible GNOME Shell extensions to be installed. See above in "Requirements".  

At some point it should be possible to have Wayland+KDE_Plasma working (UPDATE: Wayland+KDE is pretty much working), and possibly Wayland+sway and Wayland+hyprland. The methods to do this already exist in the `xremap` keymapper, but that project is written in Rust and `keyszer` is written in Python.  

There are specific remaps or overrides of default remaps for several common desktop environments (or distros which have shortcut peculiarities in their default desktop setups). They become active if the desktop environment is detected correctly by the `env.py` module used by the config file, or the information about the desktop can be placed in some `OVERRIDE` variables in the config file.  

## Usage

Toshy does its best to set itself up automatically on any Linux system that uses `systemd` and that is a "known" Linux distro type that the installer knows how to deal with (i.e., has a list of the correct packages to install, and knows how to use the package manager). Generally this means distros that use `apt`, `dnf` or `pacman` so far (and `zypper` from openSUSE now).  

If the install was successful, there should be a number of different terminal commands available to check the status of the Toshy `systemd` user services (the services are not system-wide, in an attempt to support multi-user setups and be ready to support Wayland more easily) and stop/start/restart the services.  

Toshy actually consists of two separate `systemd` services meant to work together, with one monitoring the other, so the shell commands are meant to make working with the paired services much easier.  

(There is now a third service, but it is only active in a Wayland+KDE environment.)  

The commands are copied into `~/.local/bin`, and you will be prompted to add that location to your shell's `PATH` if it is not present. Depends on the distro whether that location is already set up as part of the path or not.  

```
toshy-services-log      (shows journalctl output for Toshy services)
toshy-services-status   (shows the current state of Toshy services)
toshy-services-start
toshy-services-stop
toshy-services-restart
```

To disable/enable the Toshy services (to prevent or restore autostart at login), use the commands below. It should still be possible to start/restart the services with the commands above if they are disabled. Using the "enable" command in turn will not automatically start the services immediately if they are not running (but the services will then autostart at the next login). If the services are enabled they can be stopped at any time with the command above, but the enabled services will start automatically at the next login.  

```
toshy-services-disable  (services can still be started/stopped manually)
toshy-services-enable   (does not auto-start the service until next login)
```

If you'd like to completely uninstall or re-install the Toshy services, use the commands below. These are the same commands used by the Toshy installer to set up the services.  

```
toshy-systemd-remove    (stops and removes the systemd service units)
toshy-systemd-setup     (installs and starts the systemd service units)
```

The following commands are also available, and meant to allow manually running just the Toshy config file, without any reliance on `systemd`. These will automatically stop the `systemd` services so there is no conflict, for instance if you need to run the `verbose` version of the command to debug a shortcut that is not working as expected, or find out how you broke the config file.  

Restarting the Toshy services, either with one of the above commands or from the GUI preferences app or tray icon menu, will stop any manual config process and return to running the Toshy config as a `systemd` service. All the commands are designed to work together as conveniently as possible.  

```
toshy-config-restart
toshy-config-start
toshy-config-start-verbose  (show debugging output in the terminal)
toshy-config-verbose-start  (alias of 'toshy-config-start-verbose')
toshy-config-stop
```

And a command that will show what Toshy sees as the environment when you launch the config. This may be helpful when troubleshooting or making reports:  

```
toshy-env
```

For changing the function keys mode of a keyboard device that uses the `hid_apple` device driver/kernel module, use this command:  

```
toshy-fnmode                    (interactive prompts mode)
toshy-fnmode --help             (show usage/options)
toshy-fnmode --info             (show current status of fnmode)
toshy-fnmode [--option] [mode]  (change fnmode non-interactively)
```

To activate the Toshy Python virtual environment for doing things like running `keyszer` directly, it is necessary to run this command:  

```
source toshy-venv
```

There are also some desktop apps that will be found in most Linux app launchers (like "Albert" or "Ulauncher") or application menus in Linux desktop environments:  

- Toshy Preferences
- Toshy Tray Icon

You may find them under a "Utilities" folder in some application menus (such as the IceWM menu). Or possibly under "Accessories" (LXDE menu).  

Both of these apps will show the current status of the `systemd` services, and allow the immediate changing of the exposed optional features, as well as stopping or restarting the Toshy services. The tray icon menu also allows opening the Preferences app, and opening the `~/.config/toshy` folder if you need to edit the config file.  

If the desktop apps aren't working for some reason, it may be useful to try to launch them from a terminal and see if they have any error output:  

```
toshy-gui
toshy-tray
```

## FAQ (Frequently Asked Questions)

This section will list some common questions, issues and fixes/tweaks that may be necessary for different distros, desktops or devices (and are not yet handled by the Toshy installer or config file). 

### How do I know Toshy is working correctly? (or, It sort of works but sort of doesn't, what's going on?)

There are two levels to what the Toshy config does (just like Kinto, from which the base config file was taken). Level one is the shifting of some of the modifier keys. In most cases, even on an unsupported Wayland environment, the shifting of the modifier keys will work and some basic "global" shortcuts like cut/copy/paste (X/C/V) will appear to work, and you'll be able to open new tabs and close them in a browser with the expected `Cmd` key shortcuts. This can create a false impression that the whole thing is "working" when it actually isn't.  

The second level of remapping is the application group/class-specific modmaps and keymaps (such as "in terminals"), and then the true app-specific keymaps for individual applications (such as "in Firefox"). These will either be working or not working.  

One of the best simple tests, if you have Firefox installed, is if using the `Cmd+comma` shortcut (which opens preferences in many macOS applications) opens a new tab in Firefox, then rapidly types the string "about:preferences", and opens the Firefox preferences. If this works, or even if it just gets through typing the "about:preferences" in the address bar, it's a clear indication that the app-specific keymaps are working. Because this is only supposed to happen when a Firefox web browser window class is detected.  

> NB: If you wind up with a string like `about;preferences` (note the semicolon instead of colon) and it does a google search each time instead of opening the Firefox preferences, you're having a problem with modifier timing in the output of macros from the keymapper. You'll need to look for the FAQ entry on changing the delays in the `throttle_delays` API in the beginning of the config file, and set longer delays to make that go away. Wayland environments and virtual machines will generally require longer delays to avoid this issue.  

If you think app-specific remaps are working in general, but for some reason they aren't working in a specific app, the app's "class" may be different than expected by the config file. Try to identify it, and let us know what the "class" and "name" attributes are.  

UPDATE: There are now a couple of "diagnostic" functions in the config file that should reveal the window attributes (and the keyboard device name) more easily in both X11/Xorg and Wayland environments, when you use one of these shortcuts:  

Safe to do in any application window:  

```
Shift+Opt+Cmd+I,I (double-tap the "I" key while holding the mods)
```

This should display a pop-up dialog box with the application class, window name/title, and the name of the keyboard device.  

ONLY DO THE SHORTCUT BELOW IN A TEXT AREA OR TEXT EDITOR APPLICATION:  

```
Shift+Opt+Cmd+T,T (double-tap the "T" key while holding the mods)
```

This shortcut will initiate a "macro" that will type out the same kind of information found in the pop-up dialog option, but also does a quick Unicode character test that should come out looking like this, on a single line:  

```
Unicode and Shift Test: 🌹—€—‡—ÿ—‡ 12345 !@#$% |\ !!!!!!
```

Here's an example of the whole macro that will be typed out:  

```
Appl. Class: 'Code'
Wind. Title: '● README.md - toshy (Workspace) - Visual Studio Code'
Kbd. Device: 'AT Translated Set 2 keyboard'
Next test should come out on ONE LINE!
Unicode and Shift Test: 🌹—€—‡—ÿ—‡ 12345 !@#$% |\ !!!!!!
```

Previous advice below the line still works too:  

* * *

In X11/Xorg environments, run this in a terminal, then click with the "cross" mouse cursor on the window you're trying to identify:  

```sh
xprop WM_CLASS _NET_WM_NAME
```

In a Wayland environment where you know the app-specific remapping is otherwise working (Wayland+GNOME with extensions or Wayland+KDE is all that works right now), run the Toshy manual config start "verbose" command and then use a shortcut that will be remapped (like `Shift+Cmd+Left_Brace`), while the keyboard focus is on the window that is not being recognized:  

```sh
toshy-config-verbose-start
```

You should see some kind of output like this, which will display the class and name according to the Wayland window context provider, and which keymap has been triggered:  

```sh
(DD) WM_CLASS: 'Xfce4-terminal' | WM_NAME: 'Terminal - testuser@mx: ~'
(DD) DEVICE: 'AT Translated Set 2 keyboard' | CAPS_LOCK: 'False' | NUM_LOCK: 'False'
(DD) ACTIVE KEYMAPS:
     'User hardware keys', 'Wordwise - not vscode', 'GenTerms overrides: Xfce4',
     'General Terminals', 'GenGUI overrides: not Chromebook', 'GenGUI overrides:
      … Xfce4', 'General GUI'
(DD) COMBO: RCtrl-MINUS => Ctrl-MINUS in KMAP: 'General Terminals'
```

In this example the Xfce4-terminal application is being correctly recognized as a terminal (`in KMAP: 'General Terminals'`), and the equivalent of `Cmd+Minus` is remapped onto `Ctrl+Minus`.  

If this terminal was not being recognized as a terminal, it would probably show `in KMAP: 'General GUI'` instead.  

To get back to using the background Toshy services if you've run any of the "manual" commands, just use the `(Re)Start Toshy Services` option from the Toshy tray icon menu, or in the Toshy Preferences GUI app, or just run this command in the terminal to restart the `systemd` services:  

```sh
toshy-services-restart
```

### Repeating Keys

If you have an issue with keys that seem to continue repeating for too long after you release the key, the issue is probably that your keyboard repeat rate is set too high. This can cause repeating keystrokes to "buffer" somehow and lead to deleting way too many characters or similar issues. Slowing down the repeat rate should keep this from happening. How you do this kind of depends on the distro and desktop environment.  

Some DEs have a nice control panel interface for setting the repeat rate, in a way that will work with both X11/Xorg and Wayland. Many how-tos online mention using `xset`, but I believe this only works in X11/Xorg environments. On my Fedora system, the `kbdrate` command seems to work, even in Wayland. If you're using GNOME, there is a control panel for this at `Universal Access > Typing` that will let you disable repeating keys or set the repeat rate (and delay).  

A good repeat rate that should keep the input system from overwhelming the keymapper with repeating keystrokes is around 10 to 20 characters per second (cps).  

### What happened to my customizations of the config?!

#### UPDATE: This shouldn't be a problem in the future

Through extraordinary effort, some updates have been merged that try very hard to retain customizations you may have made to the Toshy config file, and preferences that have been saved to an `sqlite3` database file in your config folder. If you installed Toshy before today (June 5th, 2023), you will need to do one more reinstall from a freshly downloaded zip or clone of the repo. After that reinstall, your config file will contain the markers necessary for the Toshy installer to grab any changes you've made within those special marked sections of the file, and merge them into any new version of the config file as it continues to evolve. **_This will probably not always work over time, depending on what you did, and what changes need to be made to the default config file._** If it doesn't work, you'll just have to merge your customizations the old way, by hand. Hopefully that won't happen often. The same full backups of the entire config folder will happen, just like before. I'll leave the rest of this FAQ entry here for a while. It still has relevant info about the backups.  

If you edit outside the "slice marks" that enable the merging process to work, your changes would still be overwritten every time you run the installer. If you think the config file needs a new location for an editable section, submit an issue about it.  

Right now, the sections marked for attempted retention through upgrades/reinstalls are:  

- API function settings for the keymapper (`keyszer`).  
- Environment overrides (custom distro name, session type, etc.)  
- Keyboard type override (**_submit an issue if you have this problem!_**)  
- "User Apps" area, intended as a good place for things like laptop hardware/function keys remaps, or apps that haven't been added to the default config file yet.  

**_Original, now slightly obsolete text of this FAQ entry below:_**  

* * *  

**Short version**: Don't worry, it's in a backup folder, and you can easily merge your changes back into the new config.  

**Long version**: Because the config file is continually evolving, and the config file itself is really a "program" written in Python that is literally executed as Python code by the keymapper (`keyszer`) at runtime, it's a bit difficult to retain the changes you've made and be sure that the new version of the config file will load without some sort of error.  

So the best solution I've come up with so far is to have the installer make a backup of your whole `~/.config/toshy` folder to a timestamped folder in `~/.config/toshy_config_backups`.  

> PLEASE NOTE: If you run the Toshy installer multiple times you may find that the most recent dated "backup" is just a backup of a fresh Toshy config folder, as it will make a new backup whenever a `toshy` folder is found in `~/.config`. In this case, the folder with your custom changes may be in an older backup folder.  

The backup folders are typically less than 1 MB in size, as the Python virtual environment folder inside (~50 MB in size) is not copied. So they should never take up too much space even if you run the installer multiple times on the same system.  

Using some software like Visual Studio Code, it is possible to compare the old and new config files in a "diff" sort of view and quickly see the differences. This can make it very easy to merge your custom changes back into the new config file with a few clicks. Then all you need to do is save the new config and restart the Toshy services or config script.  

If you keep your modifications within the `keyszer` API functions at the very beginning of the config file, and the "User Apps" marked section around the middle of the config file, it should be pretty easy to merge your customizations back whenever you update Toshy or install on a new machine. The "User Apps" section is designed to be a good place in the config to put some customizations like making the brightness and volume keys on a laptop function row work correctly for your specific machine.  

I will be trying to work on doing a more automatic copying/merging of existing user settings into a new config file.  

There is an `include()` function in `keyszer` that theoretically allows separate files to be part of the config, but due to the dynamic nature of the config file, and how it gets loaded by the keymapper, I had a lot of issues trying to use that method to solve this problem.  

### My keyboard is not recognized as the correct type

> **_NOTE! If you have this problem, please submit an issue report about it, so the device name can be added to the default Toshy config!_**  

#### UPDATE: There is now a way to override the keyboard type

Use the verbose manual config command below, and look for lines with `KB_TYPE:` to see your keyboard device name, as seen by the keymapper and the function that tries to identify the keyboard type. You can also find it in the list output from the terminal command `toshy-devices`.  

You can then take the device name and add it to this Python dictionary between special markers in the config file that will ensure the change will get retained when re-installing or upgrading Toshy:  

```py
keyboards_UserCustom_dct = {
    # Add your keyboard device here if its type is misidentified by isKBtype() function
    # Valid types to map device to: Apple, Windows, IBM, Chromebook
    # Example:
    'My Keyboard Device Name': 'Apple',
}
```

This will force the keyboard to be treated as the 'type' you put after the colon.  

> **_NOTE! If you have this problem, please submit an issue report about it, so the device name can be added to the default Toshy config!_**  

**_Original content of this FAQ is below:_** 

* * *  

If you run the verbose output script you'll be able to see the device name that `keyszer` is seeing when you use your keyboard. Run this in a terminal, and then use a remapped shortcut like `Shift+Cmd+Left_Brace` or `Shift+Cmd+Right_Brace` (the square bracket keys). Or just `Cmd+Tab` away from the terminal and back.  

```sh
toshy-config-verbose-start
```

Using the device name, you can look for the correct keyboard Python "list" in the config file and add the device name to the list. The list names are:   

```py
keyboards_IBM
keyboards_Chromebook
keyboards_Windows
keyboards_Apple
```

Add your device name as an item in the relevant list, and restart Toshy. The keyboard device should now be treated as the correct type, with the modifiers in the right places.  

> **_NOTE! If you have this problem, please submit an issue report about it, so the device name can be added to the default Toshy config!_**  

### My keyboard is a switchable Windows/Mac "universal" model

I'm going to recommend that such keyboards be placed in the "Windows" mode. Most such keyboards won't be automatically identified as an "Apple" keyboard by Toshy (mostly because the device name won't contain "Apple") so things will probably work best if you just leave it in "Windows" mode and let Toshy deal with remapping the modifiers.  

If that doesn't work out well, you'll need to add it to the custom dictionary described in the FAQ entry above to force the device to be identified as an "Apple" keyboard type, and try to use it in the Mac-compatibility mode.  

### CLI/Shell commands missing/unavailable

If you don't have `~/.local/bin` in your shell path, or you answered `n` when prompted during install to add it to the path, you will have to add it to the path yourself, or re-run the installer. Alternately, if you're trying to see the commands immediately after running the installer, you may need to run one of the following commands:  

```sh
hash -r
```

or...

```sh
source ~/.bashrc
```

or...

```sh
. ~/.bashrc
```

(The dot at the beginning is the equivalent of `source`.)  

Which RC file you need to `source` depends on your shell.  

In the case that the path was already added to the RC file, another way of getting a new environment where you can see the `toshy-*` commands is to just close your terminal window (or tab) and open a new one.  

### Touchpads/Trackpads and `keyszer` Suspend Timer

The `keyszer` (fork of `xkeysnail`) keymapper is pretty good, but there is an issue with [modifier key] + [tap or click] when using a touchpad versus a mouse. The keymapper uses a technique that "suspends" modifier key presses briefly (default is 1 second) to try and keep certain applications from seeing those modifier presses and performing some unwanted action. Notable apps that have issues with doing the wrong thing just from seeing a modifier key press are Visual Studio Code (and it's more Open Source variants VSCodium and Code - OSS) and the Firefox web browser. They will frequently focus or open items on the menu bar then they see the `Option/Alt` key in any way.  

The suspend timer scheme works well for mouse usage, letting you do things like `Alt+click`, `Ctrl+click/Cmd+click` and `Shift+click`, but with a touchpad, you may need to reduce the one-second timer to zero or 0.1 seconds in order for those operations to work as you would expect. Look for this near the top of the `toshy_config.py` file:  

```py
timeouts(
    multipurpose    = 1,        # default: 1 sec
    suspend         = 1,        # default: 1 sec, try 0.1 sec for touchpads
)
```

If you do need to disable or reduce the suspend timer because of the touchpad issue, it will become more important to implement the fixes below for VSCode and Firefox, to keep them from focusing the menu bar every time you hit `Option/Alt`.  

### VSCode(s) and Firefox menu stealing focus when hitting `Option/Alt`

For Firefox, the fix is relatively simple: Get to the advanced config settings by entering `about:config` into the URL/address bar. Accept the warning, and search for:  

```ini
ui.key.menuAccessKeyFocuses
```

Double-click the item to change it from "true" to "false", and the `Option/Alt` key will stop focusing the menu bar.  

For VSCode/VSCodium/Code-OSS, use `Cmd+Shift+P` to open the command palette, enter `open user settings json` to open the settings JSON file where you need to place these lines:  

```json
    "window.titleBarStyle": "custom",
    "window.enableMenuBarMnemonics": false,
    "window.customMenuBarAltFocus": false,
```

If there is nothing else in your user settings JSON file, it would need to have enclosing curly braces, like this:  

```json
{
    "window.titleBarStyle": "custom",
    "window.enableMenuBarMnemonics": false,
    "window.customMenuBarAltFocus": false
}
```

And the last line in every section of a JSON formatted file can't have a comma at the end, or there will be an error.  

You may be prompted to restart the app after saving this particular set of lines, and it will change how the VSCode window looks, with a combined menu/titlebar. The `Option/Alt` key will no longer focus the menu bar.  

### Option-key Special Character Entry (or Macros) Acting Weird

Sometimes, especially in virtual machines (but also on some bare metal installs) there is a problem in Linux with the "timing" of modifier key presses, leading to failures of some shortcut combos.  

The Option-key special characters in particular rely on a shortcut combo (`Shift+Ctrl+U`), and if that doesn't work the special character can't be created. And the mimicry of the highlighting of "dead keys" characters will probably also fail, since it does stuff like `Shift+Left`.  

This will also usually affect "macros" where you attempt to get the keymapper to type out multiple characters or strings or perform multiple shortcut combos when you use a shortcut. They may fail somewhere in the middle, or a shifted character will come out as a non-shifted character.  

A solution (well, a "mitigation") for this has been implemented in `keyszer`, and the API function is already in the Toshy config file. Injecting a short delay before and after the "normal" key press (to make sure that the modifier press and release are seen as happening with the correct timing) will usually solve the issue.  

Look for this code early in the Toshy config file:  

```py
throttle_delays(
    key_pre_delay_ms  = 0, # default: 0 ms, range: 0-150 ms, suggested: 1-50 ms
    key_post_delay_ms = 0, # default: 0 ms, range: 0-150 ms, suggested: 1-100 ms
)
```

For a bare metal install, a few milliseconds is usually sufficient to make infrequent glitches go away. Sometimes even as little as 1 ms, but often 2-4 ms for both delays is a good value to start with. For operating inside a virtual machine it may be necessary to use higher values like 50 ms (pre) and 70 ms (post) to get completely reliable behavior. With the right value the reliablity can be so close to 100% that it becomes impractical to find the failure in testing.  

Update for Wayland+GNOME:  

> I've decided to have values of 10/15 in the config by default, since even on bare metal installs there are often strange problems if there isn't a small delay. This is especially true on Wayland+GNOME, where the keymapper must rely on talking to a GNOME Shell extension to get the window info. I don't think this is quite as fast as using `Xlib` in X11/Xorg sessions, so many shortcuts are quite flaky without a bit of throttle delay.  

NB: A lengthy delay will of course cause macros to come out quite a bit more slowly as the delay gets longer. So really long macros will be potentially impractical inside a virtual machine, for instance. This is why the values are clamped to a maximum of 150 ms each. The keyboard will be unresponsive while a long macro is coming out. Currently there is no way to interrupt the macro in progress. Not a big deal when the delay is 1 ms per character, but a problem if the total delay between characters is 150 ms or more.  

### Macros Acting Weird/Failing/Unreliable

See above for the fix using `throttle_delays()`.  

### KDE Plasma and the Option-Key Special Characters

KDE Plasma desktops don't generally use `ibus` (like GNOME desktops usually do by default), or `fcitx` as an input manager. So you may find that the Option-key special character Unicode shortcut of `Shift+Ctrl+U` will not do anything, and the Unicode address of the special character will appear on screen instead of the desired character. This is unfortunately apparently not a shortcut that is built into the Linux kernel input system in general.  

The fix for this, if you want to use those characters in KDE apps, is to install `ibus` and use `im-chooser` to choose `ibus` as the input manager. You may also be able to use `fcitx` as I have seen some references to it supporting the `Shift+Ctrl+U` shortcut, but I haven't tested it.  

Otherwise, without a compatible input manager that responds to the `Shift+Ctrl+U` shortcut to enable Unicode character entry, the special characters will only work correctly in GTK-based applications, which seem to have the `ibus` response to that shortcut built into the GTK framework.  

### Sublime Text 3 and Option-Key Special Characters

For some reason, even when I am in GNOME, the Unicode character entry shortcut of `Shift+Ctrl+U` does not work in Sublime Text 3, so none of the Option-key special characters will work in that app. No idea why. Someone said that they couldn't replicate the problem in a build of Sublime Text 4, and that's all I know about it. No known workaround. (Other than moving to ST4.)  

### International/Non-US keyboard layouts

As of right now the keymapper has a key definition file (a mapping of key symbols to key codes) that is only designed for standard US/English keyboard layouts/languages. And, the keymapper has no knowledge of the current keyboard layout/language, which is remarkably difficult to obtain even on X11/Xorg, and Wayland is worse. Due to these limitations there will be shortcut combos that will act like you are using a US QWERTY keyboard layout, even though you are using, for instance, French AZERTY or something else. If you attempt to use `Cmd+A` on such a layout, the result will be `Cmd+Q` as the keymapper still thinks the `A` key is a `Q`. So instead of "Select All" you'd perform "Close Window".  

There is a solution to this, which is to find and modify the `key.py` file in the `keyszer` package folder (which in the case of Toshy will now be somewhere in `~/.config/toshy/.venv/`). But that would need to be done for every possible keyboard layout that is different from a US QWERTY layout.  

Some international users choose to use a US layout simply because it is a bit easier to use for coding, so they will not run into this problem.  

I'm still looking for a more general/flexible solution to this issue.  

Also, closely related, the Option-key special character schemes that have been implemented are based only on two US keyboard layouts in macOS, the standard US layout and the "ABC Extended" layout (which is still a US layout, but with enhancements to the available special characters and diacritic "dead keys"). So the special character arrangement will have differences from what an international user of macOS might be used to. This, also, is not going to be a simple problem to solve completely.  

### Meta vs Super vs Win(dows) vs Command/Cmd keys

These are all different names for the same key code. The Linux kernal appears to primarily refer to the key as `Meta`, while some Linux desktops (notably GNOME) like to refer to the same key as the `Super` key. Meanwhile, it is the same key as the `Windows` key on PC keyboards (which may have an image of "Tux" the Linux penguin on custom Linux keyboards/laptops). And, to top everything off, the Apple keyboard `Command` key uses the same key code.  

So, as far as the keymapper is concerned, using any of "Win", "Super", "Meta", or "Cmd" in the config file will result in the same key code. I will typically try to refer to it as "Meta" to match the Linux kernel documentation, but it depends on the circumstances. When referring to how it is used in GNOME I'll say "Super", for instance.  

### Xubuntu and the Meta/Super/Win/Cmd key

Xubuntu (using Xfce desktop environment) appears to run a background app at startup called `xcape` that binds the `Super/Meta/Win/Cmd` key (all different names for the same key) to activate the Whisker Menu by itself. To deactivate this, open the "Session and Startup" control panel app, go to the "Application Autostart" tab, and uncheck the "Bind Super Key" item. That will stop the `xcape` command from running at startup. Until you log out or restart, there will still be the background `xcape` process binding the key, but that can be stopped with:  

```sh
killall xcape
```

### Lubuntu Application Menu and Meta/Super/Win/Cmd key

In Lubuntu, right-click on the hummingbird(?) menu icon on the toolbar at the bottom of the screen, and select `Configure "Application Menu"` to change the keybinding from `Super_L` (left Meta key) to `Alt+F1`. If Toshy is enabled, using either the physical equivalent of `Cmd+Space` or `Option+F1` should work. if Toshy is disabled, just use the physical `Alt+F1` keys. NB: The shortcut apparently needs to be set very quickly after clicking the button to change the shortcut. If it doesn't work the first time, just try again, until it says `Alt+F1`.  

### Linux Mint Application Menu (Cinnamon/Xfce/MATE) and the Meta/Super/Win/Cmd key

On Linux Mint (Cinnamon and MATE variants) they use a custom menu widget/applet that is set up to activate with the Meta/Super/Win/Cmd key. The shortcut for this is not exposed in the usual keyboard shortcuts control panels. Right-click on the menu applet icon and go to "Configure" or "Preferences" (make sure you're not opening the preferences for the entire panel, just the menu applet).  

You will see a couple of things that vaguely look like buttons. You can click on the first one and set the shortcut to something like `Ctrl+Esc`. Click on the other button and hit `Backspace` and it will show "unassigned". This will disable the activation of the menu with the Meta/Super/Win/Cmd key.  

Alternately, instead of disabling the secondary shortcut, you could set the secondary shortcut to `Alt+Space` (use the keys corresponding to the physical position of `Option+Space` on an Apple keyboard if Toshy is enabled), but you will have to track down the same shortcut in the regular keyboard shortcuts control panel (something like "Window menu"?) and disable it. If you do this, it will be possible to open the application menu with the same physical keys whether Toshy is enabled or disabled.  

You may need to temporarily DISABLE Toshy (from the tray icon menu, or the GUI preferences app) if it is active, in order to successfully set the main shortcut to `Ctrl+Esc`. Then re-enable Toshy. Or, press the equivalent on your keyboard of `Cmd+Space` when setting the shortcut, and what should appear as the new shortcut is `Ctrl+Esc`.  

If Cinnamon is detected by the Toshy config, `Cmd+Space` will already be getting remapped onto `Ctrl+Esc`, so you should now be able to open the application menu with `Cmd+Space`, if you assigned the suggested shortcut to it.  

In MATE, the remap is set to `Alt+Space`, which is a shortcut that doesn't seem to intefere with any existing shortcut. To set this as the shortcut for the menu applet in MATE, Toshy must be disabled while setting the shortcut, then re-enabled afterward.  

In the Xfce variant of Mint, they use the Whisker Menu applet, and the shortcut (Super_L) is exposed in **_Keyboard >> Application Shortcuts_**. The Toshy config remap for Xfce is set to `Super+Space`, to avoid conflicts with other Xfce functions. So if you set the shortcut for the Whisker Menu to `Super+Space`, it should start working when you use `Cmd+Space`. It shouldn't be necessary to disable Toshy, but the physical keys to set the shortcut to `Super+Space` with Toshy enabled will be physical `Ctrl+Space`.  

### GNOME and the Meta/Super/Win/Cmd key (`overlay-key`)

By default GNOME desktops seem to want to use the Meta/Super/Win/Cmd key to open the "overview". This is not a shortcut that is exposed in the usual `Settings >> Keyboard` control panel. The Toshy installer will disable the keybinding if GNOME is detected, since it's weird/unexpected in macOS for a modifier key to perform an action by itself.  

Here are the commands to disable and re-enable the `overlay-key` keybinding:  

Disable:  

```sh
gsettings set org.gnome.mutter overlay-key ''
```

Enable/Re-enable:  

```sh
gsettings reset org.gnome.mutter overlay-key
```

### GNOME "Switch Windows" vs "Switch Applications" (Cmd+Tab task-switching)

GNOME desktops have the ability to either do task-switching like Windows (switch between all open windows individually) or like macOS (switch between "applications" as groups of windows). Except where an extension is interfering with this ability, like the COSMIC desktop extension on Pop!_OS. Depending on the Linux distro, `Alt+Tab` may be assigned to "Switch windows" or to "Switch applications".  

If you want to task-switch more like macOS, set the "Switch applications" shortcut in the GNOME Keyboard settings control panel to be the one assigned `Alt+Tab`, and set the "Switch windows of an application" to be `Alt+Grave` (the "`" backtick/Grave character, above the Tab key).  

Note that this will also change the appearance and function of the task-switcher dialog that appears when you use the corresponding shortcut. The "Switch applications" shortcut is like the macOS task-switcher, it shows one large application icon for each group of windows belonging to the same "application". The "Switch windows" shortcut will show a task-switcher dialog that has a preview icon for every **_window_** open on the current workspace, similar to Windows and Linux desktop environments like KDE Plasma. The "large icons" task-switcher tends to have far fewer items and be easier to navigate visually. Just like on macOS, the equivalent of `Cmd+Grave` can be used to switch windows of the same application.  

Which task-switching style works for you is down to personal preference, and how well you like the macOS style of task-switching with `Cmd+Tab`.  

### KDE Plasma and the Meta/Super/Win/Cmd key

KDE Plasma desktops tend to have the Meta/Super/Win/Cmd key bound to open the application menu. Like the other desktop environments that bind the `Meta` key to do something by itself, this appears to be an alien concept as far as the regular keyboard shortcut control panel is concerned. You won't find it there. To disable this secret modifier-only binding, you have to put something in a hidden dotfile and refresh `KWin`.  

> UPDATE: The Toshy installer will now take care of this, and `toshy_setup.py` has command-line options to apply or remove this tweak independently of the full install procedure. 

Open the file `~/.config/kwinrc`, or create it if it doesn't exist. Append this information at the end of the file: 

```ini
[ModifierOnlyShortcuts]
Meta=
```

Then, run this command in the terminal: 

```sh
qdbus org.kde.KWin /KWin reconfigure
```

To undo this, remove or comment out the same text in the file, and run the same command. The `Meta` key binding should be back.  

More info about this:  

https://userbase.kde.org/Plasma/Tips#Windows.2FMeta_Key  

### Manjaro/Arcolinux KDE shortcut for Application Menu

Something strange is happening in Manjaro KDE and Arcolinux KDE desktops with the shortcut to open the application menu/launcher applet. In the primary shortcut settings control panel, there is a shortcut of `Alt+F1` set, which should work with the Toshy config. But the `Alt+F1` shortcut doesn't even work with Toshy disabled. If you right-click on the menu icon you can open the applet settings dialog and set the `Alt+F1` shortcut in its preferences (choose to reassign it) and then hit Apply, and it will start working with `Cmd+Space` when Toshy is enabled. And also it will now work even when Toshy is disabled. There are other identically named shortcut settings in the main KDE control panel for shortcuts, but they seem to want to open `krunner`, the search/launcher bar that pops out from the top of the screen.  

### More Will Follow...

I'll add to this as more testing happens and more reports/questions come in.  

### Sponsor Me / Donate

This type of project takes extraordinary amounts of time and effort to work around weird problems in different distros. If you feel like I did something useful by creating this, and you'd like me to be able to spend time maintaining and improving it, buy me a coffee:  

[![ko-fi](https://ko-fi.com/img/githubbutton_sm.svg)](https://ko-fi.com/G2G34VVZW)

Thanks for checking out Toshy!  

§
