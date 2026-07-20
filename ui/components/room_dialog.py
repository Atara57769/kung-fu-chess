import tkinter as tk

class RoomDialog:
    """A native OS dialog using Tkinter to prompt for Room name/ID."""
    
    def __init__(self, parent_title: str = "Room") -> None:
        self.result_action = None  # 'create', 'join', or None
        self.room_name = ""
        
        self.root = tk.Tk()
        self.root.title(parent_title)
        self.root.geometry("300x125")
        self.root.resizable(False, False)
        
        self.root.update_idletasks()
        w = self.root.winfo_width()
        h = self.root.winfo_height()
        x = (self.root.winfo_screenwidth() - w) // 2
        y = (self.root.winfo_screenheight() - h) // 2
        self.root.geometry(f"+{x}+{y}")
        
        self.root.attributes("-topmost", True)
        
        self.label = tk.Label(self.root, text="room name")
        self.label.pack(anchor="w", padx=15, pady=(10, 2))
        
        self.entry = tk.Entry(self.root, width=35)
        self.entry.pack(fill="x", padx=15, pady=(0, 10))
        self.entry.focus_set()
        
        self.btn_frame = tk.Frame(self.root)
        self.btn_frame.pack(fill="x", padx=15, pady=5)
        
        self.btn_create = tk.Button(self.btn_frame, text="Create", width=8, command=self._on_create)
        self.btn_create.pack(side="left", padx=(0, 5))
        
        self.btn_join = tk.Button(self.btn_frame, text="Join", width=8, command=self._on_join)
        self.btn_join.pack(side="left", padx=5)
        
        self.btn_cancel = tk.Button(self.btn_frame, text="Cancel", width=8, command=self._on_cancel)
        self.btn_cancel.pack(side="right", padx=(5, 0))
        
        self.root.bind("<Return>", lambda event: self._on_join())
        self.root.bind("<Escape>", lambda event: self._on_cancel())
        self.root.protocol("WM_DELETE_WINDOW", self._on_cancel)
        
        self.root.mainloop()
        
    def _on_create(self) -> None:
        self.result_action = "create"
        self.room_name = self.entry.get().strip()
        self.root.destroy()
        
    def _on_join(self) -> None:
        self.result_action = "join"
        self.room_name = self.entry.get().strip()
        self.root.destroy()
        
    def _on_cancel(self) -> None:
        self.result_action = None
        self.root.destroy()
