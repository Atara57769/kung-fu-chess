class boardService:
    def __init__(self, board):
        self.board = board
        self.selected_piece = None
        self.clock = 0

    def click(self, x, y):
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
                self.selected_piece = (cell_y, cell_x)
            else:
                # Perform the move to the new cell and clear selection
                self.board.grid[cell_y][cell_x] = sel_token
                self.board.grid[sel_y][sel_x] = '.'
                self.selected_piece = None

    def wait(self, ms):
        self.clock += ms

    def print_board(self):
        """Prints the board in canonical space-separated format."""
        for row in self.board.grid:
            print(" ".join(row))
