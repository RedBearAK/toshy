function notifyActiveWindow(window){
    // Check if the client is null (might be null when task switcher dialog has focus)
    if (!window) {
        console.log("The client object is null");
        return;
    }

    var caption = window.hasOwnProperty('caption') ? window.caption : "UNDEF";
    var resourceClass = window.hasOwnProperty('resourceClass') ? window.resourceClass : "UNDEF";
    var resourceName = window.hasOwnProperty('resourceName') ? window.resourceName : "UNDEF";

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

// Set up the function link to the event
workspace.windowActivated.connect(notifyActiveWindow);
