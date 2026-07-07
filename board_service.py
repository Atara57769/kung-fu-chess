from models.pieces import get_piece


class boardService:
    def __init__(self, board):
        self.board = board
        self.selected_piece = None
        self.clock = 0
        self.pending_moves = []

    def _apply_completed_moves(self):
        self.pending_moves.sort(key=lambda m: m['arrival'])
        remaining = []
        for m in self.pending_moves:
            if m['arrival'] <= self.clock:
                from_y, from_x = m['from']
                to_y, to_x = m['to']
                token = m['token']
                # Apply the move on the grid
                self.board.grid[to_y][to_x] = token
                if self.board.grid[from_y][from_x] == token:
                    self.board.grid[from_y][from_x] = '.'
            else:
                remaining.append(m)
        self.pending_moves = remaining

    def click(self, x, y):
        self._apply_completed_moves()
        if self.pending_moves:
            return

        # Determine board dimensions
        H = len(self.board.grid)
        W = self.board.width
        
        # Convert to cell coordinates
        cell_x = x // 100
        cell_y = y // 100
        
        # Ignore clicks outside the board boundaries
        if not (0 <= cell_x < W and 0 <= cell_y < H):
            return
            
        token = self.board.grid[cell_y][cell_x]
        
        # Ignore clicks on pieces that are currently in transit
        if any(m['from'] == (cell_y, cell_x) for m in self.pending_moves):
            return

        if self.selected_piece is None:
            # If no piece is selected, clicking a piece selects it
            if token != '.':
                self.selected_piece = (cell_y, cell_x)
        else:
            # A piece is already selected
            sel_y, sel_x = self.selected_piece
            sel_token = self.board.grid[sel_y][sel_x]
            sel_color = sel_token[0]
            
            if token != '.' and token[0] == sel_color:
                # Replace selection with another friendly piece
                if any(m['from'] == (cell_y, cell_x) for m in self.pending_moves):
                    return
                self.selected_piece = (cell_y, cell_x)
            else:
                # Check if the selected piece is already in transit
                if any(m['from'] == (sel_y, sel_x) for m in self.pending_moves):
                    return
                
                # Check if the destination is targeted by another pending move
                if any(m['to'] == (cell_y, cell_x) for m in self.pending_moves):
                    return

                # Validate the move according to the piece type
                piece = get_piece(sel_token)
                if piece is None or piece.is_legal_move(self.board, sel_y, sel_x, cell_y, cell_x):
                    # Calculate travel duration
                    duration = 1000
                    if piece is not None:
                        duration = piece.get_travel_duration(sel_y, sel_x, cell_y, cell_x)
                    
                    # Schedule the move
                    self.pending_moves.append({
                        'from': (sel_y, sel_x),
                        'to': (cell_y, cell_x),
                        'token': sel_token,
                        'arrival': self.clock + duration
                    })
                    self.selected_piece = None
                else:
                    # Illegal move is ignored (keep selection)
                    pass

    def wait(self, ms):
        self.clock += ms
        self._apply_completed_moves()

    def print_board(self):
        """Prints the board in canonical space-separated format."""
        self._apply_completed_moves()
        for row in self.board.grid:
            print(" ".join(row))
