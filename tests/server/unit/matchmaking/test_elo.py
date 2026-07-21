from server.services.elo.elo_service import calculate_elo

def test_elo_white_wins():
    """Verify rating shifts when White (1500) beats Black (1500)."""
    new_w, new_b = calculate_elo(1500, 1500, 1.0)
    assert new_w > 1500
    assert new_b < 1500
    # Expected rating shift with K=32 on equal ratings is +-16
    assert new_w == 1516
    assert new_b == 1484

def test_elo_black_wins():
    """Verify rating shifts when Black (1600) beats White (1400)."""
    new_w, new_b = calculate_elo(1400, 1600, 0.0)
    # White was expected to lose (lower rated). Black wins.
    # Expected expected_w = 1 / (1 + 10^(200/400)) = 1 / (1 + 10^0.5) ~ 0.24
    # outcome = 0.0
    # White shift = 32 * (0 - 0.24) = -7.6 -> new_w = 1392
    # Black shift = 32 * (1 - 0.76) = +7.6 -> new_b = 1607
    assert new_w == 1392
    assert new_b == 1607

def test_elo_draw():
    """Verify rating shifts on draw outcome when ratings differ."""
    new_w, new_b = calculate_elo(1600, 1400, 0.5)
    # White was expected to win (higher rated). White loses rating, Black gains rating.
    assert new_w < 1600
    assert new_b > 1400
