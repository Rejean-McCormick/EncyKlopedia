"""Responsive shell stays on-screen; no template inference is performed."""
from spek.studio_gui import initial_window_size


def test_sizes_stay_below_screen_on_typical_desktops():
    for sw, sh in [(1024, 768), (1069, 850), (1280, 720), (1920, 1080)]:
        w, h = initial_window_size(sw, sh)
        assert w < sw, (sw, sh, w, h)
        assert h < sh, (sw, sh, w, h)
        assert w <= 1270 and h <= 820


def test_regular_screen_uses_original_cap():
    assert initial_window_size(1920, 1080) == (1270, 820)


def test_small_windows_remain_reasonable():
    assert initial_window_size(1024, 768) == (976, 678)
