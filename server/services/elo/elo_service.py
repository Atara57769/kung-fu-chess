def calculate_elo(rating_w: int, rating_b: int, outcome: float) -> tuple[int, int]:
    """Runs the standard ELO rating shift formula.
    
    outcome: 1.0 for White win, 0.0 for Black win, 0.5 for Draw.
    """
    k = 32
    expected_w = 1.0 / (1.0 + 10 ** ((rating_b - rating_w) / 400.0))
    expected_b = 1.0 - expected_w
    
    new_w = int(rating_w + k * (outcome - expected_w))
    new_b = int(rating_b + k * ((1.0 - outcome) - expected_b))
    return new_w, new_b
