from PyQt5 import QtWidgets
from PyQt5.QtCore import Qt, QSize
from PyQt5.QtGui import QFontDatabase, QColor, QBrush
from collections import OrderedDict

monospace = QFontDatabase.systemFont(QFontDatabase.FixedFont)
highlight = QBrush(QColor(255, 153, 51))
default = QBrush(QColor(255, 255, 255))

def _chunks(l, n):
    for i in xrange(0, len(l), n):
        yield l[i:i + n]

def _makewidget(val):
    out = QtWidgets.QTableWidgetItem(str(val))
    out.setFlags(Qt.ItemIsEnabled)
    out.setFont(monospace)
    return out


class Window(QtWidgets.QWidget):
    _display_modes = ['binary', 'decimal', 'hex', 'ascii']
    registers = OrderedDict()
    display_mode = 'hex'

    def __init__(self, registers=None):
        super(Window, self).__init__()

        self.setLayout(QtWidgets.QVBoxLayout())
        self._layout = self.layout()

        self._picker = QtWidgets.QComboBox()
        for mode in self._display_modes:
            self._picker.addItem(mode)
        self._picker.setCurrentIndex(2)
        self._layout.addWidget(self._picker)
        self._picker.currentIndexChanged.connect(self.change_display_mode)

        self._table = QtWidgets.QTableWidget()
        self._table.setColumnCount(2)
        self._table.setHorizontalHeaderLabels(['Register', 'Value'])
        self._table.horizontalHeader().setStretchLastSection(True)
        self._table.verticalHeader().setVisible(False)
        self._layout.addWidget(self._table)

        self.setObjectName('Register_Window')

        self.should_clean = False

        if registers is not None:
            self.update_registers(registers)

    def update_registers(self, registers):
        """ Takes a dict of registers - 'name' : (value, width)"""
        self._table.setRowCount(len(registers))
        for register in registers:
            self.update_single_register(register, registers[register][0], registers[register][1])
        self.resize(QSize(self._layout.sizeHint().width(), self._table.viewportSizeHint().height() + self._picker.sizeHint().height() + 30 ))

    def update_single_register(self, name, value, width=32):
        if(self.should_clean):
            for reg in self.registers:
                self.registers[reg].dirty = False
        if name not in self.registers.keys():
            self.registers[name] = Register(name, len(self.registers.keys()), width, value)
            self._update_table_entry(name)
        else:
            if self.registers[name].value != value:
                self.registers[name].setval(value)
                self._update_table_entry(name)
        self.should_clean = False

    def _update_table_entry(self, name):
        self._table.setItem(self.registers[name].index, 0, _makewidget(self.registers[name].name))
        self._table.setItem(self.registers[name].index, 1, _makewidget(self.registers[name][self.display_mode]))

    def change_display_mode(self, mode):
        if type(mode) is int:
            if (mode < 0) or (mode >= len(self._display_modes)):
                print("Mode index out of range")
                return
            mode = self._display_modes[mode]
        if mode not in self._display_modes:
            print(str(mode) + " is not a valid display mode! Valid modes are: " + str(self._display_modes))
            return
        self.display_mode = mode
        for name in self.registers.keys():
            self._update_table_entry(name)
        self.should_clean = False
        print("Disabling Cleaning")
        self.highlight_dirty()

    def highlight_dirty(self):
        for reg in self.registers:
            reg = self.registers[reg]
            if(reg.dirty):
                t_item = self._table.item(reg.index, 1)
                if t_item is not None:
                    print("Highlighting " + reg.name)
                    t_item.setForeground(highlight)
                if(self.should_clean):
                    print("Cleaning " + reg.name)
                    reg.dirty = False
            else:
                t_item = self._table.item(reg.index, 1)
                if t_item is not None:
                    print("Restoring to default color: " + reg.name)
                    t_item.setForeground(default)
        print("Will Clean Next Time")
        self.should_clean = True

class Register():
    def __init__(self, name, index, width, value=0):
        self.name = name
        self.bitwidth = width
        self.value = value
        self.index = index
        self.dirty = False

    def __getitem__(self, encoding):
        if encoding == 'hex':
            return self.hex
        if encoding == 'decimal':
            return self.decimal
        if encoding == 'binary':
            return self.binary
        if encoding == 'ascii':
            return self.ascii
        return None

    def __repr__(self):
        return self.name + " (" + str(self.bitwidth) + "b): " + self.hex

    @property
    def binary(self):
        base = bin(self.value)[2:]
        out = '0' * (self.bitwidth - len(base)) + base
        return ' '.join([chunk for chunk in _chunks(out, 8)])

    @property
    def decimal(self):
        return self.value

    @property
    def hex(self):
        base = hex(self.value).replace("L","")
        out = "0x" + "0"*((self.bitwidth / 4) - len(base.split('0x')[1])) + base.split('0x')[1]
        return out

    @property
    def ascii(self):
        hexstr = self.hex[2:]
        return "".join([('.' if (int(c, 16) < 32 or int(c, 16) >= 127) else chr(int(c, 16))) for c in _chunks(hexstr, 2)])

    def setval(self, newval):
        self.value = int(newval)
        self.dirty = True