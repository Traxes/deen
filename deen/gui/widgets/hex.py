import codecs
import string

from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import (QBrush, QColor)
from PyQt5.QtWidgets import (QTableWidget, QTableWidgetItem, QHeaderView)


class HexViewWidget(QTableWidget):
    bytesChanged = pyqtSignal()

    def __init__(self, content=None, max_bytes_per_line=16, width=1,
                 read_only=False, parent=None):
        super(HexViewWidget, self).__init__(parent)
        self.parent = parent
        self._max_bytes_per_line = max_bytes_per_line
        self._bytes_per_line = max_bytes_per_line
        self._width = width
        self._read_only = read_only
        if content:
            self.content = content
        else:
            self.content = bytearray()
        self.horizontalHeader().setStretchLastSection(True)

    def _reconstruct_table(self):
        try:
            self.itemChanged.disconnect(self._item_changed)
        except:
            pass
        self.clear()
        rows = []
        for i in range(0, len(self._data), self._bytes_per_line):
            rows.append(self._data[i:i+self._bytes_per_line])
        self.setRowCount(len(rows))
        cols = self._bytes_per_line // self._width + 1  # ascii
        self.setColumnCount(cols)
        self._process_headers()
        for y, row in enumerate(rows):
            self._process_row(y, row)
        self.resizeColumnsToContents()
        self.itemChanged.connect(self._item_changed)

    def _process_headers(self):
        cols = self.columnCount()
        for i in range(cols):
            self.horizontalHeader().setSectionResizeMode(i, QHeaderView.ResizeToContents)
        header_labels = []
        for i in range(0, self._bytes_per_line, self._width):
            header_labels.append('{:X}'.format(i))
        header_labels.append('ASCII')
        row_labels = []
        for i in range(0, len(self._data), self._bytes_per_line):
            row_labels.append('{:X}'.format(i))
        self.setHorizontalHeaderLabels(header_labels)
        self.setVerticalHeaderLabels(row_labels)

    def _process_row(self, y, row):
        cols = self.columnCount()
        for x, i in enumerate(range(0, len(row), self._width)):
            block = row[i:i+self._width]
            item = QTableWidgetItem(codecs.encode(block, 'hex').decode())
            item.setBackground(QBrush(QColor('lightgray')))
            item.setForeground(QBrush(QColor('black')))
            item.setTextAlignment(Qt.AlignHCenter | Qt.AlignVCenter)
            item.setData(Qt.UserRole, block)  # store original data
            if self._read_only:
                item.setFlags(Qt.ItemIsSelectable | Qt.ItemIsEnabled)
            else:
                item.setFlags(Qt.ItemIsSelectable | Qt.ItemIsEnabled | Qt.ItemIsEditable)
            self.setItem(y, x, item)

        # process remaining, unfilled cells
        for j in range(x+1, cols):
            item = QTableWidgetItem()
            item.setBackground(QBrush(QColor('white')))
            item.setFlags(Qt.NoItemFlags)
            item.setTextAlignment(Qt.AlignHCenter)
            self.setItem(y, j, item)

        text = self._bytes_to_ascii(row)
        item = QTableWidgetItem(text)
        item.setData(Qt.UserRole, row)  # store original data
        item.setTextAlignment(Qt.AlignLeft| Qt.AlignVCenter)
        item.setBackground(QBrush(QColor('lightblue')))
        item.setForeground(QBrush(QColor('black')))
        if self._read_only:
            item.setFlags(Qt.ItemIsSelectable | Qt.ItemIsEnabled)
        else:
            item.setFlags(Qt.ItemIsSelectable | Qt.ItemIsEnabled | Qt.ItemIsEditable)
        self.setItem(y, cols - 1, item)

    def _bytes_to_ascii(self, data):
        if not isinstance(data, (bytes, bytearray)):
            data = codecs.encode(data, 'utf8')
        allowed = (set(string.printable.encode()) - set(string.whitespace.encode())) | {b' '}
        allowed = [ord(x) if isinstance(x, str) else x for x in allowed]
        return ''.join([chr(c) if c in allowed else '.' for c in data])

    def _item_changed(self, item):
        def reset_hex_text(orig_data):
            text = codecs.encode(orig_data, 'hex').decode()
            item.setText(text)
        col = item.column()
        row = item.row()
        text = item.text()
        orig_data = item.data(Qt.UserRole)
        offset = row * self._bytes_per_line
        if col != self.columnCount() - 1:  # hex part
            text = text.strip()
            fmt = '{{:>0{}}}'.format(self._width * 2)
            text = fmt.format(text)
            if len(text) != self._width * 2:
                reset_hex_text(orig_data)
                return
            offset += col * self._width
            try:
                value = codecs.decode(text, 'hex')
            except ValueError:
                reset_hex_text(orig_data)
                return
        else:  # ascii part
            if len(orig_data) != len(text):
                text = self._bytes_to_ascii(orig_data)
                item.setText(text)
                return
            value = bytearray()
            for a, b in zip(orig_data, text.encode()):
                if b == b'.'[0]:
                    value.append(a)
                else:
                    value.append(b)
        self._data[offset:offset+len(value)] = value
        self.bytesChanged.emit()
        self._reconstruct_table()

    @property
    def width(self):
        return self._width

    @width.setter
    def width(self, val):
        if val not in (1, 2, 2**2, 2**3, 2**4, 2**5, 2**6):
            raise ValueError('Width not power of 2')
        self._width = val
        self._reconstruct_table()

    @property
    def content(self):
        return self._data

    @content.setter
    def content(self, content):
        assert isinstance(content, bytearray), TypeError('bytearray required. Got ' + type(content).__name__)
        self._data = content
        if self._data:
            self._bytes_per_line = min(len(self._data), self._max_bytes_per_line)
        self._reconstruct_table()

    @property
    def bytes_per_line(self):
        return self._bytes_per_line

    @bytes_per_line.setter
    def bytes_per_line(self, val):
        self._max_bytes_per_line = val
        self._bytes_per_line = min(self._max_bytes_per_line, self._bytes_per_line)
        self._reconstruct_table()

    def to_bytes(self):
        return self.content
