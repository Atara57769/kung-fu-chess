import tkinter as tk

DEFAULT_PARENT_TITLE = "Room"
WINDOW_GEOMETRY = "300x125"
WINDOW_GEOMETRY_OFFSET = "+{}+{}"
TK_TOPMOST_ATTR = "-topmost"
LABEL_ROOM_NAME = "room name"
ANCHOR_WEST = "w"
FILL_X = "x"
BTN_LABEL_CREATE = "Create"
BTN_LABEL_JOIN = "Join"
BTN_LABEL_CANCEL = "Cancel"
SIDE_LEFT = "left"
SIDE_RIGHT = "right"
EVENT_RETURN = "<Return>"
EVENT_ESCAPE = "<Escape>"
PROTOCOL_DELETE_WINDOW = "WM_DELETE_WINDOW"
ACTION_CREATE = "create"
ACTION_JOIN = "join"


class RoomDialog:
    """A native OS dialog using Tkinter to prompt for Room name/ID."""
    
    def __init__(self, parent_title: str = DEFAULT_PARENT_TITLE) -> None:
        self.result_action = None  # 'create', 'join', or None
        self.room_name = ""
        
        self.root = tk.Tk()
        self.root.title(parent_title)
        self.root.geometry(WINDOW_GEOMETRY)
        self.root.resizable(False, False)
        
        self.root.update_idletasks()
        w = self.root.winfo_width()
        h = self.root.winfo_height()
        x = (self.root.winfo_screenwidth() - w) // 2
        y = (self.root.winfo_screenheight() - h) // 2
        self.root.geometry(WINDOW_GEOMETRY_OFFSET.format(x, y))
        
        self.root.attributes(TK_TOPMOST_ATTR, True)
        
        self.label = tk.Label(self.root, text=LABEL_ROOM_NAME)
        self.label.pack(anchor=ANCHOR_WEST, padx=15, pady=(10, 2))
        
        self.entry = tk.Entry(self.root, width=35)
        self.entry.pack(fill=FILL_X, padx=15, pady=(0, 10))
        self.entry.focus_set()
        
        self.btn_frame = tk.Frame(self.root)
        self.btn_frame.pack(fill=FILL_X, padx=15, pady=5)
        
        self.btn_create = tk.Button(self.btn_frame, text=BTN_LABEL_CREATE, width=8, command=self._on_create)
        self.btn_create.pack(side=SIDE_LEFT, padx=(0, 5))
        
        self.btn_join = tk.Button(self.btn_frame, text=BTN_LABEL_JOIN, width=8, command=self._on_join)
        self.btn_join.pack(side=SIDE_LEFT, padx=5)
        
        self.btn_cancel = tk.Button(self.btn_frame, text=BTN_LABEL_CANCEL, width=8, command=self._on_cancel)
        self.btn_cancel.pack(side=SIDE_RIGHT, padx=(5, 0))
        
        self.root.bind(EVENT_RETURN, lambda event: self._on_join())
        self.root.bind(EVENT_ESCAPE, lambda event: self._on_cancel())
        self.root.protocol(PROTOCOL_DELETE_WINDOW, self._on_cancel)
        
        self.root.mainloop()
        
    def _on_create(self) -> None:
        self.result_action = ACTION_CREATE
        self.room_name = self.entry.get().strip()
        self.root.destroy()
        
    def _on_join(self) -> None:
        self.result_action = ACTION_JOIN
        self.room_name = self.entry.get().strip()
        self.root.destroy()
        
    def _on_cancel(self) -> None:
        self.result_action = None
        self.root.destroy()

