import Clutter from "gi://Clutter";
import Meta from "gi://Meta";
import { overview } from "resource:///org/gnome/shell/ui/main.js";
import { Extension } from "resource:///org/gnome/shell/extensions/extension.js";

let DEBUGGING = false;
const POINTER_SUPPRESSION_MS = 2000;

let EXT_NAME = "unknown_extension";
let suppressPointerWarpUntil = 0;

export default class MouseFollowsFocus extends Extension {
    constructor(metadata) {
        super(metadata);
        EXT_NAME = metadata.name;
    }

    enable() {
        dbg_log(`enabling ${EXT_NAME}`);
        reset_pointer_suppression();

        for (const actor of global.get_window_actors()) {
            if (actor.is_destroyed()) {
                continue;
            }

            const win = actor.get_meta_window();
            connect_to_window(win);
        }

        this.create_signal = global.display.connect(
            "window-created",
            (_ignore, win) => {
                dbg_log(`window created ${win}`);

                connect_to_window(win);
            },
        );

        this.hide_signal = overview.connect("hidden", () => {
            // the focus might change whilst we're in the overview, i.e. by
            // searching for an already open app.
            const win = get_focused_window();
            if (win !== null) {
                focus_changed(win);
            }
        });

        this.pointer_signal = global.stage.connect(
            "captured-event",
            (_actor, event) => {
                record_pointer_input(event);
                return Clutter.EVENT_PROPAGATE;
            },
        );
    }

    disable() {
        dbg_log(`disabling ${EXT_NAME}`);

        if (this.create_signal !== undefined) {
            global.display.disconnect(this.create_signal);
            this.create_signal = undefined;
        }

        if (this.hide_signal !== undefined) {
            overview.disconnect(this.hide_signal);
            this.hide_signal = undefined;
        }

        if (this.pointer_signal !== undefined) {
            global.stage.disconnect(this.pointer_signal);
            this.pointer_signal = undefined;
        }

        for (const actor of global.get_window_actors()) {
            if (actor.is_destroyed()) {
                continue;
            }

            const win = actor.get_meta_window();
            if (win._mousefollowsfocus_extension_signal) {
                win.disconnect(win._mousefollowsfocus_extension_signal);
                delete win._mousefollowsfocus_extension_signal;
            }
        }

        reset_pointer_suppression();
    }
}

function reset_pointer_suppression() {
    suppressPointerWarpUntil = 0;
}

function record_pointer_input(event) {
    if (event === null) {
        return;
    }

    switch (event.type()) {
    case Clutter.EventType.KEY_PRESS:
        suppressPointerWarpUntil = 0;
        dbg_log("keyboard input cleared pointer suppression");
        break;
    case Clutter.EventType.BUTTON_PRESS:
    case Clutter.EventType.BUTTON_RELEASE:
    case Clutter.EventType.TOUCH_BEGIN:
    case Clutter.EventType.TOUCH_END:
        suppressPointerWarpUntil = Date.now() + POINTER_SUPPRESSION_MS;
        dbg_log(`suppressing pointer warp until ${suppressPointerWarpUntil}`);
        break;
    default:
        break;
    }
}

function pointer_warp_is_suppressed() {
    return Date.now() <= suppressPointerWarpUntil;
}

function get_window_actor(window) {
    for (const actor of global.get_window_actors()) {
        if (!actor.is_destroyed() && actor.get_meta_window() === window) {
            return actor;
        }
    }

    return undefined;
}

function cursor_within_window(mouse_x, mouse_y, win) {
    // use get_buffer_rect instead of get_frame_rect here, because the frame_rect may
    // exclude shadows, which might already cause a focus-on-hover event, therefore causing
    // the pointer to jump around eratically.
    let rect = win.get_buffer_rect();

    dbg_log(`window rect: ${rect.x}:${rect.y} - ${rect.width}:${rect.height}`);

    return (
        mouse_x >= rect.x &&
        mouse_x <= rect.x + rect.width &&
        mouse_y >= rect.y &&
        mouse_y <= rect.y + rect.height
    );
}

function dbg_log(message) {
    if (DEBUGGING) {
        console.log(EXT_NAME, message);
    }
}

function focus_changed(win) {
    const actor = get_window_actor(win);
    dbg_log("window focus event received");

    if (actor) {
        let rect = win.get_buffer_rect();

        let [mouse_x, mouse_y, _] = global.get_pointer();

        if (cursor_within_window(mouse_x, mouse_y, win)) {
            dbg_log("pointer within window, discarding event");
        } else if (overview.visible) {
            dbg_log("overview visible, discarding event");
        } else if (rect.width < 10 && rect.height < 10) {
            // xdg-copy creates a 1x1 pixel window to capture mouse events.
            // Ignore this and similar windows.
            dbg_log("window too small, discarding event");
        } else if (pointer_warp_is_suppressed()) {
            dbg_log("recent pointer input, discarding event");
        } else {
            dbg_log("targeting new window");
            let seat = Clutter.get_default_backend().get_default_seat();
            if (seat !== null) {
                seat.warp_pointer(
                    rect.x + rect.width / 2,
                    rect.y + rect.height / 2,
                );
            } else {
                dbg_log("seat is null!");
            }
        }
    }
}

function connect_to_window(win) {
    const type = win.get_window_type();
    if (type !== Meta.WindowType.NORMAL) {
        dbg_log(`ignoring window, window type: ${type}`);
        return;
    }

    win._mousefollowsfocus_extension_signal = win.connect(
        "focus",
        focus_changed,
    );
}

function get_focused_window() {
    return global.display.focus_window;
}
