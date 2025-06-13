/*
KWin Script Toshy D-Bus Notify Active Window - Direct Signal Approach
(C) 2023-24 RedBearAK <64876997+RedBearAK@users.noreply.github.com>
GNU General Public License v3.0
*/

const debugMode = readConfig("debugMode", true);
function debug(...args) {
    if (debugMode) { console.debug("toshy-dbus-notifyactivewindow:", ...args); }
}
debug("initializing direct signal approach");

// Detect KDE version
const isKDE6 = typeof workspace.windowList === 'function';

// Set up aliases just like the working app switcher script
let activeWindow;
let connectWindowActivated;
if (isKDE6) {
    activeWindow = () => workspace.activeWindow;
    connectWindowActivated = (handler) => workspace.windowActivated.connect(handler);
} else {
    activeWindow = () => workspace.activeClient;
    connectWindowActivated = (handler) => workspace.clientActivated.connect(handler);
}

// Track last known window info
let lastWindowInfo = "";

function notifyActiveWindow(window) {
    if (!window) {
        debug("window object is null");
        return;
    }

    var caption = window.hasOwnProperty('caption') ? window.caption : "UNDEF";
    var resourceClass = window.hasOwnProperty('resourceClass') ? window.resourceClass : "UNDEF";
    var resourceName = window.hasOwnProperty('resourceName') ? window.resourceName : "UNDEF";

    debug("notifying DBus - Caption:", caption, "Class:", resourceClass);

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

function checkForTitleChange() {
    const current = activeWindow();
    if (current) {
        const currentTitle = current.caption || "";
        if (currentTitle !== lastWindowInfo) {
            debug("title changed from", lastWindowInfo, "to", currentTitle);
            lastWindowInfo = currentTitle;
            notifyActiveWindow(current);
        }
    }
}

function onWindowActivated(window) {
    debug("window activated:", window ? window.caption : "null");
    if (window) {
        lastWindowInfo = window.caption || "";
    }
    notifyActiveWindow(window);
}

// Connect to window activation - this definitely works
connectWindowActivated(onWindowActivated);

// Try direct connections to input signals
debug("attempting to connect input signals");
workspace.pointerButtonStateChanged.connect(checkForTitleChange);
workspace.keyboardModifiersChanged.connect(checkForTitleChange);

debug("script loaded with direct signal connections");



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
