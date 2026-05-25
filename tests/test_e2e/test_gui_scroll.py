import pytest
import customtkinter as ctk
from src.ui.gui.screens.splitter import SplitterGUI
from src.ui.gui.screens.clipper import ClipperGUI
from src.ui.gui.screens.merger import MergerGUI
from unittest.mock import MagicMock

class MockApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.shared_state = {"video_path": "", "export_path": ""}

@pytest.fixture
def mock_app():
    return MockApp()

def test_splitter_scroll_methods(mock_app):
    screen = SplitterGUI(mock_app, mock_app.shared_state)
    assert hasattr(screen, "_bind_scroll_to_widgets")
    assert hasattr(screen, "_on_mouse_wheel")

def test_clipper_scroll_methods(mock_app):
    screen = ClipperGUI(mock_app, mock_app.shared_state)
    assert hasattr(screen, "_bind_scroll_to_widgets")
    assert hasattr(screen, "_on_mouse_wheel")

def test_merger_scroll_methods(mock_app):
    screen = MergerGUI(mock_app, mock_app.shared_state)
    assert hasattr(screen, "_bind_scroll_to_widgets")
    assert hasattr(screen, "_on_mouse_wheel")

def test_mouse_wheel_redirection_splitter(mock_app):
    screen = SplitterGUI(mock_app, mock_app.shared_state)
    
    # Mock the internal canvas
    mock_canvas = MagicMock()
    screen.queue_frame._parent_canvas = mock_canvas
    
    # Simulate a mouse wheel event
    class MockEvent:
        def __init__(self, delta, num=0):
            self.delta = delta
            self.num = num
            
    # Windows/macOS style
    screen._on_mouse_wheel(MockEvent(-120))
    mock_canvas.yview_scroll.assert_called_with(1, "units")
    
    # Linux style (Button-4)
    screen._on_mouse_wheel(MockEvent(0, num=4))
    mock_canvas.yview_scroll.assert_called_with(-1, "units")

def test_mouse_wheel_redirection_clipper(mock_app):
    screen = ClipperGUI(mock_app, mock_app.shared_state)
    mock_canvas = MagicMock()
    screen.queue_frame._parent_canvas = mock_canvas
    
    class MockEvent:
        def __init__(self, delta, num=0):
            self.delta = delta
            self.num = num
            
    screen._on_mouse_wheel(MockEvent(240))
    mock_canvas.yview_scroll.assert_called_with(-2, "units")

def test_mouse_wheel_redirection_merger(mock_app):
    screen = MergerGUI(mock_app, mock_app.shared_state)
    mock_canvas = MagicMock()
    screen.queue_frame._parent_canvas = mock_canvas
    
    class MockEvent:
        def __init__(self, delta, num=0):
            self.delta = delta
            self.num = num
            
    screen._on_mouse_wheel(MockEvent(0, num=5))
    mock_canvas.yview_scroll.assert_called_with(1, "units")
