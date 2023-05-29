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
        "caption" in client ? client.caption : "UNDEF",
        "resourceClass" in client ? client.resourceClass : "UNDEF",
        "resourceName" in client ? client.resourceName : "UNDEF"
    );
}

if (workspace.activeClient) {
    notifyActiveWindow(workspace.activeClient);
}

if (client) {
    notifyActiveWindow(client)
}

workspace.clientActivated.connect(function(client){
    notifyActiveWindow(client);
});
