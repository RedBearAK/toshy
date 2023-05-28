workspace.clientActivated.connect(function(client){
    callDBus(
        "org.toshy.Toshy",
        "/org/toshy/Toshy",
        "org.toshy.Toshy",
        "NotifyActiveWindow",
        "caption" in client ? client.caption : "",
        "resourceClass" in client ? client.resourceClass : "",
        "resourceName" in client ? client.resourceName : ""
    );
});
