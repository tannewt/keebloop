import board
import keypad

class Sofle:
    # Left side
    LED = board.TX
    DATA = board.RX
    SDA = board.D2
    SCL = board.D3

    ROW0 = board.D5
    ROW1 = board.D6
    ROW2 = board.D7
    ROW3 = board.D8
    ROW4 = board.D9

    # Right side
    ENCA = board.A3
    ENCB = board.A2
    COL0 = board.A1
    COL1 = board.A0
    COL2 = board.SCK
    COL3 = board.MISO
    COL4 = board.MOSI
    COL5 = board.D10
    SW25A = board.D10

    def prefixed_pins(self, prefix):
        names = []
        for name in dir(self):
            if name.startswith(prefix):
                names.append(name)
        names.sort()
        return [getattr(self, n) for n in names]

    def __init__(self, flipped):
        self.columns = self.prefixed_pins("COL")
        self.rows = self.prefixed_pins("ROW")
        self.flipped = flipped

        self.keys = keypad.KeyMatrix(
            row_pins=self.rows,
            column_pins=self.columns,
            columns_to_anodes=True,
        )

    def get(self):
        key_event = self.keys.events.get()
        if key_event is None:
            return None

        row = key_event.key_number // len(self.columns)
        col = key_event.key_number % len(self.columns)
        key_number = key_event.key_number
        if self.flipped:
            col = len(self.columns) - col - 1
            key_number = len(self.columns) * (row + 1) + len(self.columns) * row + col
        else:
            key_number = (2 * len(self.columns) * row) + col

        return (key_number, key_event)
