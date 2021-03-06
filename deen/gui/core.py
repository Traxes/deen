import logging

from PyQt5.QtWidgets import QMainWindow, QApplication, QMessageBox, QFileDialog, QBoxLayout, QErrorMessage

import deen.constants
from deen.gui.widgets.log import DeenLogger, DeenStatusConsole
from deen.gui.widgets.ui_deenmainwindow import Ui_MainWindow
from deen.gui.encoder import DeenEncoderWidget

LOGGER = logging.getLogger(__name__)


class DeenGui(QMainWindow):
    """The main window class that is the core of
    the Deen GUI. If is basically just the main
    window with a central element that includes
    one or more DeenEncoderWidget."""
    def __init__(self, parent=None, plugins=None):
        super(DeenGui, self).__init__(parent)
        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)
        self.plugins = plugins
        self.widgets = []
        self.ui.actionLoad_from_file.triggered.connect(self.load_from_file)
        self.ui.actionQuit.triggered.connect(QApplication.quit)
        self.ui.actionAbout.triggered.connect(self.show_about)
        self.ui.actionStatus_console.triggered.connect(self.show_status_console)
        self.ui.actionTop_to_bottom.triggered.connect(self.set_widget_direction_toptobottom)
        self.ui.actionLeft_to_right.triggered.connect(self.set_widget_direction_lefttoright)
        self.widgets.append(DeenEncoderWidget(self))
        for widget in self.widgets:
            self.ui.encoder_widget_layout.addWidget(widget)
        self.load_from_file_dialog = QFileDialog(self)
        self.setWindowTitle('deen')
        self.log = DeenLogger(self)
        # Start Deen GUI maximized with focus on the text field
        self.showMaximized()
        self.widgets[0].text_field.setFocus(True)
        self.show()

    def set_root_content(self, data):
        if data:
            if isinstance(data, (str, bytes)):
                data = bytearray(data)
            self.widgets[0].content = data

    def set_widget_direction_toptobottom(self):
        self.ui.encoder_widget_layout.setDirection(QBoxLayout.TopToBottom)

    def set_widget_direction_lefttoright(self):
        self.ui.encoder_widget_layout.setDirection(QBoxLayout.LeftToRight)

    def show_about(self):
        about = QMessageBox(self)
        about.setWindowTitle('About')
        about.setText(deen.constants.about_text)
        about.resize(100, 75)
        about.show()

    def show_status_console(self):
        status = DeenStatusConsole(self)
        status.setWindowTitle('Status Console')
        status.resize(600, 400)
        status.console.show()
        status.show()

    def show_error_msg(self, error_msg, parent=None):
        """Generic message box for displaying any
        kind of error message from GUI elements."""
        widget = parent or self
        dialog = QMessageBox(widget)
        dialog.setIcon(QMessageBox.Critical)
        dialog.setWindowTitle('Error')
        dialog.setText(error_msg)
        dialog.show()

    def load_from_file(self, file_name=None):
        if file_name:
            name = file_name
        else:
            name = self.load_from_file_dialog.getOpenFileName(
                        self.load_from_file_dialog, 'Load from File')
        if not name or not name[0]:
            return
        if isinstance(name, tuple):
            name = name[0]
        with open(name, 'rb') as file:
            content = file.read()
        if content:
            self.widgets[0].clear_content()
            self.widgets[0].content =  bytearray(content)
            try:
                content = content.decode('utf8')
            except UnicodeDecodeError:
                content = content.decode('utf8', errors='replace')
                self.widgets[0].text_field.setReadOnly(True)
                LOGGER.warning('Failed to decode file content, root widget will be read only')
            self.widgets[0].text_field.setPlainText(content)
        self.widgets[0].hex_field.setHidden(True)
        self.widgets[0].text_field.setHidden(False)
