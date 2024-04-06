/*
KWin Script Toshy D-Bus Notify Active Window
(C) 2023-24 RedBearAK <64876997+RedBearAK@users.noreply.github.com>
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
if (isKDE6) {
    // For KDE 6
    connectWindowActivated = (handler) => workspace.windowActivated.connect(handler);
} else {
    // For KDE 5
    connectWindowActivated = (handler) => workspace.clientActivated.connect(handler);
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

    callDBus(
        "org.toshy.Toshy",
        "/org/toshy/Toshy",
        "org.toshy.Toshy",
        "NotifyActiveWindow",
        caption,
        resourceClass,
        resourceName
    );
}


// Connect the event with the handler using the abstraction
connectWindowActivated(notifyActiveWindow);


// Test running a loop to overcome the problem of 
// window titles not updating in apps with tabbed UI if
// no window event has occurred (i.e., when switching tabs)

// Adding a loop to periodically execute notifyActiveWindow with the active window
const intervalTime = 500; // intervalTime is in milliseconds
setInterval(() => {
    let activeWindow = workspace.activeClient;
    if (activeWindow) {
        notifyActiveWindow(activeWindow);
    }
}, intervalTime);
