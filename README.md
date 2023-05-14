# Toshy README

## Make your Linux keyboard act like a 'Tosh!

Toshy is a config file for the `keyszer` Python-based keymapper for Linux (which was forked from `xkeysnail`). The Toshy config is not strictly a fork of Kinto, but was based in the beginning entirely on the config file for Kinto.sh by Ben Reaves (https://github.com/rbreaves/kinto or https://kinto.sh). Without Kinto, Toshy would not exist.  Using Toshy will feel basically the same as using Kinto, just with some new features and some problems solved.  

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

 1. Automatic categorizing of the keyboard type of the current keyboard device. No more switching of keyboard types from the tray icon menu, or re-running the installer, or being asked to press a certain key on the keyboard during install. Some keyboard devices will need to be added to a Python list in the config to be recognized as the correct type. This will evolve over time from user feedback.  

 1. Changing of settings on-the-fly, without restarting the keymapper process. The tray icon menu and GUI preferences app will allow quickly enabling or disabling certain features, or changing the special characters layout. The change takes effect right away. (Adding or changing shortcuts in the config file will still require restarting the keymapper.)  

 1. Modmaps with `keyszer` are now concurrent/cascading rather than mutually exclusive. This enables some of the interesting fixes described in the following items.  

 1. Fix for "media" functions on arrow keys. Some laptop keyboards don't have the usual PgUp/PgDn/Home/End navigation functions on the arrow keys, when you hold the `Fn` key. Instead, they have PlayPause/Stop/Back/Forward. A `modmap` in the Toshy config will optionally fix this, making the arrow keys work more like a standard MacBook keyboard. This feature can be enabled from the tray icon or GUI preferences app.  

 1. This one is starting to become less relevant, with most common GTK apps already moving to GTK 4. But apps that use GTK 3 had a bug where they wouldn't recognize the "navigation" functions on the keypad keys (when NumLock is off) if you tried to use them with a modifier key (i.e., as part of a shortcut). Those keys would just get ignored. So if you didn't have the "real" navigation keys on your keyboard, there was no way to use shortcuts involving things like PgUp/PgDn/Home/End (on the numeric keypad). A `modmap` in the Toshy config will automatically fix this, if NumLock is off and the "Forced Numpad" feature (below) is disabled.  

 1. "Forced Numpad" feature: On PCs, if the keyboard has a numeric keypad, NumLock is typically off, so the keypad doesn't automatically act as a Numpad, but provides navigation functions until you turn NumLock on. But if you've used macOS for any length of time, you might have noticed that the numeric keypad is always a numeric keypad, and the "Clear" key sends `Escape` to clear calculator apps. You have to use `Fn+Clear` to disable NumLock and get to the navigation functions. A `modmap` in the Toshy config is enabled by default and makes the numeric keypad always a numeric keypad and turns the NumLock key into a "Clear" key. This can be disabled in the tray icon menu or GUI preferences app, or termporarily disabled with `Fn+Clear` (on Apple keyboards) or the equivalent of `Option+NumLock` on PC keyboards (usually this is physical `Win+NumLock`).  

 1. Sections of the config file are labeled with ASCII art designed to be readable on a "minimap" or "overview" sidebar view, to make finding certain parts of the config file a little easier. There's also a "tag" on each section that can be located easily with a `Find` search in any text editor.  

 1. Custom function to make the `Enter` key behave pretty much like it does in the Finder, in most Linux file managers. Mainly what this enables is using the `Enter` key to quickly rename files, while still leaving it usable in text fields like `Find` and the location bar. Not perfect, but works OK in most cases.  

 1. Evolving fix for the problem of `Cmd+W` unexpectedly failing to close a lot of Linux "child" windows and "dialog" windows (that have no binding to `Ctrl+W` and want either `Escape` or `Alt+F4/Ctrl+Q` to close). This can lead to a bad unconscious habit of hitting `Cmd+W` followed immediately by `Cmd+Q` (which becomes a problem when you're actually using macOS). The list of windows targeted by this pair of keymaps will grow over time, with input from users encountering the issue.  

 1. Fix for shortcut behavior in file save/open dialogs in apps like Firefox, now that WM_NAME is available. This is an addition to the "Finder Mods" that mimic Finder keyboard behavior in most common Linux file manager apps.  

 1. A collection of tab navigation fixes for various apps with a tabbed UI that don't use the mostly standard Ctrl+PgUp/PgDn shortcuts.  

 1. Another growing collection of enhancements to various Linux apps to enable shortcuts like Cmd+comma (preferences) and Cmd+I (get info/properties) to work in more apps.  

 1. A function (`matchProps()`) that enables very powerful and complex (or simple) matching on multiple properties at the same time. Application class, window name/title, device name, NumLock and CapsLock LED state.  

 1. More that I will add later when I remember...  

## Requirements

- Linux (no Windows support planned, use Kinto for Windows)
- `keyszer` (keymapper for Linux, forked from `xkeysnail`)
- X11 (Wayland support in `keyszer` is possible in the future)
- systemd (but you can just run the config from terminal or shell script)
- dbus-python (for the tray indicator and GUI app)

## Installation

Download the latest zip from the big green button. Unzip it, and open a terminal in the resulting folder. Run the `toshy_setup.py` script.  

```sh
./toshy_setup.py
```

Currently working distros:

- Ubuntu
- Xubuntu
- Kubuntu
- Linux Mint
- Fedora

## FAQ (Frequently Asked Questions)

This section will list some common questions, issues and fixes/tweaks that may be necessary for different distros, desktops or devices. 

### Option-key Special Character Entry (or Macros) Acting Weird

Sometimes, especially in virtual machines (but also on some bare metal installs) there is a problem in Linux with the "timing" of modifier key presses, leading to failures of some shortcut combos.  

The Option-key special characters in particular rely on a shortcut combo (`Shift+Ctrl+U`), and if that doesn't work the special character can't be created. And the mimicry of the highlighting of "dead keys" characters will probably also fail, since it does stuff like `Shift+Left`.  

This will also usually affect "macros" where you attempt to get the keymapper to type out multiple characters or strings or perform multiple shortcut combos when you use a shortcut. They may fail somewhere in the middle, or a shifted character will come out as a non-shifted character.  

A solution to this has been implemented in `keyszer`, and the API function is already in the Toshy config file. Injecting a short delay before and after the "normal" key press (to make sure that the modifier press and release are seen as happening with the correct timing) will usually solve the issue. Look for this code early in the Toshy config file:  

```py
throttle_delays(
    key_pre_delay_ms  = 0, # default: 0 ms, range: 0-150 ms, suggested: 1-50 ms
    key_post_delay_ms = 0, # default: 0 ms, range: 0-150 ms, suggested: 1-100 ms
)
```

For a bare metal install, a few milliseconds is usually sufficient to make infrequent glitches go away. Sometimes even as little as 1 ms, but often 2-4 ms for both delays is a good value to start with. For operating inside a virtual machine it may be necessary to use higher values like 50 ms (pre) and 70 ms (post) to get completely reliable behavior. With the right value the reliablity can be so close to 100% that it becomes impractical to find the failure in testing.  

NB: A lengthy delay will of course cause macros to come out quite a bit more slowly as the delay gets longer. So really long macros will be potentially impractical inside a virtual machine, for instance. This is why the values are clamped to a maximum of 150 ms each. The keyboard will be unresponsive while a long macro is coming out. Currently there is no way to interrupt the macro in progress. Not a big deal when the delay is 1 ms per character, but a problem if the total delay between characters is 150 ms or more.  

### Macros Acting Weird/Failing/Unreliable

See above for the fix.  

### KDE Plasma and Option-Key Special Characters

KDE Plasma desktops don't generally use `ibus` (like GNOME desktops usually do by default), or `fcitx` as an input manager. So you may find that the Option-key special character Unicode shortcut of `Shift+Ctrl+U` will not do anything, and the Unicode address of the special character will appear on screen instead of the desired character. This is unfortunately apparently not a shortcut that is built into the Linux kernel input system in general.  

The fix for this, if you want to use those characters in KDE apps, is to install `ibus` and use `im-chooser` to choose `ibus` as the input manager. You may also be able to use `fcitx` as I have seen some references to it supporting the `Shift+Ctrl+U` shortcut, but I haven't tested it.  

Otherwise, without a compatible input manager that responds to the `Shift+Ctrl+U` shortcut to enable Unicode character entry, the special characters will only work correctly in GTK-based applications, which seem to have the `ibus` response to that shortcut built into the GTK framework.  

### Sublime Text 3 and Option-Key Special Characters

For some reason, even when I am in GNOME, the Unicode character entry shortcut of `Shift+Ctrl+U` does not work in Sublime Text 3, so none of the Option-key special characters will work in that app. No idea why. Someone said that they couldn't replicate the problem in a build of Sublime Text 4, and that's all I know about it. No known workaround. (Other than moving to ST4.)  

### Xubuntu and the Meta/Super/Win/Cmd key

Xubuntu (using Xfce desktop environment) appears to run a background app at startup called `xcape` that binds the `Super/Meta/Win/Cmd` key (all different names for the same key) to activate the Whisker Menu by itself. To deactivate this, open the "Session and Startup" control panel app, go to the "Application Autostart" tab, and uncheck the "Bind Super Key" item. That will stop the `xcape` command from running at startup. Until you log out or restart, there will still be the background `xcape` process binding the key, but that can be stopped with:  

```sh
killall xcape
```

### Linux Mint Application Menu (Cinnamon/Xfce/MATE) and the Meta/Super/Win/Cmd key

On Linux Mint (Cinnamon and MATE variants) they use a custom menu widget/applet that is set up to activate with the Meta/Super/Win/Cmd key. The shortcut for this is not exposed in the usual keyboard shortcuts control panels. Right-click on the menu applet icon and go to "Configure" or "Preferences" (make sure you're not opening the preferences for the entire panel, just the menu applet).  

You will see a couple of things that vaguely look like buttons. You can click on the first one and set the shortcut to something like `Ctrl+Esc`. Click on the other button and hit `Backspace` and it will show "unassigned". This will disable the activation of the menu with the Meta/Super/Win/Cmd key. Alternately, you could set the secondary shortcut to `Alt+Space` (use the keys corresponding to `Option+Space` if Toshy is enabled), but you will have to track down the same shortcut in the regular keyboard shortcuts control panel (something like "Window menu"?) and disable it. If you do this, it will be possible to open the application menu with the same physical keys whether Toshy is enabled or disabled.  

You may need to temporarily DISABLE Toshy (from the tray icon menu, or the GUI preferences app) if it is active, in order to successfully set the shortcut to `Ctrl+Esc`. Then re-enable Toshy. Or, press the equivalent on your keyboard of `Cmd+Space` when setting the shortcut, and what should appear as the new shortcut is `Ctrl+Esc`.  

If Cinnamon is detected by the Toshy config, `Cmd+Space` will already be getting remapped onto `Ctrl+Esc`, so you should now be able to open the application menu with `Cmd+Space` if you assigned the suggested shortcut to it.  

In MATE, the remap is set to `Alt+Space`. To set this as the shortcut for the menu applet in MATE, Toshy must be disabled while setting the shortcut, then re-enabled afterward.  

In the Xfce variant of Mint, they use the Whisker Menu applet, and the shortcut (Super_L) is exposed in **_Keyboard >> Application Shortcuts_**. The remap for Xfce is set to `Super+Space`, to avoid conflicts with other Xfce functions. So if you set the shortcut for the Whisker Menu to `Super+Space`, it should start working when you use `Cmd+Space`. It shouldn't be necessary to disable Toshy, but the physical keys to set the shortcut to `Super+Space` with Toshy enabled will be physical `Ctrl+Space`.  

### GNOME and the Meta/Super/Win/Cmd key (`overlay-key`)

By default GNOME desktops seem to want to use the Meta/Super/Win/Cmd key to open the "overview". This is not a shortcut that is exposed in the usual _Settings >> Keyboard_ control panel. The Toshy installer will disable the binding if GNOME is detected, since it's weird/unexpected in macOS for a modifier key to perform an action by itself.  

Here are the commands to disable and re-enable the `overlay-key` binding:  

Disable:  

```sh
gsettings set org.gnome.mutter overlay-key ''
```

Enable/Re-enable:  

```sh
gsettings reset org.gnome.mutter overlay-key
```

### GNOME Switch Windows vs Switch Applications (Cmd+Tab task switching)

GNOME desktops have the ability to either do task switching like Windows (switch between all open windows individually) or like macOS (switch between "applications" as groups of windows). Except where an extension is interfering with this ability, like the COSMIC desktop extension on Pop!_OS. Depending on the Linux distro, `Alt+Tab` may be assigned to "Switch windows" or to "Switch applications". If you want to task switch more like macOS, set the "Switch applications" shortcut in the GNOME Keyboard settings control panel to be the one assigned `Alt+Tab`, and set the "Switch windows of an application" to be `Alt+Grave` (the "`" backtick/Grave character, above the Tab key).  

Note that this will also change the appearance and function of the task switcher dialog that appears when you use the corresponding shortcut. The "Switch applications" shortcut is like the macOS task switcher, it shows one large application icon for each group of windows belonging to the same "application". The "Switch windows" shortcut will show a task switcher that has a preview icon for every **_window_** open on the current workspace, similar to Windows and Linux desktop environments like KDE Plasma. The "large icons" task switcher tends to have far fewer items and be easier to navigate visually. Just like on macOS, the equivalent of `Cmd+Grave` can be used to switch windows of the same application. Which style works for you is down to personal prefernce, and how well you like the macOS style of task switching with `Cmd+Tab`.  

### KDE Plasma and the Meta/Super/Win/Cmd key

KDE Plasma desktops tend to have the Meta/Super/Win/Cmd key bound to open the application menu. Like the other desktop environments that bind the `Meta` key to do something by itself, this appears to be an alien concept as far as the regular keyboard shortcut control panel is concerned. You won't find it there. To disable this secret modifier-only binding, you have to put something in a hidden dotfile and refresh `KWin`.  

Open the file `~/.config/kwinrc`, or create it if it doesn't exist. Append this information at the end of the file: 

```ini
[ModifierOnlyShortcuts]
Meta=
```

Then, run this command in the terminal: 

```sh
qdbus org.kde.KWin /KWin reconfigure
```

To undo, remove or comment out the same text in the file, and run the same command. The `Meta` key binding should be back.  

### Manjaro GNOME Cmd+Q (Close Window) shortcut

The GNOME variant of Manjaro has the "Close Window" shortcut set to Super+Q instead of the typical `Alt+F4`. This will make it impossible to close windows with `Cmd+Q` and will disable part of the fix for the `Cmd+W` problem, which for some windows remaps to `Alt+F4` to close the window. The recommended solution at this time is to change the shortcut for "Close Window" in the Manjaro GNOME Keyboard settings control panel back to `Alt+F4`.  

It would be possible to support the default shortcut, but would be more complicated to implement a fix for the windows that need `Cmd+W` to remap to `Alt+F4`. But perhaps this should be done at some point...  

### More Will Follow...

I'll add to this as more testing happens and more reports come in.  
