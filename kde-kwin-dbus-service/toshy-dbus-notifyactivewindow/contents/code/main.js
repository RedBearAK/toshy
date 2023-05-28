workspace.clientActivated.connect(function(client){
    console.log("client: " + client);
    console.log("caption: " + client.caption);
    console.log("resourceClass: " + client.resourceClass);
    console.log("resourceName: " + client.resourceName);

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
