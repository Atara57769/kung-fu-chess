import cv2
import numpy as np
from ui.rendering.img import Img
from ui.screens.base_screen import Screen
from ui.components.button import Button
from ui.components.label import Label
from ui.components.popup import Popup
from ui.ui_config import BG_COLOR_BGR

class HomeScreen(Screen):
    """Presents the main home dashboard with matchmaking and room options."""
    
    def __init__(self, screen_manager, width: int, height: int, username: str = "Player", rating: int = 1200) -> None:
        self.screen_manager = screen_manager
        self.width = width
        self.height = height
        self.username = username
        self.rating = rating
        
        self.popup = None
        self.buttons: list[Button] = []
        self.labels: list[Label] = []
        
        self._setup_components()

    def _setup_components(self) -> None:
        """Initializes the labels, buttons and popup dialogs on the home screen."""
        cx = self.width // 2
        
        # Labels
        self.labels.append(Label(cx, 80, "KUNG-FU CHESS", centered=True))
        self.labels.append(Label(cx, 130, f"Welcome, {self.username} (ELO: {self.rating})", centered=True))
        
        # Buttons
        self.buttons.append(Button(cx - 130, 200, 260, 45, "Quick Match", self._on_quick_match))
        self.buttons.append(Button(cx - 130, 260, 260, 45, "Custom Room", self._on_custom_room_click))
        
        # Popup for room actions
        popup_buttons = [
            ("Create Room", self._on_create_room),
            ("Join Room", self._on_join_room),
            ("Cancel", self._on_close_popup)
        ]
        self.popup = Popup("Custom Rooms", "Select an option below to proceed:", popup_buttons)

    def _on_quick_match(self) -> None:
        """Triggers matchmaking and transitions to the waiting screen."""
        from ui.screens.waiting_screen import WaitingScreen
        waiting_screen = WaitingScreen(self.screen_manager, self.width, self.height)
        self.screen_manager.switch_to(waiting_screen)

    def _on_custom_room_click(self) -> None:
        """Opens the room option popup modal."""
        self.popup.show()

    def _on_create_room(self) -> None:
        """Simulates room creation and transitions to RoomScreen."""
        self.popup.hide()
        from ui.screens.room_screen import RoomScreen
        room_screen = RoomScreen(
            self.screen_manager, 
            self.width, 
            self.height, 
            room_id="9999", 
            is_creator=True,
            white_player=self.username
        )
        self.screen_manager.switch_to(room_screen)

    def _on_join_room(self) -> None:
        """Prompts for room ID in terminal and transitions to RoomScreen."""
        self.popup.hide()
        # Non-blocking simple console prompt for room joining in Phase 2
        print("\n=== JOIN ROOM ===")
        try:
            room_id = input("Enter Room ID: ").strip()
            if not room_id:
                room_id = "0000"
        except Exception:
            room_id = "0000"
            
        from ui.screens.room_screen import RoomScreen
        room_screen = RoomScreen(
            self.screen_manager, 
            self.width, 
            self.height, 
            room_id=room_id, 
            is_creator=False,
            white_player="Opponent",
            black_player=self.username
        )
        self.screen_manager.switch_to(room_screen)

    def _on_close_popup(self) -> None:
        """Closes the active popup modal."""
        self.popup.hide()

    def handle_click(self, x: int, y: int, is_right: bool = False) -> None:
        """Directs mouse clicks to buttons or the open popup."""
        if self.popup.visible:
            self.popup.handle_click(x, y)
            return
            
        for btn in self.buttons:
            btn.handle_click(x, y)

    def handle_mouse_move(self, x: int, y: int) -> None:
        """Directs cursor coordinates to components for hover effects."""
        if self.popup.visible:
            self.popup.update_hover(x, y)
            return
            
        for btn in self.buttons:
            btn.update_hover(x, y)

    def _draw_gradient_background(self, canvas: Img) -> None:
        """Fills canvas with a sleek dark radial-like vertical gradient."""
        # Base colors (dark grey/blue to dark grey/purple)
        c1 = np.array([25, 23, 21], dtype=np.float32)
        c2 = np.array([12, 10, 8], dtype=np.float32)
        
        for y in range(self.height):
            factor = y / self.height
            color = (1.0 - factor) * c1 + factor * c2
            canvas.img[y, :] = color.astype(np.uint8)

    def render(self, canvas: Img) -> None:
        """Renders the premium background, labels, buttons and popups."""
        if canvas.img is None:
            canvas.img = np.zeros((self.height, self.width, 3), dtype=np.uint8)
            
        self._draw_gradient_background(canvas)
        
        for lbl in self.labels:
            lbl.render(canvas)
            
        for btn in self.buttons:
            btn.render(canvas)
            
        self.popup.render(canvas)
