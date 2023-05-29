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

var originalClient = workspace.activeClient;
var allClients = workspace.clientList();

// Index of the currently active client
var originalIndex = allClients.indexOf(originalClient);

// Calculate the index of the next client in the list
var nextIndex = (originalIndex + 1) % allClients.length;

// Activate the next client (equivalent to Alt+Tab)
workspace.activateClient(allClients[nextIndex]);

// Re-activate the original client (equivalent to Alt+Tab)
workspace.activateClient(originalClient);

if (workspace.activeClient) {
    notifyActiveWindow(workspace.activeClient);
}

workspace.clientActivated.connect(function(client){
    notifyActiveWindow(client);
});
