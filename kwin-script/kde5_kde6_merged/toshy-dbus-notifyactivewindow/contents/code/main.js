/*
KWin Script Toshy D-Bus Notify Active Window - Enhanced with Title Change Detection
(C) 2023-25 RedBearAK <64876997+RedBearAK@users.noreply.github.com>
GNU General Public License v3.0
*/

const debugMode = readConfig("debugMode", true);
function debug(...args) {
    if (debugMode) { console.debug("toshy-dbus-notifyactivewindow:", ...args); }
}
debug("Initializing");

// Detect KDE version
const isKDE6 = typeof workspace.windowList === 'function';

// Abstraction for connecting to window activation event
let connectWindowActivated;
let connectWindowClosed;
let activeWindow;

if (isKDE6) {
    // For KDE 6
    connectWindowActivated  = (handler) => workspace.windowActivated.connect(handler);
    connectWindowClosed     = (handler) => workspace.windowRemoved.connect(handler);
    activeWindow            = () => workspace.activeWindow;
} else {
    // For KDE 5
    connectWindowActivated  = (handler) => workspace.clientActivated.connect(handler);
    connectWindowClosed     = (handler) => workspace.clientRemoved.connect(handler);
    activeWindow            = () => workspace.activeClient;
}

function notifyActiveWindow(window){
    // Check if the window object is null (might be null when task switcher dialog has focus)
    if (!window) {
        debug("The window object is null");
        return;
    }

    var caption         = window.hasOwnProperty('caption')          ? window.caption : "UNDEF";
    var resourceClass   = window.hasOwnProperty('resourceClass')    ? window.resourceClass : "UNDEF";
    var resourceName    = window.hasOwnProperty('resourceName')     ? window.resourceName : "UNDEF";

    debug("Notifying DBus - Caption:", caption, "Class:", resourceClass, "Name:", resourceName);

    callDBus(
        "org.toshy.Plasma",
        "/org/toshy/Plasma",
        "org.toshy.Plasma",
        "NotifyActiveWindow",
        caption,
        resourceClass,
        resourceName
    );
}

// Track which windows already have caption change listeners (avoids duplicates)
let trackedWindows = new Set();
// Track the currently active window for caption changes
let currentActiveWindow = null;

// Enhanced window activation handler
function onWindowActivated(window) {
    debug("Window activated:", window ? window.caption : "null");
    notifyActiveWindow(window);
    
    // Update which window we're tracking for caption changes
    currentActiveWindow = window;
    
    // Set up caption change tracking for this window (only once per window)
    if (window && window.captionChanged && !trackedWindows.has(window)) {
        debug("Setting up caption tracking for:", window.caption);
        trackedWindows.add(window);
        
        window.captionChanged.connect(() => {
            // Only notify if this window is still the active one
            if (window === currentActiveWindow) {
                debug("Active window caption changed:", window.caption);
                notifyActiveWindow(window);
            } else {
                debug("Ignoring caption change from inactive window:", window.caption);
            }
        });
    }
}

// Clean up the Set when windows are closed
function onWindowClosed(window) {
    if (window && trackedWindows.has(window)) {
        debug("Removing closed window from tracking:", window.caption);
        trackedWindows.delete(window);
        
        // Clear currentActiveWindow if it was the one that closed
        if (window === currentActiveWindow) {
            currentActiveWindow = null;
        }
    }
}

// Connect the main event handlers
connectWindowActivated(onWindowActivated);
connectWindowClosed(onWindowClosed);



/////////////////////////////////////////////////////////////////////////////////////////////////////
/////////////////////////////////////////////////////////////////////////////////////////////////////
/////////////////////////////////////////////////////////////////////////////////////////////////////
/////////////////////////////////////////////////////////////////////////////////////////////////////
/////////////////////////////////////////////////////////////////////////////////////////////////////
/////////////////////////////////////////////////////////////////////////////////////////////////////
/////////////////////////////////////////////////////////////////////////////////////////////////////
/////////////////////////////////////////////////////////////////////////////////////////////////////
/////////////////////////////////////////////////////////////////////////////////////////////////////
/////////////////////////////////////////////////////////////////////////////////////////////////////
/////////////////////////////////////////////////////////////////////////////////////////////////////
/////////////////////////////////////////////////////////////////////////////////////////////////////
/////////////////////////////////////////////////////////////////////////////////////////////////////



// /*
// KWin Script Toshy D-Bus Notify Active Window
// (C) 2023-24 RedBearAK <64876997+RedBearAK@users.noreply.github.com>
// GNU General Public License v3.0
// */

// const debugMode = readConfig("debugMode", true);
// function debug(...args) {
//     if (debugMode) { console.debug("toshy-dbus-notifyactivewindow:", ...args); }
// }
// debug("Initializing");

// // Detect KDE version
// const isKDE6 = typeof workspace.windowList === 'function';

// // Abstraction for connecting to window activation event
// let connectWindowActivated;
// if (isKDE6) {
//     // For KDE 6
//     connectWindowActivated = (handler) => workspace.windowActivated.connect(handler);
// } else {
//     // For KDE 5
//     connectWindowActivated = (handler) => workspace.clientActivated.connect(handler);
// }


// function notifyActiveWindow(window){
//     // Check if the window object is null (might be null when task switcher dialog has focus)
//     if (!window) {
//         debug("The window object is null");
//         return;
//     }

//     var caption         = window.hasOwnProperty('caption')          ? window.caption : "UNDEF";
//     var resourceClass   = window.hasOwnProperty('resourceClass')    ? window.resourceClass : "UNDEF";
//     var resourceName    = window.hasOwnProperty('resourceName')     ? window.resourceName : "UNDEF";

//     callDBus(
//         "org.toshy.Plasma",
//         "/org/toshy/Plasma",
//         "org.toshy.Plasma",
//         "NotifyActiveWindow",
//         caption,
//         resourceClass,
//         resourceName
//     );
// }


// // Connect the event with the handler using the abstraction
// connectWindowActivated(notifyActiveWindow);


// // We need a way to run a loop that can update the window title for 
// // apps with tabbed UIs. But loop techniques don't seem to work in
// // KWin scripts. 
