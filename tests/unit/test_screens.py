import pytest
from ui.screens.screen_manager import ScreenManager
from ui.screens.base_screen import Screen
from ui.components.button import Button
from ui.components.label import Label

class DummyScreen(Screen):
    def __init__(self) -> None:
        self.clicked = False
        self.clicked_coords = (0, 0)
        self.updated = False
        self.dt_value = 0.0

    def handle_click(self, x: int, y: int, is_right: bool = False) -> None:
        self.clicked = True
        self.clicked_coords = (x, y)

    def update(self, dt: float) -> None:
        self.updated = True
        self.dt_value = dt

def test_screen_manager_delegation():
    """Verify ScreenManager correctly routes click and update events."""
    sm = ScreenManager()
    screen = DummyScreen()
    sm.switch_to(screen)
    
    assert sm.active_screen is screen
    
    sm.handle_click(10, 20)
    assert screen.clicked is True
    assert screen.clicked_coords == (10, 20)
    
    sm.update(0.05)
    assert screen.updated is True
    assert screen.dt_value == 0.05

def test_button_clicks():
    """Verify Button invokes callback only when clicked inside boundaries."""
    clicked = False
    def on_click():
        nonlocal clicked
        clicked = True

    btn = Button(x=10, y=10, w=100, h=40, text="Test", callback=on_click)
    
    # Click outside
    res = btn.handle_click(5, 5)
    assert res is False
    assert clicked is False
    
    # Click inside
    res = btn.handle_click(15, 15)
    assert res is True
    assert clicked is True

def test_button_hover_updates():
    """Verify Button correctly updates hover state."""
    btn = Button(x=10, y=10, w=100, h=40, text="Test", callback=lambda: None)
    
    btn.update_hover(50, 30)
    assert btn.is_hovered is True
    
    btn.update_hover(150, 30)
    assert btn.is_hovered is False
