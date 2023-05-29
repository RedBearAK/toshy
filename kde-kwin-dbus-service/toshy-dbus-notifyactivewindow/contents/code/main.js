// Original form of the KWin script:

// workspace.clientActivated.connect(function(client){
//     callDBus(
//         "org.toshy.Toshy",
//         "/org/toshy/Toshy",
//         "org.toshy.Toshy",
//         "NotifyActiveWindow",
//         "caption" in client ? client.caption : "",
//         "resourceClass" in client ? client.resourceClass : "",
//         "resourceName" in client ? client.resourceName : ""
//     );
// });

function notifyActiveWindow(client){
    callDBus(
        "org.toshy.Toshy",
        "/org/toshy/Toshy",
        "org.toshy.Toshy",
        "NotifyActiveWindow",
        "caption" in client ? client.caption : "",
        "resourceClass" in client ? client.resourceClass : "",
        "resourceName" in client ? client.resourceName : ""
    );
}

if (workspace.activeClient) {
    notifyActiveWindow(workspace.activeClient);
}

workspace.clientActivated.connect(function(client){
    notifyActiveWindow(client);
});
