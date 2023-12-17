// Cinnamon extension to provide focused window info via D-Bus interface

// debugging: 
// The output of the debug statements typically goes to the Looking Glass log 
// in Cinnamon, which can be accessed through the lg command in the Alt+F2 
// run dialog, or directly in ~/.cinnamon/glass.log.

// testing from terminal: 
// dbus-send --print-reply --dest=app.toshy.ToshyFocusedWindow /app/toshy/ToshyFocusedWindow app.toshy.ToshyFocusedWindow.GetFocusedWindowInfo
// qdbus app.toshy.ToshyFocusedWindow /app/toshy/ToshyFocusedWindow app.toshy.ToshyFocusedWindow.GetFocusedWindowInfo
// gdbus call --session --dest app.toshy.ToshyFocusedWindow --object-path /app/toshy/ToshyFocusedWindow --method app.toshy.ToshyFocusedWindow.GetFocusedWindowInfo


const Gio = imports.gi.Gio;

const dbus_iface_name = 'app.toshy.ToshyFocusedWindow'
const dbus_iface_path = '/app/toshy/ToshyFocusedWindow'

const DBusInterfaceXML = `
<node>
    <interface name='${dbus_iface_name}'>
        <method name='GetFocusedWindowInfo'>
            <arg type='s' direction='out' name='windowInfo' />
        </method>
    </interface>
</node>`;

const Extension = class {
    GetFocusedWindowInfo() {
        let focusedWindow   = global.display.focus_window;
        let appClass        = "ERR_no_focusedWindow";
        let windowTitle     = "ERR_no_focusedWindow";
        if (focusedWindow) {
            appClass        = focusedWindow.get_wm_class() || "ERR_no_appClass";
            windowTitle     = focusedWindow.get_title() || "ERR_no_windowTitle";
        }
        return JSON.stringify({ "appClass": appClass, "windowTitle": windowTitle });
    }
};

let dbusObject;

function enable() {
    let dbusInterfaceInfo = Gio.DBusNodeInfo.new_for_xml(DBusInterfaceXML).interfaces[0];
    dbusObject = new Gio.DBusExportedObject.wrapJSObject(dbusInterfaceInfo, new Extension());
    // dbusObject.export(Gio.DBus.session, '/org/cinnamon/extensions/ToshyFocusedWindow');
    dbusObject.export(Gio.DBus.session, dbus_iface_path);
}

function disable() {
    if (dbusObject) {
        dbusObject.unexport();
        dbusObject = null;
    }
}
