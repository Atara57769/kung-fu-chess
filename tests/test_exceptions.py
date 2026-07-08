from exceptions import UnknownTokenError, RowWidthMismatchError

def test_exceptions():
    exc1 = UnknownTokenError("test unknown")
    assert isinstance(exc1, ValueError)
    
    exc2 = RowWidthMismatchError("test mismatch")
    assert isinstance(exc2, ValueError)
