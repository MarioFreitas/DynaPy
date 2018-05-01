import sys

import numpy as np
from DynaPy import PltCanvas, get_text
from GUI.excitationGeneratorGUI import Ui_MainWindow
from PyQt5.QtCore import *
from PyQt5.QtGui import *
from PyQt5.QtWidgets import *
from matplotlib.backends.backend_qt4agg import NavigationToolbar2QT as NavigationToolbar


class MainWindow(QMainWindow, Ui_MainWindow):
    nameSignal = pyqtSignal(str)

    def __init__(self, parent=None, fileName=''):
        super(MainWindow, self).__init__(parent)
        self.setupUi(self)
        self.setWindowIcon(QIcon('icon_64.ico'))

        # Excitation Canvas
        self.widget.excitationCanvas = PltCanvas()
        self.widget.mpl_toolbar = NavigationToolbar(self.widget.excitationCanvas, self)
        self.widget.gridLabel = QLabel('Show Grid', self)
        self.widget.gridChkBox = QCheckBox(self)
        self.widget.gridChkBox.stateChanged.connect(self.excitation_grid_toggle)

        self.widget.gridLayout = QGridLayout()
        self.widget.gridLayout.addWidget(self.widget.excitationCanvas, 1, 1, 1, 3)
        self.widget.gridLayout.addWidget(self.widget.gridLabel, 2, 1)
        self.widget.gridLayout.addWidget(self.widget.gridChkBox, 2, 2)
        self.widget.gridLayout.addWidget(self.widget.mpl_toolbar, 2, 3)

        self.widget.setLayout(self.widget.gridLayout)

        self.show()

        if fileName == '':
            self.fileName = None
        else:
            self.open_file(fileName=fileName)

        # Connect Buttons
        self.comboBox.currentIndexChanged.connect(self.acceleration_unit_change)
        self.pushButton.clicked.connect(self.add_row)
        self.pushButton_2.clicked.connect(self.remove_row)
        self.pushButton_3.clicked.connect(self.plot_excitation)

        # Connect Actions
        self.actionNew.triggered.connect(self.new_file)
        self.actionOpen.triggered.connect(self.open_file)
        self.actionSave.triggered.connect(self.save_file)
        self.actionSave_as.triggered.connect(self.save_file_as)
        self.actionQuit.triggered.connect(self.close)
        self.actionAbout.triggered.connect(self.about)

    def closeEvent(self, event):
        quit_msg = "Are you sure you want to exit the program?"
        reply = QMessageBox.question(self, 'Confirm Exit',
                                     quit_msg, QMessageBox.Yes, QMessageBox.No)

        if reply == QMessageBox.Yes:
            event.accept()
            self.nameSignal.emit(str(self.fileName))
        else:
            event.ignore()

    # Menu Methods
    def new_file(self, triggered=False, flag=True):
        if flag:
            quit_msg = "This operation will erase all unsaved data. Are you sure you want to open a new file?"
            reply = QMessageBox.question(self, 'Confirm New File',
                                         quit_msg, QMessageBox.Yes, QMessageBox.No)

            if reply == QMessageBox.No:
                return

        self.tableWidget.clear()
        self.acceleration_unit_change()
        self.widget.excitationCanvas.plot_excitation([], [])
        for i in range(self.tableWidget.rowCount() - 1):
            self.tableWidget.removeRow(0)

    def open_file(self, triggered=False, fileName=None):
        if fileName is not None:
            self.fileName = fileName
        else:
            fileName = QFileDialog.getOpenFileName(self, 'Open File', './save/Excitations',
                                                   filter="Text File (*.txt)")[0]
            if fileName == '':
                return None
            self.new_file(flag=False)
            self.fileName = fileName
        self.setWindowTitle('Excitation Generator - [{}]'.format(self.fileName))

        try:
            with open(self.fileName, 'r', encoding='utf-8') as file:
                unit = file.readline()
                if unit == 'unit: g\n':
                    self.comboBox.setCurrentIndex(0)
                elif unit == 'unit: m/s2\n':
                    self.comboBox.setCurrentIndex(1)

                rows = int(file.readline())
                self.cells = []
                for i in range(rows):
                    cell_row = []
                    row = file.readline()
                    row = row.split(', ')
                    t = row[0]
                    a = row[1].strip('\n')
                    x = QTableWidgetItem()

                    y = QTableWidgetItem()
                    x.setText(t)
                    y.setText(a)
                    self.cells.append([x, y])
                    self.tableWidget.setItem(i, 0, x)
                    self.tableWidget.setItem(i, 1, y)
                    self.tableWidget.insertRow(i + 1)

            self.tableWidget.removeRow(i + 1)
            self.plot_excitation()
        except FileNotFoundError:
            self.fileName = None
            self.setWindowTitle('Excitation Generator')
            return

    def save_file(self):
        if self.fileName is None:
            self.save_file_as()
        else:
            self.check_table()
            if get_text(self.comboBox) == 'g':
                unit = 'unit: g\n'
            elif get_text(self.comboBox) == 'm/s²':
                unit = 'unit: m/s2\n'

            rows = '{}\n'.format(self.tableWidget.rowCount())

            with open(self.fileName, 'w') as file:
                file.write(unit)
                file.write(rows)
                for i in range(self.tableWidget.rowCount()):
                    file.write('{}, '.format(get_text(self.tableWidget.item(i, 0))))
                    file.write('{}\n'.format(get_text(self.tableWidget.item(i, 1))))

    def save_file_as(self):
        """ Brings a file save dialog box, saves the file directory to self.fileName and calls self.save_file()

                :return: None
                """
        self.fileName = QFileDialog.getSaveFileName(self, 'Save as', './save/Excitations',
                                                    filter="Text File (*.txt)")[0]
        if self.fileName == '':
            self.fileName = None
            return
        self.setWindowTitle('Excitation Generator - [{}]'.format(self.fileName))
        self.save_file()

    def about(self):
        pass

    # Table Widget Methods
    def acceleration_unit_change(self):
        if get_text(self.comboBox) == 'g':
            self.tableWidget.setHorizontalHeaderLabels(['Time (s)', 'Acceleration (g)'])
        elif get_text(self.comboBox) == 'm/s²':
            self.tableWidget.setHorizontalHeaderLabels(['Time (s)', 'Acceleration (m/s²)'])

    def add_row(self):
        i = self.tableWidget.rowCount()
        self.tableWidget.insertRow(i)

    def remove_row(self):
        i = self.tableWidget.currentRow()
        self.tableWidget.removeRow(i)

    def check_table(self):
        rows = self.tableWidget.rowCount()
        columns = self.tableWidget.columnCount()

        for i in range(rows):
            for j in range(columns):
                self.tableWidget.setCurrentCell(i, j)
                flag = self.check_cell(i, j)
                if flag:
                    return True

    def check_cell(self, row, column):
        try:
            float(get_text(self.tableWidget.item(row, column)))
        except Exception:
            error01_title = "Error 01"
            error01_msg = "Table item has non-float value."
            QMessageBox.warning(self, error01_title, error01_msg, QMessageBox.Ok)
            return True
        else:
            return False

    # Excitation Canvas Method
    def excitation_grid_toggle(self):
        """ Toggles plot grid on and off

        :return: None
        """
        self.widget.excitationCanvas.axes.grid(self.widget.gridChkBox.isChecked())
        self.widget.excitationCanvas.draw()

    def plot_excitation(self):
        flag = self.check_table()
        if flag:
            return
        t = []
        a = []
        for i in range(self.tableWidget.rowCount()):
            x = float(get_text(self.tableWidget.item(i, 0)))
            y = float(get_text(self.tableWidget.item(i, 1)))
            t.append(x)
            a.append(y)

        t = np.array(t)
        a = np.array(a)

        if get_text(self.comboBox) == 'g':
            self.widget.excitationCanvas.plot_excitation(t, a, 'g')
        elif get_text(self.comboBox) == 'm/s²':
            self.widget.excitationCanvas.plot_excitation(t, a)


if __name__ == '__main__':
    app = QApplication(sys.argv)
    gui = MainWindow()
    gui.show()
    sys.exit(app.exec_())
