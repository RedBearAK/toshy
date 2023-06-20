function notifyActiveWindow(client){
    // Check if the client is null (might be null when task switcher dialog has focus)
    if (!client) {
        console.log("The client object is null");
        return;
    }

    var caption = client.hasOwnProperty('caption') ? client.caption : "UNDEF";
    var resourceClass = client.hasOwnProperty('resourceClass') ? client.resourceClass : "UNDEF";
    var resourceName = client.hasOwnProperty('resourceName') ? client.resourceName : "UNDEF";

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

workspace.clientActivated.connect(function(client){
    notifyActiveWindow(client);
});
