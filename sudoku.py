import random


def construct_puzzle_solution():
    # Loop until we're able to fill all 81 cells with numbers, while
    # satisfying the constraints above.
    while True:
        try:
            puzzle = [[0]*9 for _ in range(9)]  # start with blank puzzle
            rows = [set(range(1, 10)) for _ in range(9)]  # set of available
            columns = [set(range(1, 10)) for _ in range(9)]  # numbers for each
            squares = [set(range(1, 10)) for _ in range(9)]  # row, column and square
            for i in range(9):
                for j in range(9):
                    # pick a number for cell (i,j) from the set of remaining available numbers
                    choices = rows[i].intersection(columns[j]).intersection(squares[(i//3)*3 + j//3])
                    choice = random.choice(list(choices))

                    puzzle[i][j] = choice

                    rows[i].discard(choice)
                    columns[j].discard(choice)
                    squares[(i//3)*3 + j//3].discard(choice)

            # success! every cell is filled.
            return puzzle

        except IndexError:
            # if there is an IndexError, we have worked ourselves in a corner (we just start over)
            pass


def pluck(puzzle, n=0):

    """
    Answers the question: can the cell (i,j) in the puzzle "puz" contain the number
    in cell "c"? """
    def can_be_a(puz, i, j, c):
        v = puz[c//9][c % 9]
        if puz[i][j] == v:
            return True
        if puz[i][j] in range(1, 10):
            return False

        for m in range(9):  # test row, col, square
            # if not the cell itself, and the mth cell of the group contains the value v, then "no"
            if not (m == c//9 and j == c % 9) and puz[m][j] == v:
                return False
            if not (i == c//9 and m == c % 9) and puz[i][m] == v:
                return False
            if not ((i//3)*3 + m//3 == c//9 and (j/3)*3 + m % 3 == c % 9) \
                    and puz[(i//3)*3 + m//3][(j//3)*3 + m % 3] == v:
                return False

        return True

    cells = set(range(81))
    cells_left = cells.copy()
    while len(cells) > n and len(cells_left):
        cell = random.choice(list(cells_left))  # choose a cell from ones we haven't tried
        cells_left.discard(cell)  # record that we are trying this cell

        # row, col and square record whether another cell in those groups could also take
        # on the value we are trying to pluck. (If another cell can, then we can't use the
        # group to deduce this value.) If all three groups are True, then we cannot pluck
        # this cell and must try another one.
        row = col = square = False

        for i in range(9):
            if i != cell//9:
                if can_be_a(puzzle, i, cell % 9, cell):
                    row = True
            if i != cell % 9:
                if can_be_a(puzzle, cell//9, i, cell):
                    col = True
            if not (((cell//9)//3)*3 + i//3 == cell//9 and ((cell//9) % 3)*3 + i % 3 == cell % 9):
                if can_be_a(puzzle, ((cell//9)//3)*3 + i//3, ((cell//9) % 3)*3 + i % 3, cell):
                    square = True

        if row and col and square:
            continue  # could not pluck this cell, try again.
        else:
            # this is a pluckable cell!
            puzzle[cell//9][cell % 9] = 0  # 0 denotes a blank cell
            cells.discard(cell)  # remove from the set of visible cells (pluck it)
            # we don't need to reset "cellsleft" because if a cell was not pluckable
            # earlier, then it will still not be pluckable now (with less information
            # on the board).

    # This is the puzzle we found, in all its glory.
    # return puzzle, len(cells)
    return puzzle


def construct_sudoku(numbers_on_field):
    return pluck(construct_puzzle_solution(), numbers_on_field)


def sudoku_solved(field):
    for row in field:
        row = list(filter(lambda n: n != 0, row))
        if len(set(row)) != 9:
            return False
    for row in _transpose(field):
        row = list(filter(lambda n: n != 0, row))
        if len(set(row)) != 9:
            return False
    return True


def _transpose(s):
    new_s = [[0 for _ in range(9)] for _ in range(9)]
    for i, row in enumerate(s):
        for j, item in enumerate(row):
            new_s[j][i] = item
    return new_s