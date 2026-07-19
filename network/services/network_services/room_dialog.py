import tkinter as tk
from typing import Tuple

class RoomDialog:
    """A modal popup dialog designed to match classic Win32 style."""
    
    def __init__(self) -> None:
        self.result: Tuple[str, str] = ("cancel", "")

    def show(self) -> Tuple[str, str]:
        """Presents the modal window and waits for user interaction."""
        root = tk.Tk()
        root.title("Room")
        root.geometry("330x120")
        root.resizable(False, False)
        root.configure(bg="#f0f0f0")
        
        # Center the dialog on screen
        screen_w = root.winfo_screenwidth()
        screen_h = root.winfo_screenheight()
        x = (screen_w - 330) // 2
        y = (screen_h - 120) // 2
        root.geometry(f"330x120+{x}+{y}")
        
        # Make the dialog modal and topmost
        root.attributes("-topmost", True)
        
        # Room name Label
        label = tk.Label(
            root, 
            text="room name", 
            bg="#f0f0f0", 
            fg="black",
            font=("MS Sans Serif", 8), 
            anchor="w"
        )
        label.place(x=10, y=10, width=100, height=15)
        
        # Entry text box with solid border and auto-focus
        entry = tk.Entry(
            root, 
            bg="white", 
            fg="black",
            bd=1, 
            relief="solid", 
            font=("MS Sans Serif", 8),
            insertbackground="black"
        )
        entry.place(x=10, y=30, width=310, height=20)
        entry.focus_set()
        
        # Button handlers
        def on_create():
            room_name = entry.get().strip()
            self.result = ("create", room_name)
            root.destroy()
            
        def on_join():
            room_name = entry.get().strip()
            self.result = ("join", room_name)
            root.destroy()
            
        def on_cancel():
            self.result = ("cancel", "")
            root.destroy()
            
        # Classic rectangular OS buttons
        btn_create = tk.Button(
            root, 
            text="Create", 
            bg="#e1e1e1", 
            activebackground="#cfcfcf", 
            fg="black",
            bd=1, 
            relief="solid", 
            font=("MS Sans Serif", 8), 
            command=on_create
        )
        btn_create.place(x=50, y=75, width=75, height=23)
        
        btn_join = tk.Button(
            root, 
            text="Join", 
            bg="#e1e1e1", 
            activebackground="#cfcfcf", 
            fg="black",
            bd=1, 
            relief="solid", 
            font=("MS Sans Serif", 8), 
            command=on_join
        )
        btn_join.place(x=130, y=75, width=75, height=23)
        
        btn_cancel = tk.Button(
            root, 
            text="Cancel", 
            bg="#e1e1e1", 
            activebackground="#cfcfcf", 
            fg="black",
            bd=1, 
            relief="solid", 
            font=("MS Sans Serif", 8), 
            command=on_cancel
        )
        btn_cancel.place(x=210, y=75, width=75, height=23)
        
        # Intercept window close button
        root.protocol("WM_DELETE_WINDOW", on_cancel)
        
        # Modal event loop block
        root.mainloop()
        
        return self.result
