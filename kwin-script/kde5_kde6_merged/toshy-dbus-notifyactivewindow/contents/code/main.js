/*
KWin Script Toshy D-Bus Notify Active Window - Input-Triggered Approach
(C) 2023-25 RedBearAK <64876997+RedBearAK@users.noreply.github.com>
GNU General Public License v3.0
*/

const debugMode = readConfig("debugMode", true);
function debug(...args) {
    if (debugMode) { console.debug("toshy-dbus-notifyactivewindow:", ...args); }
}
debug("Initializing input-triggered approach");

// Detect KDE version
const isKDE6 = typeof workspace.windowList === 'function';

// Abstraction for connecting to events
let connectWindowActivated;
let activeWindow;
if (isKDE6) {
    connectWindowActivated = (handler) => workspace.windowActivated.connect(handler);
    activeWindow = () => workspace.activeWindow;
} else {
    connectWindowActivated = (handler) => workspace.clientActivated.connect(handler);
    activeWindow = () => workspace.activeClient;
}

// Track the last known active window info
let lastActiveWindowInfo = {
    caption: "",
    resourceClass: "",
    resourceName: ""
};

function notifyActiveWindow(window) {
    if (!window) {
        debug("The window object is null");
        return;
    }

    var caption = window.hasOwnProperty('caption') ? window.caption : "UNDEF";
    var resourceClass = window.hasOwnProperty('resourceClass') ? window.resourceClass : "UNDEF";
    var resourceName = window.hasOwnProperty('resourceName') ? window.resourceName : "UNDEF";

    debug("Notifying DBus - Caption:", caption, "Class:", resourceClass);

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

function checkActiveWindowChanged() {
    const current = activeWindow();
    if (!current) return;
    
    const currentInfo = {
        caption: current.hasOwnProperty('caption') ? current.caption : "UNDEF",
        resourceClass: current.hasOwnProperty('resourceClass') ? current.resourceClass : "UNDEF",
        resourceName: current.hasOwnProperty('resourceName') ? current.resourceName : "UNDEF"
    };
    
    // Check if anything changed
    if (currentInfo.caption !== lastActiveWindowInfo.caption ||
        currentInfo.resourceClass !== lastActiveWindowInfo.resourceClass ||
        currentInfo.resourceName !== lastActiveWindowInfo.resourceName) {
        
        debug("Active window info changed - updating DBus");
        debug("Old caption:", lastActiveWindowInfo.caption, "New caption:", currentInfo.caption);
        
        lastActiveWindowInfo = currentInfo;
        notifyActiveWindow(current);
    }
}

// Handle window activation (the reliable part)
function onWindowActivated(window) {
    debug("Window activated:", window ? window.caption : "null");
    
    // Update our tracking and notify DBus
    if (window) {
        lastActiveWindowInfo = {
            caption: window.hasOwnProperty('caption') ? window.caption : "UNDEF",
            resourceClass: window.hasOwnProperty('resourceClass') ? window.resourceClass : "UNDEF",
            resourceName: window.hasOwnProperty('resourceName') ? window.resourceName : "UNDEF"
        };
    }
    
    notifyActiveWindow(window);
}

// Try to connect to user interaction events as triggers
function tryConnectInputEvents() {
    let connectedEvents = 0;
    
    // Try pointer button events (mouse clicks - perfect for tab clicking)
    try {
        if (typeof workspace.pointerButtonStateChanged !== 'undefined') {
            debug("Connecting to pointerButtonStateChanged signal");
            workspace.pointerButtonStateChanged.connect(checkActiveWindowChanged);
            connectedEvents++;
        }
    } catch (e) {
        debug("pointerButtonStateChanged not available:", e);
    }
    
    // Try keyboard modifier events (catches Ctrl+Tab, Alt+Tab, etc.)
    try {
        if (typeof workspace.keyboardModifiersChanged !== 'undefined') {
            debug("Connecting to keyboardModifiersChanged signal");
            workspace.keyboardModifiersChanged.connect(checkActiveWindowChanged);
            connectedEvents++;
        }
    } catch (e) {
        debug("keyboardModifiersChanged not available:", e);
    }
    
    debug("Connected to", connectedEvents, "input event signals");
    return connectedEvents > 0;
}

// Connect to window activation events
connectWindowActivated(onWindowActivated);

// Try to connect to user interaction events as triggers
if (!tryConnectInputEvents()) {
    debug("Input events not available - falling back to captionChanged approach");
    
    // Fallback: still try captionChanged even though it seems broken
    let trackedWindows = new Set();
    
    function onWindowActivatedWithCaption(window) {
        onWindowActivated(window);
        
        // Set up captionChanged tracking (maybe it works sometimes?)
        if (window && window.captionChanged && !trackedWindows.has(window)) {
            debug("Setting up captionChanged tracking for:", window.caption);
            trackedWindows.add(window);
            
            window.captionChanged.connect(() => {
                debug("captionChanged fired for:", window.caption);
                checkActiveWindowChanged();
            });
        }
    }
    
    // Replace the simple handler with the caption-tracking one
    connectWindowActivated(onWindowActivatedWithCaption);
}

debug("Script loaded - using input-triggered active window monitoring");


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
