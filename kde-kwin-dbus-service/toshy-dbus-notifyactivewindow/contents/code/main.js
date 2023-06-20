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

// function notifyActiveWindow(client){
//     callDBus(
//         "org.toshy.Toshy",
//         "/org/toshy/Toshy",
//         "org.toshy.Toshy",
//         "NotifyActiveWindow",
//         "caption" in client ? client.caption : "UNDEF",
//         "resourceClass" in client ? client.resourceClass : "UNDEF",
//         "resourceName" in client ? client.resourceName : "UNDEF"
//     );
// }

function notifyActiveWindow(client){
    var caption = client.hasOwnProperty('caption') ? client.caption : "UNDEF";
    var resourceClass = client.hasOwnProperty('resourceClass') ? client.resourceClass : "UNDEF";
    var resourceName = client.hasOwnProperty('resourceName') ? client.resourceName : "UNDEF";
    
    console.log("Calling D-Bus with the following variables:");
    console.log("Caption: " + caption);
    console.log("Resource Class: " + resourceClass);
    console.log("Resource Name: " + resourceName);
    
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

if (workspace.activeClient) {
    notifyActiveWindow(workspace.activeClient);
}

workspace.clientActivated.connect(function(client){
    notifyActiveWindow(client);
});
