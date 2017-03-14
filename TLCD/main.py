"""
Script name: TLCD Analyser GUI
Author: Mario Raul Freitas

This script contains the Graphical User Interface code for the TLCD Analyser software.
It utilises PyQt4 as the GUI framework.
This is the main script of the project and will be used to generate the .exe file for
distribution.
"""
from PyQt4.QtCore import *
from PyQt4.QtGui import *
from matplotlib.backends.backend_qt4agg import NavigationToolbar2QT as NavigationToolbar
import numpy as np
import sys
from DynaPy.TLCD.GUI.DpInputData import InputData
from DynaPy.TLCD.GUI.DpConfigurations import Configurations
from DynaPy.TLCD.GUI.DpOutputData import OutputData
from DynaPy.TLCD.GUI.DpStory import Story
from DynaPy.TLCD.GUI.DpTLCD import TLCD
from DynaPy.TLCD.GUI.DpExcitation import Excitation
from DynaPy.TLCD.GUI.DpPltCanvas import PltCanvas
from DynaPy.TLCD.GUI.DpStructureCanvas import StructureCanvas
from DynaPy.TLCD.GUI.DpTLCDCanvas import TLCDCanvas
from DynaPy.TLCD.GUI.DpAnimationCanvas import AnimationCanvas
from DynaPy.lib import get_text
from DynaPy.DynaSolver import *

inputData = InputData()
inputData.configurations = Configurations()

outputData = None

debugOption = False
np.set_printoptions(linewidth=100, precision=2)


class RunSimulationThread(QThread):
    mySignal = pyqtSignal(OutputData)

    def __init__(self, inputData_, parent=None):
        super(RunSimulationThread, self).__init__(parent)
        self.inputData = inputData_

    def run(self):
        # Assemble matrices
        mass = assemble_mass_matrix(self.inputData.stories, self.inputData.tlcd)
        damping = assemble_damping_matrix(self.inputData.stories, self.inputData.tlcd)
        stiffness = assemble_stiffness_matrix(self.inputData.stories, self.inputData.tlcd)
        force = assemble_force_matrix(self.inputData.excitation, mass, self.inputData.configurations)

        outputData = OutputData(mass, damping, stiffness, force, self.inputData.configurations)
        self.mySignal.emit(outputData)


class RunSetOfSimulationsThread(QThread):
    mySignal = pyqtSignal(list)
    percentageSignal = pyqtSignal(float)

    def __init__(self, inputData_, relativeFrequencies, parent=None):
        super(RunSetOfSimulationsThread, self).__init__(parent)
        self.inputData = inputData_
        self.relativeFrequencies = relativeFrequencies

    def run(self):
        dmfList = []
        totalIter = len(self.relativeFrequencies)
        for i, j in zip(self.relativeFrequencies, range(len(self.relativeFrequencies))):
            dmfList.append(self.simulation(self.inputData, i))
            percentageDone = (j+1)/totalIter*100
            self.percentageSignal.emit(percentageDone)
        self.mySignal.emit(dmfList)

    def simulation(self, inputData_,  relativeFrequency):
        inputData_.excitation.frequencyInput = relativeFrequency
        inputData_.excitation.relativeFrequency = True
        inputData_.excitation.calc_frequency()

        mass = assemble_mass_matrix(inputData_.stories, inputData_.tlcd)
        damping = assemble_damping_matrix(inputData_.stories, inputData_.tlcd)
        stiffness = assemble_stiffness_matrix(inputData_.stories, inputData_.tlcd)
        force = assemble_force_matrix(inputData_.excitation, mass, inputData_.configurations)

        outputData = OutputData(mass, damping, stiffness, force, inputData_.configurations)
        return outputData.DMF


class MainWindow(QMainWindow):
    """
    Main window of the application. Contains all global parameters of the GUI application.
    """
    def __init__(self, parent=None):
        """
        Initializes the main window and sets up the entire GUI application.
        :param parent: No parent
        :return: None
        """
        # Initiate parent class
        super(MainWindow, self).__init__(parent)

        # Set up MainWindow's child widgets
        self.mainWidget = MainWidget(self)
        self.setCentralWidget(self.mainWidget)

        # MainWindow Geometry, Title and Icon
        self.setGeometry(100, 100, 800, 600)
        self.setWindowTitle('Dynapy TLCD Analyser')
        self.setWindowIcon(QIcon(None))

        # Declare save file
        self.fileName = None

        # File menu actions
        self.new_file_action()
        self.open_file_action()
        self.save_file_action()
        self.save_file_as_action()
        self.export_report_action()
        self.export_animation_action()
        self.quit_action()

        # Configurations Menu actions
        self.methods_menu()
        self.time_step_action()
        self.boundary_conditions_action()
        self.structure_damping_action()
        self.fluid_parameters_action()

        # Run Menu actions
        self.run_simulation_action()
        self.run_set_of_simulations_action()
        self.run_optimization_action()
        self.run_animation_action()

        # Window Menu actions
        self.maximize_action()
        self.full_screen_action()

        # Help Menu actions
        self.about_action()
        self.dev_tool_action()

        # Main Menu Initialization
        self.main_menu()

        # Show GUI
        self.showMaximized()

        # DEBUG OPTION - LOAD IMMEDIATELY
        if debugOption:
            self.open_file()
            self.run_simulation()

    def new_file_action(self):
        """
        Action for creating a new file. Resets the entire application.
        Shortcut: Ctrl + N
        :return: None
        """
        self.newFileAct = QAction('Novo', self)
        self.newFileAct.setShortcut('Ctrl+N')
        self.newFileAct.triggered.connect(self.new_file)
        # TODO update new file code for new assets

    def new_file(self):
        """ Resets all GUI inputs, inputData variable and save file.

        :return: None
        """

        # Set stories combobox index to 0
        structureTab = self.mainWidget.tabs.structureTab
        structureTab.combox0.setCurrentIndex(0)

        # Reset inputData
        global inputData
        inputData = InputData()
        inputData.configurations = Configurations()

        # Reset method
        self.set_method_mdf()

        # Reset save file
        self.fileName = None
        self.setWindowTitle('Dynapy TLCD Analyser')

        # Reset GUI
        for i in range(structureTab.combox0.count()-1, 0, -1):
            structureTab.combox0.removeItem(i)
        structureTab.le1.setText('')
        structureTab.le2.setText('')
        structureTab.le3.setText('')
        structureTab.le4.setText('')
        structureTab.le5.setText('')
        structureTab.structureCanvas.painter(inputData.stories)

        tlcdTab = self.mainWidget.tabs.tlcdTab
        tlcdTab.combox0.setCurrentIndex(0)
        tlcdTab.le1.setText('')
        tlcdTab.le2.setText('')
        tlcdTab.le3.setText('')
        # tlcdTab.le4.setText('')
        tlcdTab.tlcdCanvas.painter(inputData.tlcd)

        excitationTab = self.mainWidget.tabs.excitationTab
        excitationTab.combox0.setCurrentIndex(0)
        excitationTab.le1.setText('')
        excitationTab.le2.setText('')
        excitationTab.le3.setText('')
        excitationTab.le4.setText('')
        excitationTab.chkbox2.setChecked(True)
        excitationTab.excitationCanvas.plot_excitation([], [])

        reportTab = self.mainWidget.tabs.reportTab
        reportTab.te1.setText("""Relatório ainda não gerado.
Preencha todos os dados e utilize o  comando "Calcular" para gerar o relatório.""")
        reportTab.te1.setFont(QFont("Times", 14))

        dynRespTab = self.mainWidget.tabs.dynRespTab
        dynRespTab.list1.clear()
        dynRespTab.list2.clear()
        dynRespTab.dynRespCanvas.reset_canvas()

        dmfTab = self.mainWidget.tabs.dmfTab

        animationTab = self.mainWidget.tabs.animationTab

        self.exportReportAct.setDisabled(True)
        self.exportAnimationAct.setDisabled(True)

    def open_file_action(self):
        """
        Action for opening a file. Resets the entire application and loads file info.
        Shortcut: Ctrl + O
        :return: None
        """
        self.openFileAct = QAction('Abrir', self)
        self.openFileAct.setShortcut('Ctrl+O')
        self.openFileAct.triggered.connect(self.open_file)

    def open_file(self):
        """ Calls self.new_file to reset everything. Then, brings a open file dialog box and save the directory to
        self.fileName. Reads the file send all data to inputData. Finally, set texts and plot figures to GUI.

        :return: None
        """
        self.new_file()

        # DEBUG OPTION - IMMEDIATELY OPEN
        if debugOption:
            self.fileName = './save/001.dpfl'
        else:
            self.fileName = QFileDialog.getOpenFileName(self, 'Salvar como', './save', filter="DynaPy File (*.dpfl)")
        self.setWindowTitle('Dynapy TLCD Analyser - [{}]'.format(self.fileName))
        self.file = open(self.fileName, 'r', encoding='utf-8')
        self.file.readline()
        self.file.readline()
        storiesNumber = self.file.readline()[:-1]
        storiesData = self.file.readline()[:-1]
        self.file.readline()
        self.file.readline()
        self.file.readline()
        tlcdData = self.file.readline()[:-1]
        self.file.readline()
        self.file.readline()
        self.file.readline()
        excitationData = self.file.readline()[:-1]
        self.file.readline()
        self.file.readline()
        self.file.readline()
        configurationsData = self.file.readline()[:-1]

        storiesNumber = eval(storiesNumber)
        storiesData = eval(storiesData)
        tlcdData = eval(tlcdData)
        excitationData = eval(excitationData)
        configurationsData = eval(configurationsData)

        for i in range(1, storiesNumber + 1):
            inputData.stories.update({i: eval(storiesData[i])})
            self.mainWidget.tabs.structureTab.combox0.addItem(str(i+1))

        inputData.tlcd = TLCD(tlcdData[0], tlcdData[1], tlcdData[2], tlcdData[3])
        inputData.excitation = Excitation(excitationData[0], excitationData[1], excitationData[2],
                                          excitationData[3], excitationData[4], excitationData[5],
                                          inputData.stories, inputData.tlcd)
        inputData.configurations = Configurations(configurationsData[0], configurationsData[1], configurationsData[2],
                                                  configurationsData[3], configurationsData[4], configurationsData[5],
                                                  configurationsData[6])

        self.mainWidget.tabs.structureTab.set_text_change()
        self.mainWidget.tabs.structureTab.structureCanvas.painter(inputData.stories)

        tlcdTypeIndex = self.mainWidget.tabs.tlcdTab.combox0.findText(str(inputData.tlcd.type))
        self.mainWidget.tabs.tlcdTab.combox0.setCurrentIndex(tlcdTypeIndex)
        self.mainWidget.tabs.tlcdTab.le1.setText(str(inputData.tlcd.diameter*100))
        self.mainWidget.tabs.tlcdTab.le2.setText(str(inputData.tlcd.width))
        self.mainWidget.tabs.tlcdTab.le3.setText(str(inputData.tlcd.waterHeight*100))
        self.mainWidget.tabs.tlcdTab.tlcdCanvas.painter(inputData.tlcd)

        exctTypeIndex = self.mainWidget.tabs.excitationTab.combox0.findText(str(inputData.excitation.type))
        self.mainWidget.tabs.excitationTab.combox0.setCurrentIndex(exctTypeIndex)
        self.mainWidget.tabs.excitationTab.le1.setText(str(inputData.excitation.amplitude))
        self.mainWidget.tabs.excitationTab.le2.setText(str(inputData.excitation.frequencyInput))
        self.mainWidget.tabs.excitationTab.le3.setText(str(inputData.excitation.exctDuration))
        self.mainWidget.tabs.excitationTab.le4.setText(str(inputData.excitation.anlyDuration))
        self.mainWidget.tabs.excitationTab.chkbox2.setChecked(inputData.excitation.relativeFrequency)
        tAnly = np.arange(0, inputData.excitation.anlyDuration+inputData.configurations.timeStep,
                          inputData.configurations.timeStep)
        tExct = np.arange(0, inputData.excitation.exctDuration+inputData.configurations.timeStep,
                          inputData.configurations.timeStep)
        a = inputData.excitation.amplitude*np.sin(inputData.excitation.frequency*tExct)
        a = np.hstack((a, np.array([0 for i in range(len(tAnly)-len(tExct))])))
        self.mainWidget.tabs.excitationTab.excitationCanvas.plot_excitation(tAnly, a)

    def save_file_action(self):
        """
        Action for saving a file. Checks if there is a file open.
        If true, saves all info input to this file.
        If false, calls save_file_as_action.
        Shortcut: Ctrl + S
        :return: None
        """
        self.saveFileAct = QAction('Salvar', self)
        self.saveFileAct.setShortcut('Ctrl+S')
        self.saveFileAct.triggered.connect(self.save_file)

    def save_file_as_action(self):
        """
        Action for saving a new file. Opens a file and save all info to it. Rewrites file.
        Shortcut: Ctrl + Alt + S
        :return: None
        """
        self.saveFileAsAct = QAction('Salvar como...', self)
        self.saveFileAsAct.setShortcut('Ctrl+Alt+S')
        self.saveFileAsAct.triggered.connect(self.save_file_as)

    def save_file(self):
        """ Checks for self.fileName: if None, calls save_file_as(), otherwise proceeds to the next check.
        Checks if all data was input: if not, raises error03, otherwise save file to self.fileName directory.
        Save file has the following structure:

        Structure:
        -------------------
        /number of stories/
        /dictionray with story namber as key and Story() call string with proper args/

        TLCD:
        -------------------
        /tuple with TLCD() args/

        Excitation:
        -------------------
        /tuple with Excitation() args/

        Configurations:
        -------------------
        /tuple with Configurations() args/

        *** Example: ***

        Structure:
        -------------------
        1
        {1: 'Story(10000.0, 3.0, 0.35, 0.35, 25000000000.0, "Engastado-Engastado")'}

        TLCD:
        -------------------
        ('TLCD Simples', 0.3, 10.0, 1.0)

        Excitation:
        -------------------
        ('Seno', 5.0, 45.554650526392187, 1.0, 3.0, 5.0)

        Configurations:
        -------------------
        ('Método das Diferenças Finitas', 0.001, 0.0, 0.0, 0.02, 998.2071, 1.003e-06, 9.807)

        :return: None
        """
        if self.fileName is None:
            self.save_file_as()
        elif inputData.stories == {} or inputData.tlcd is None or inputData.excitation is None:
            icon = QStyle.SP_MessageBoxWarning
            self.error03 = QMessageBox()
            self.error03.setText('Preencha e confirme todos os dados nas abas Estrutura, TLCD e Excitação antes '+
                                 'de salvar.')
            self.error03.setWindowTitle('Erro 03')
            self.error03.setWindowIcon(self.error03.style().standardIcon(icon))
            self.error03.setIcon(QMessageBox.Warning)
            self.error03.show()
        else:
            self.file = open(self.fileName, 'w', encoding='utf-8')
            self.file.write('Structure: \n-------------------\n')
            self.file.write('{}\n'.format(len(inputData.stories)))

            stories = {}
            for i, j in inputData.stories.items():
                stories.update({i: 'Story({}, {}, {}, {}, {}, "{}")'.format(j.mass, j.height, j.width,
                                                                          j.depth, j.E, j.vinculum)})
            self.file.write('{}\n'.format(stories))

            self.file.write('\nTLCD: \n-------------------\n')
            tlcd = inputData.tlcd
            tlcdData = (tlcd.type, tlcd.diameter, tlcd.width, tlcd.waterHeight)
            self.file.write('{}\n'.format(tlcdData))

            self.file.write('\nExcitation: \n-------------------\n')
            excitation = inputData.excitation
            excitationData = (excitation.type, excitation.amplitude, excitation.frequencyInput,
                              excitation.relativeFrequency, excitation.exctDuration, excitation.anlyDuration)
            self.file.write('{}\n'.format(excitationData))

            self.file.write('\nConfigurations: \n-------------------\n')
            configurations = inputData.configurations
            configurationsData = (configurations.method, configurations.timeStep, configurations.initialDisplacement,
                                  configurations.initialVelocity, configurations.relativeDampingRatio,
                                  configurations.liquidSpecificMass, configurations.kineticViscosity,
                                  configurations.gravity)
            self.file.write('{}\n'.format(configurationsData))

            self.file.close()

    def save_file_as(self):
        """ Brings a file save dialog box, saves the file directory to self.fileName and calls self.save_file()

        :return: None
        """
        self.fileName = QFileDialog.getSaveFileName(self, 'Salvar como', './save', filter="DynaPy File (*.dpfl)")
        self.setWindowTitle('Dynapy TLCD Analyser - [{}]'.format(self.fileName))
        self.save_file()

    def export_report_action(self):
        """
        Action for exporting report as a text file.
        Opens a file and saves report info to it.
        Shortcut: Ctrl + Alt + E
        :return: None
        """
        self.exportReportAct = QAction('Exportar relatório...', self)
        self.exportReportAct.setShortcut('Ctrl+Alt+E')
        # self.exportReportAct.triggered.connect(sys.exit)
        self.exportReportAct.setDisabled(True)
        # TODO implement export report code

    def export_animation_action(self):
        """
        Action for exporting animation as a gif image.
        Shortcut: Ctrl + Shift + E
        :return: None
        """
        self.exportAnimationAct = QAction('Exportar animação...', self)
        self.exportAnimationAct.setShortcut('Ctrl+Shift+E')
        # self.exportAnimationAct.triggered.connect(sys.exit)
        self.exportAnimationAct.setDisabled(True)
        # TODO implement export animation code

    def quit_action(self):
        """
        Action for quitting the application.
        Shortcut: Ctrl + Q
        :return: None
        """
        self.quitAct = QAction('Sair', self)
        self.quitAct.setShortcut('Ctrl+Q')
        self.quitAct.setStatusTip('Fecha o programa.')
        self.quitAct.triggered.connect(sys.exit)

    def methods_menu(self):
        self.methodsMenu = QMenu('Métodos', self)

        self.mdfMethod = QAction('Método das Diferenças Finitas', self)
        self.mdfMethod.setCheckable(True)
        self.mdfMethod.setChecked(True)
        self.mdfMethod.triggered.connect(self.set_method_mdf)

        self.linAccelMethod = QAction('Método da Aceleração Linear', self)
        self.linAccelMethod.setCheckable(True)
        self.linAccelMethod.triggered.connect(self.set_method_lin_accel)

        self.methodsMenu.addAction(self.mdfMethod)
        self.methodsMenu.addAction(self.linAccelMethod)
        # TODO implement method choice code
        # TODO add avg acceleration method and rk4 method
        # TODO remember to modify set_method_* methods

    def time_step_action(self):
        self.timeStepAct = QAction('Passo...', self)
        self.timeStepAct.setStatusTip('Altera o passo de tempo utilizado nas iterações')
        self.timeStepAct.triggered.connect(self.time_step)

    def time_step(self):
        self.timeStepDialog = QWidget()
        self.timeStepDialog.grid = QGridLayout()
        self.timeStepDialog.label = QLabel('Passo de tempo: (s)', self)
        self.timeStepDialog.le = QLineEdit(self)
        self.timeStepDialog.le.setPlaceholderText('0.001')
        self.timeStepDialog.le.setText(str(inputData.configurations.timeStep))
        self.timeStepDialog.button = QPushButton('Ok', self)
        self.timeStepDialog.button.clicked.connect(self.time_step_config)
        self.timeStepDialog.grid.addWidget(self.timeStepDialog.label, 1, 1)
        self.timeStepDialog.grid.addWidget(self.timeStepDialog.le, 1, 2)
        self.timeStepDialog.grid.addWidget(self.timeStepDialog.button, 2, 1, 1, 2)
        self.timeStepDialog.setLayout(self.timeStepDialog.grid)
        self.timeStepDialog.setWindowTitle('Definição do passo de tempo')
        self.timeStepDialog.setGeometry(300, 300, 300, 200)
        self.timeStepDialog.show()

    def time_step_config(self):
        try:
            inputData.configurations.timeStep = float(get_text(self.timeStepDialog.le))
            self.timeStepDialog.hide()
        except ValueError:
            icon = QStyle.SP_MessageBoxWarning
            self.error05 = QMessageBox()
            self.error05.setText('O passo de tempo deve ser um número real')
            self.error05.setWindowTitle('Erro 05')
            self.error05.setWindowIcon(self.error05.style().standardIcon(icon))
            self.error05.setIcon(QMessageBox.Warning)
            self.error05.show()

    def boundary_conditions_action(self):
        self.boundaryConditionsAct = QAction('Condições de contorno...', self)
        self.boundaryConditionsAct.setStatusTip('Altera deslocamento e velocidade inicial')
        self.boundaryConditionsAct.triggered.connect(self.boundary_conditions)

    def boundary_conditions(self):
        self.boundaryConditionsDialog = QWidget()
        self.boundaryConditionsDialog.grid = QGridLayout()
        self.boundaryConditionsDialog.label1 = QLabel('Deslocamento inicial: (m)')
        self.boundaryConditionsDialog.label2 = QLabel('Velocidade inicial: (m/s)')
        self.boundaryConditionsDialog.le1 = QLineEdit(self)
        self.boundaryConditionsDialog.le1.setPlaceholderText('0.00')
        self.boundaryConditionsDialog.le1.setText(str(inputData.configurations.initialDisplacement))
        self.boundaryConditionsDialog.le2 = QLineEdit(self)
        self.boundaryConditionsDialog.le2.setPlaceholderText('0.00')
        self.boundaryConditionsDialog.le2.setText(str(inputData.configurations.initialVelocity))
        self.boundaryConditionsDialog.btn = QPushButton('Ok', self)
        self.boundaryConditionsDialog.btn.clicked.connect(self.boundary_conditions_config)
        self.boundaryConditionsDialog.grid.addWidget(self.boundaryConditionsDialog.label1, 1, 1)
        self.boundaryConditionsDialog.grid.addWidget(self.boundaryConditionsDialog.label2, 2, 1)
        self.boundaryConditionsDialog.grid.addWidget(self.boundaryConditionsDialog.le1, 1, 2)
        self.boundaryConditionsDialog.grid.addWidget(self.boundaryConditionsDialog.le2, 2, 2)
        self.boundaryConditionsDialog.grid.addWidget(self.boundaryConditionsDialog.btn, 3, 1, 1, 2)
        self.boundaryConditionsDialog.setLayout(self.boundaryConditionsDialog.grid)
        self.boundaryConditionsDialog.setWindowTitle('Definição das condições de contorno')
        self.boundaryConditionsDialog.setGeometry(300, 300, 300, 200)
        self.boundaryConditionsDialog.show()

    def boundary_conditions_config(self):
        try:
            inputData.configurations.initialDisplacement = float(get_text(self.boundaryConditionsDialog.le1))
            inputData.configurations.initialVelocity = float(get_text(self.boundaryConditionsDialog.le2))
            self.boundaryConditionsDialog.hide()
        except ValueError:
            icon = QStyle.SP_MessageBoxWarning
            self.error06 = QMessageBox()
            self.error06.setText('Deslocamento e velocidade iniciais devem ser números reais')
            self.error06.setWindowTitle('Erro 06')
            self.error06.setWindowIcon(self.error06.style().standardIcon(icon))
            self.error06.setIcon(QMessageBox.Warning)
            self.error06.show()

    def structure_damping_action(self):
        self.structureDampingAct = QAction('Amortecimento da Estrutura...', self)
        self.structureDampingAct.setStatusTip('Altera a taxa de amortecimento da estrutura')
        self.structureDampingAct.triggered.connect(self.structure_damping)

    def structure_damping(self):
        self.structureDampingDialog = QWidget()
        self.structureDampingDialog.grid = QGridLayout()
        self.structureDampingDialog.label = QLabel('Taxa de amortecimento da estrutura:', self)
        self.structureDampingDialog.le = QLineEdit(self)
        self.structureDampingDialog.le.setPlaceholderText('0.02')
        self.structureDampingDialog.le.setText(str(inputData.configurations.relativeDampingRatio))
        self.structureDampingDialog.button = QPushButton('Ok', self)
        self.structureDampingDialog.button.clicked.connect(self.structure_damping_config)
        self.structureDampingDialog.grid.addWidget(self.structureDampingDialog.label, 1, 1)
        self.structureDampingDialog.grid.addWidget(self.structureDampingDialog.le, 1, 2)
        self.structureDampingDialog.grid.addWidget(self.structureDampingDialog.button, 2, 1, 1, 2)
        self.structureDampingDialog.setLayout(self.structureDampingDialog.grid)
        self.structureDampingDialog.setWindowTitle('Definição da taxa de amortecimento da estrutura')
        self.structureDampingDialog.setGeometry(300, 300, 300, 200)
        self.structureDampingDialog.show()

    def structure_damping_config(self):
        try:
            inputData.configurations.relativeDampingRatio = float(get_text(self.structureDampingDialog.le))
            self.structureDampingDialog.hide()
        except ValueError:
            icon = QStyle.SP_MessageBoxWarning
            self.error07 = QMessageBox()
            self.error07.setText('A taxa de amortecimento da estrutura deve ser um número real')
            self.error07.setWindowTitle('Erro 07')
            self.error07.setWindowIcon(self.error07.style().standardIcon(icon))
            self.error07.setIcon(QMessageBox.Warning)
            self.error07.show()

    def fluid_parameters_action(self):
        self.fluidParametersAct = QAction('Parâmetros do fluido...', self)
        self.fluidParametersAct.setStatusTip('Altera os parâmetros do fluido')
        self.fluidParametersAct.triggered.connect(self.fluid_parameters)

    def fluid_parameters(self):
        self.fluidParametersDialog = QWidget()
        self.fluidParametersDialog.grid = QGridLayout()
        self.fluidParametersDialog.label1 = QLabel('Massa específica: (kg/m³)')
        self.fluidParametersDialog.label2 = QLabel('Viscosidade cinemática: (m²/s)')
        self.fluidParametersDialog.le1 = QLineEdit(self)
        self.fluidParametersDialog.le1.setPlaceholderText('998.2071')
        self.fluidParametersDialog.le1.setText(str(inputData.configurations.liquidSpecificMass))
        self.fluidParametersDialog.le2 = QLineEdit(self)
        self.fluidParametersDialog.le2.setPlaceholderText('1.003e-6')
        self.fluidParametersDialog.le2.setText(str(inputData.configurations.kineticViscosity))
        self.fluidParametersDialog.btn = QPushButton('Ok', self)
        self.fluidParametersDialog.btn.clicked.connect(self.fluid_parameters_config)
        self.fluidParametersDialog.grid.addWidget(self.fluidParametersDialog.label1, 1, 1)
        self.fluidParametersDialog.grid.addWidget(self.fluidParametersDialog.label2, 2, 1)
        self.fluidParametersDialog.grid.addWidget(self.fluidParametersDialog.le1, 1, 2)
        self.fluidParametersDialog.grid.addWidget(self.fluidParametersDialog.le2, 2, 2)
        self.fluidParametersDialog.grid.addWidget(self.fluidParametersDialog.btn, 3, 1, 1, 2)
        self.fluidParametersDialog.setLayout(self.fluidParametersDialog.grid)
        self.fluidParametersDialog.setWindowTitle('Definição dos parâmetros do fluido')
        self.fluidParametersDialog.setGeometry(300, 300, 300, 200)
        self.fluidParametersDialog.show()

    def fluid_parameters_config(self):
        try:
            inputData.configurations.liquidSpecificMass = float(get_text(self.fluidParametersDialog.le1))
            inputData.configurations.kineticViscosity = float(get_text(self.fluidParametersDialog.le2))
            self.fluidParametersDialog.hide()
        except ValueError:
            icon = QStyle.SP_MessageBoxWarning
            self.error08 = QMessageBox()
            self.error08.setText('Massa específica e viscosidade cinemática devem ser números reais')
            self.error08.setWindowTitle('Erro 08')
            self.error08.setWindowIcon(self.error08.style().standardIcon(icon))
            self.error08.setIcon(QMessageBox.Warning)
            self.error08.show()

    def set_method_mdf(self):
        self.mdfMethod.setChecked(True)
        self.linAccelMethod.setChecked(False)

    def set_method_lin_accel(self):
        self.mdfMethod.setChecked(False)
        self.linAccelMethod.setChecked(True)

    def run_simulation_action(self):
        """
        Action for running the program for a given set of parameters.
        Generates dynamic response plots.
        Generates simulation, but does not show up.
        Shortcut: Ctrl + R
        :return: None
        """
        self.runSimAct = QAction('Resposta Dinâmica', self)
        self.runSimAct.setShortcut('Ctrl+R')
        self.runSimAct.setStatusTip('Calcula e plota a resposta dinâmica da estrutura.')
        self.runSimAct.triggered.connect(self.run_simulation)
        # TODO Implement calculation and ploting code

    def run_simulation(self):
        if inputData.stories == {} or inputData.tlcd is None or inputData.excitation is None:
            icon = QStyle.SP_MessageBoxWarning
            self.error04 = QMessageBox()
            self.error04.setText('Preencha e confirme todos os dados nas abas Estrutura, TLCD e Excitação antes '+
                                 'de acionar a rotina de cálculo.')
            self.error04.setWindowTitle('Erro 04')
            self.error04.setWindowIcon(self.error04.style().standardIcon(icon))
            self.error04.setIcon(QMessageBox.Warning)
            self.error04.show()
        else:
            # Confirm tlcd
            self.mainWidget.tabs.tlcdTab.add_tlcd()

            # Add the tlcd to the last story
            lastStory = inputData.stories[len(inputData.stories)]
            inputData.stories[len(inputData.stories)] = Story(lastStory.mass, lastStory.height, lastStory.width,
                                                              lastStory.depth, lastStory.E, lastStory.vinculum,
                                                              inputData.tlcd)

            # Calculate the damping ratio of each story
            for i in inputData.stories.values():
                i.calc_damping_ratio(inputData.configurations.relativeDampingRatio)

            # Confirm excitation
            self.mainWidget.tabs.excitationTab.add_excitation()

            # Calculate response
            def process(outputSignal):
                global outputData
                outputData = outputSignal

                # Generate plot
                self.mainWidget.tabs.dynRespTab.add_list1_items()
                self.mainWidget.tabs.dynRespTab.list1.setCurrentRow(self.mainWidget.tabs.dynRespTab.list1.count() - 2)
                self.mainWidget.tabs.dynRespTab.add_list2_item()
                self.mainWidget.tabs.dynRespTab.plot_dyn_resp()

                # Generate report
                self.mainWidget.tabs.reportTab.generate_report_simulation()

            self.runSimulationThread = RunSimulationThread(inputData)
            self.runSimulationThread.mySignal.connect(process)
            self.runSimulationThread.start()

    def run_set_of_simulations_action(self):
        """
        Action for running the program for a given set of parameters multiple times.
        Generates dynamic magnification factor plots and dynamic response at r=1.
        Generates simulation, but does not show up.
        Shortcut: Ctrl + Alt + R
        :return: None
        """
        self.runSetofSimAct = QAction('DMF(r)', self)
        self.runSetofSimAct.setShortcut('Ctrl+Alt+R')
        self.runSetofSimAct.setStatusTip('Calcula e plota a o Fator de Amplificação Dinâmica' +
                                         ' em função da Relação de Frequências.')
        self.runSetofSimAct.triggered.connect(self.run_set_of_simulations)
        # self.runSetofSimAct.setDisabled(True)
        # TODO Implement calculation and ploting code

    def run_set_of_simulations(self):
        if inputData.stories == {} or inputData.tlcd is None or inputData.excitation is None:
            icon = QStyle.SP_MessageBoxWarning
            self.error04 = QMessageBox()
            self.error04.setText('Preencha e confirme todos os dados nas abas Estrutura, TLCD e Excitação antes '+
                                 'de acionar a rotina de cálculo.')
            self.error04.setWindowTitle('Erro 04')
            self.error04.setWindowIcon(self.error04.style().standardIcon(icon))
            self.error04.setIcon(QMessageBox.Warning)
            self.error04.show()
        else:
            # Confirm tlcd
            self.mainWidget.tabs.tlcdTab.add_tlcd()

            # Add the tlcd to the last story
            lastStory = inputData.stories[len(inputData.stories)]
            inputData.stories[len(inputData.stories)] = Story(lastStory.mass, lastStory.height, lastStory.width,
                                                              lastStory.depth, lastStory.E, lastStory.vinculum,
                                                              inputData.tlcd)

            # Calculate the damping ratio of each story
            for i in inputData.stories.values():
                i.calc_damping_ratio(inputData.configurations.relativeDampingRatio)

            # Confirm excitation
            self.mainWidget.tabs.excitationTab.add_excitation()

            relativeFrequencies = np.arange(0.01, 2.01, 0.01)

            def process(signalMessage):
                global DMFPlotList
                dmfList = signalMessage
                DMFPlotList = [relativeFrequencies, dmfList]
                self.mainWidget.tabs.dmfTab.dmfCanvas.plot_dmf(relativeFrequencies, dmfList)

            self.runSetOfSimulationsThread = RunSetOfSimulationsThread(inputData, relativeFrequencies)
            self.runSetOfSimulationsThread.mySignal.connect(process)
            progressBar = self.mainWidget.tabs.dmfTab.progressBar
            self.runSetOfSimulationsThread.percentageSignal.connect(progressBar.setValue)
            self.runSetOfSimulationsThread.start()

    def run_optimization_action(self):
        """
        Action for running the program for a given set of parameters and find optimum design.
        Generates dynamic magnification factor plots and dynamic response at r=1.
        Generates simulation, but does not show up.
        Shortcut: Ctrl + R
        :return: None
        """
        self.runOptimizationAct = QAction('Otimização', self)
        self.runOptimizationAct.setShortcut('Ctrl+Alt+Shift+R')
        self.runOptimizationAct.setStatusTip('Calcula e plota a resposta dinâmica da estrutura.')
        # self.runOptimizationAct.triggered.connect(sys.exit)
        self.runOptimizationAct.setDisabled(True)
        # TODO Implement calculation and ploting code

    def run_animation_action(self):
        """
        Action for running the program for a given set of parameters and find optimum design.
        Generates dynamic magnification factor plots and dynamic response at r=1.
        Generates simulation, but does not show up.
        Shortcut: Ctrl + R
        :return: None
        """
        self.runAnimationAct = QAction('Animação', self)
        self.runAnimationAct.setShortcut('Ctrl+Shift+R')
        self.runAnimationAct.setStatusTip('Gera animação da resposta dinâmica da estrutura.')
        # self.runAnimationAct.triggered.connect(sys.exit)
        self.runAnimationAct.setDisabled(True)
        # TODO Implement calculation and ploting code

    def maximize_action(self):
        """
        Action for maximizing the GUI Window.
        Shortcut: None
        :return: None
        """
        self.maximize = QAction('Maximizar', self)
        self.maximize.setStatusTip('Maximiza a janela')
        self.maximize.triggered.connect(self.showMaximized)

    def full_screen_action(self):
        """
        Action for toggling full screen on and off.
        Shortcut: Ctrl + F
        :return: None
        """
        self.full_screen = QAction('Tela Cheia', self)
        self.full_screen.setStatusTip('Modo tela cheia')
        self.full_screen.setShortcut('Ctrl+F')
        self.full_screen.triggered.connect(self.check_full_screen_func)
        # TODO fix full screen toggling flickering

    def check_full_screen_func(self):
        """
        Method that checks if application is on full screen or not and toggles state.
        :return: None
        """
        if self.isFullScreen():
            self.full_screen.triggered.connect(self.showNormal)
        else:
            self.full_screen.triggered.connect(self.showFullScreen)

    def about_action(self):
        """
        Action for showing the application 'About'.
        Shortcut: F1
        :return: None
        """
        self.aboutmsg = QMessageBox()
        self.aboutmsg.setText('Dynapy TLCD Analyser - Versão 0.4')
        self.aboutmsg.setInformativeText(
            'Esse programa toma os dados de um edifício tipo "shear-building" equipado com um Amortecedor de ' +
            'Coluna de Líquido Sintonizado (TLCD) e calcula a resposta dinâmica de cada um dos pavimentos. ' +
            'Além disso, o software é capaz de fazer análises de frequências, otimizações e gerar animações. ' +
            'Esse programa tem cunho puramente educacional. O autor não se responsabiliza pelo uso ou mau uso do ' +
            'programa e pelos seus resultados. O usuário é responsávelo por toda e qualquer conclusão feita ' +
            'com o uso do programa. Não existe nenhum compromisso de bom funcionamento ou qualquer garantia.')
        self.aboutmsg.setWindowTitle('Dynapy TLCD Analyser')
        self.aboutmsg.setIconPixmap(QPixmap(None))

        self.aboutAct = QAction('Sobre', self)
        self.aboutAct.setShortcut('F1')
        self.aboutAct.setStatusTip('Mostra as informações do programa')
        self.aboutAct.triggered.connect(self.aboutmsg.exec_)
        # TODO Fix about text. Include icon, name, version, author, date and description.

    def dev_tool_action(self):
        self.devToolAct = QAction('Development Tool', self)
        self.devToolAct.setShortcut('Shift+F10')
        self.devToolAct.setStatusTip('Abre uma caixa de diálogo para executar linhas de código digitadas pelo usuário.')
        self.devToolAct.triggered.connect(self.dev_tool)

    def dev_tool(self):
        self.devDialog = QWidget()

        self.devDialog.setGeometry(300, 300, 800, 200)
        self.devDialog.setWindowTitle('Development Tool')

        self.devDialog.textEdit = QTextEdit(self)
        self.devDialog.btn = QPushButton('Executar', self)
        self.devDialog.btn.clicked.connect(self.dev_tool_exec)
        self.devDialog.layout = QGridLayout()
        self.devDialog.layout.addWidget(self.devDialog.textEdit, 1, 1)
        self.devDialog.layout.addWidget(self.devDialog.btn, 2, 1)
        self.devDialog.setLayout(self.devDialog.layout)

        self.devDialog.show()

    def dev_tool_exec(self):
        exec(get_text(self.devDialog.textEdit))

    def main_menu(self):
        """
        Method for setting up Main Menu bar. Creates the menu and add the actions.
        :return: None
        """

        # Create Main Menu Bar
        mainMenu = self.menuBar()

        # Create File Menu and add Actions
        fileMenu = mainMenu.addMenu('Arquivo')
        fileMenu.addAction(self.newFileAct)
        fileMenu.addAction(self.openFileAct)
        fileMenu.addAction(self.saveFileAct)
        fileMenu.addAction(self.saveFileAsAct)
        fileMenu.addSeparator()
        fileMenu.addAction(self.exportReportAct)
        fileMenu.addAction(self.exportAnimationAct)
        fileMenu.addSeparator()
        fileMenu.addAction(self.quitAct)

        # Create Configurations Menu and add Actions
        configMenu = mainMenu.addMenu('Configurações')
        configMenu.addMenu(self.methodsMenu)
        configMenu.addAction(self.timeStepAct)
        configMenu.addAction(self.boundaryConditionsAct)
        configMenu.addAction(self.structureDampingAct)
        configMenu.addAction(self.fluidParametersAct)

        # Create Run Menu and add Actions
        runMenu = mainMenu.addMenu('Calcular')
        runMenu.addAction(self.runSimAct)
        runMenu.addAction(self.runSetofSimAct)
        runMenu.addAction(self.runOptimizationAct)
        runMenu.addAction(self.runAnimationAct)

        # Create Window Menu and add Actions
        windowMenu = mainMenu.addMenu('Janela')
        windowMenu.addAction(self.maximize)
        windowMenu.addAction(self.full_screen)
        windowMenu.addSeparator()

        # Create Help Menu and add Actions
        helpMenu = mainMenu.addMenu('Ajuda')
        helpMenu.addAction(self.aboutAct)
        helpMenu.addSeparator()
        helpMenu.addAction(self.devToolAct)

        # Set up status bar
        self.statusBar()


class MainWidget(QWidget):
    def __init__(self, parent):
        super(MainWidget, self).__init__(parent)

        self.tabs = TabWidget(self)

        self.grid = QGridLayout()
        self.grid.addWidget(self.tabs, 1, 1, 1, 1)
        self.setLayout(self.grid)


class TabWidget(QTabWidget):
    def __init__(self, parent):
        super(TabWidget, self).__init__(parent)

        self.structureTab = StructureTab(self)
        self.addTab(self.structureTab, 'Estrutura')

        self.tlcdTab = TLCDTab(self)
        self.addTab(self.tlcdTab, 'TLCD')

        self.excitationTab = ExcitationTab(self)
        self.addTab(self.excitationTab, 'Excitação')

        self.reportTab = ReportTab(self)
        self.addTab(self.reportTab, 'Relatório')

        self.dynRespTab = DynRespTab(self)
        self.addTab(self.dynRespTab, 'Resposta Dinâmica')

        self.dmfTab = DMFTab(self)
        self.addTab(self.dmfTab, 'DMF(r)')

        self.animationTab = AnimationTab(self)
        self.addTab(self.animationTab, 'Animação')


class StructureTab(QWidget):
    def __init__(self, parent):
        super(StructureTab, self).__init__(parent)

        self.lb0 = QLabel('Número do Pavimento: ', self)
        self.lb1 = QLabel('Massa do Pavimento: (toneladas)', self)
        self.lb2 = QLabel('Altura do Pavimento: (m)', self)
        self.lb3 = QLabel('Largura dos Pilares: (cm)', self)
        self.lb4 = QLabel('Profundidade dos Pilares: (cm)', self)
        self.lb5 = QLabel('Módulo de Elasticidade dos Pilares: (GPa)', self)
        self.lb6 = QLabel('Vínculo dos Pilares: ', self)

        self.combox0 = QComboBox(self)
        self.combox0.addItem('1')
        self.combox0.currentIndexChanged.connect(self.set_text_change)

        self.le1 = QLineEdit(self)
        self.le1.setPlaceholderText('10')

        self.le2 = QLineEdit(self)
        self.le2.setPlaceholderText('3')

        self.le3 = QLineEdit(self)
        self.le3.setPlaceholderText('35')

        self.le4 = QLineEdit(self)
        self.le4.setPlaceholderText('35')

        self.le5 = QLineEdit(self)
        self.le5.setPlaceholderText('25')

        self.combox6 = QComboBox(self)
        self.combox6.addItem('Engastado-Engastado')
        self.combox6.addItem('Engastado-Apoiado')
        self.combox6.addItem('Apoiado-Engastado')
        self.combox6.addItem('Apoiado-Apoiado')

        self.btn7 = QPushButton('Adicionar Pavimento', self)
        self.btn7.clicked.connect(self.add_story)

        self.btn8 = QPushButton('Remover Pavimento', self)
        self.btn8.clicked.connect(self.remove_story)

        self.structureCanvas = StructureCanvas(self)

        self.blanklb1 = QLabel('1', self)
        self.blanklb1.setFixedSize(1, 1)
        self.blanklb2 = QLabel('1', self)
        self.blanklb2.setFixedSize(1, 1)

        self.form = QGridLayout()
        self.form.addWidget(self.lb0, 0, 1)
        self.form.addWidget(self.lb1, 1, 1)
        self.form.addWidget(self.lb2, 2, 1)
        self.form.addWidget(self.lb3, 3, 1)
        self.form.addWidget(self.lb4, 4, 1)
        self.form.addWidget(self.lb5, 5, 1)
        self.form.addWidget(self.lb6, 6, 1)
        self.form.addWidget(self.combox0, 0, 2)
        self.form.addWidget(self.le1, 1, 2)
        self.form.addWidget(self.le2, 2, 2)
        self.form.addWidget(self.le3, 3, 2)
        self.form.addWidget(self.le4, 4, 2)
        self.form.addWidget(self.le5, 5, 2)
        self.form.addWidget(self.combox6, 6, 2)
        self.form.addWidget(self.btn7, 7, 1, 1, 2)
        self.form.addWidget(self.btn8, 8, 1, 1, 2)

        self.grid = QGridLayout()
        self.grid.addLayout(self.form, 1, 1)
        self.grid.addWidget(self.structureCanvas, 1, 2)
        self.setLayout(self.grid)

    def add_story(self):
        storyNumber = int(get_text(self.combox0))  # integer
        mass = float(get_text(self.le1)) * 1000  # float (ton -> kg)
        height = float(get_text(self.le2))  # float (m -> m)
        width = float(get_text(self.le3)) / 100  # float (cm -> m)
        depth = float(get_text(self.le4)) / 100  # float (cm -> m)
        E = float(get_text(self.le5)) * 1e9  # float (GPa -> Pa)
        vinculum = str(get_text(self.combox6))  # string

        story = Story(mass, height, width, depth, E, vinculum)
        inputData.stories.update({storyNumber: story})
        self.structureCanvas.painter(inputData.stories)

        if self.combox0.currentIndex() + 1 == self.combox0.count():
            self.combox0.addItem(str(int(get_text(self.combox0)) + 1))
            self.combox0.setCurrentIndex(self.combox0.currentIndex()+1)
        else:
            self.combox0.setCurrentIndex(self.combox0.currentIndex()+1)

    def remove_story(self):
        if self.combox0.currentIndex() + 1 == self.combox0.count() - 1:
            storyNumber = int(get_text(self.combox0))
            inputData.stories.pop(storyNumber)
            self.combox0.removeItem(storyNumber)
            self.structureCanvas.painter(inputData.stories)
        else:
            icon = QStyle.SP_MessageBoxWarning
            self.msgRemoveStory = QMessageBox()
            self.msgRemoveStory.setText('Remova primeiro o último andar adicionado.')
            self.msgRemoveStory.setWindowTitle('Erro de Remoção')
            self.msgRemoveStory.setWindowIcon(self.msgRemoveStory.style().standardIcon(icon))
            self.msgRemoveStory.show()

    def set_text_change(self):
        i = int(get_text(self.combox0))
        if i <= len(inputData.stories):
            self.le1.setText(str(inputData.stories[i].mass/1e3))
            self.le2.setText(str(inputData.stories[i].height))
            self.le3.setText(str(inputData.stories[i].width*100))
            self.le4.setText(str(inputData.stories[i].depth*100))
            self.le5.setText(str(inputData.stories[i].E/1e9))
            self.combox6.setCurrentIndex(self.combox6.findText(str(inputData.stories[i].vinculum)))

        else:
            self.le1.setText(str(inputData.stories[i-1].mass/1e3))
            self.le2.setText(str(inputData.stories[i-1].height))
            self.le3.setText(str(inputData.stories[i-1].width*100))
            self.le4.setText(str(inputData.stories[i-1].depth*100))
            self.le5.setText(str(inputData.stories[i-1].E/1e9))
            self.combox6.setCurrentIndex(self.combox6.findText(str(inputData.stories[i-1].vinculum)))


class TLCDTab(QWidget):
    def __init__(self, parent):
        super(TLCDTab, self).__init__(parent)

        self.combox0 = QComboBox(self)
        self.combox0.addItem('TLCD Simples')
        # self.combox0.addItem('TLCD Pressurizado')

        self.lb0 = QLabel('Model de TLCD', self)
        self.lb1 = QLabel('Diâmetro: (cm)', self)
        self.lb2 = QLabel('Largura: (m)', self)
        self.lb3 = QLabel('Altura da lâmina: (cm)', self)
        # self.lb4 = QLabel('Pressão de ar: (kPa)', self)

        self.le1 = QLineEdit(self)
        self.le1.setPlaceholderText('30')

        self.le2 = QLineEdit(self)
        self.le2.setPlaceholderText('10')

        self.le3 = QLineEdit(self)
        self.le3.setPlaceholderText('100')

        # self.le4 = QLineEdit(self)
        # self.le4.setPlaceholderText('1')
        # self.le4.setDisabled(True)

        self.btn5 = QPushButton('Confirmar TLCD', self)
        self.btn5.clicked.connect(self.add_tlcd)

        self.tlcdCanvas = TLCDCanvas(self)

        self.form = QGridLayout()
        self.form.addWidget(self.lb0, 0, 1)
        self.form.addWidget(self.combox0, 0, 2)
        self.form.addWidget(self.lb1, 1, 1)
        self.form.addWidget(self.le1, 1, 2)
        self.form.addWidget(self.lb2, 3, 1)
        self.form.addWidget(self.le2, 3, 2)
        self.form.addWidget(self.lb3, 2, 1)
        self.form.addWidget(self.le3, 2, 2)
        # self.form.addWidget(self.lb4, 4, 1)
        # self.form.addWidget(self.le4, 4, 2)
        self.form.addWidget(self.btn5, 4, 1, 1, 2)

        self.grid = QGridLayout()
        self.grid.addLayout(self.form, 1, 1)
        self.grid.addWidget(self.tlcdCanvas, 1, 2)
        self.setLayout(self.grid)

    def add_tlcd(self):
        inputData.tlcd = None
        tlcdType = get_text(self.combox0)

        if tlcdType == 'TLCD Simples':
            diameter = float(get_text(self.le1))/100  # float (cm -> m)
            width = float(get_text(self.le2))   # float (m)
            waterHeight = float(get_text(self.le3))/100     # float (cm -> m)
            tlcd = TLCD(tlcdType, diameter, width, waterHeight, configurations=inputData.configurations)
            inputData.tlcd = tlcd
            self.tlcdCanvas.painter(tlcd)
        else:
            self.tlcdCanvas.painter(None)


class ExcitationTab(QWidget):
    def __init__(self, parent):
        super(ExcitationTab, self).__init__(parent)

        self.lb0 = QLabel('Tipo de Excitação', self)
        self.lb1 = QLabel('Amplitude: (m/s²)', self)
        self.lb2 = QLabel('Frequência: (rad/s)', self)
        self.lb3 = QLabel('Duração da Excitação: (s)', self)
        self.lb4 = QLabel('Tempo de Análise: (s)', self)

        self.combox0 = QComboBox(self)
        self.combox0.addItem('Seno')

        self.le1 = QLineEdit(self)
        self.le1.setPlaceholderText('5')

        self.le2 = QLineEdit(self)
        self.le2.setPlaceholderText('30')

        self.chkbox2 = QCheckBox('Usar relação de frequências', self)
        self.chkbox2.stateChanged.connect(self.lb2_change)
        self.chkbox2.setChecked(True)

        self.le3 = QLineEdit(self)
        self.le3.setPlaceholderText('3')

        self.le4 = QLineEdit(self)
        self.le4.setPlaceholderText('5')

        self.btn5 = QPushButton('Confirmar Excitação', self)
        self.btn5.clicked.connect(self.add_excitation)

        self.excitationCanvas = PltCanvas()

        self.form = QGridLayout()
        self.form.addWidget(self.lb0, 0, 1)
        self.form.addWidget(self.lb1, 1, 1)
        self.form.addWidget(self.lb2, 2, 1)
        self.form.addWidget(self.lb3, 3, 1)
        self.form.addWidget(self.lb4, 4, 1)
        self.form.addWidget(self.combox0, 0, 2)
        self.form.addWidget(self.le1, 1, 2)
        self.form.addWidget(self.le2, 2, 2)
        self.form.addWidget(self.le3, 3, 2)
        self.form.addWidget(self.le4, 4, 2)
        self.form.addWidget(self.chkbox2, 2, 3)
        self.form.addWidget(self.btn5, 5, 1, 1, 3)

        self.grid = QGridLayout()
        self.grid.addLayout(self.form, 1, 1)
        self.grid.addWidget(self.excitationCanvas, 1, 2)
        self.setLayout(self.grid)

    def lb2_change(self):
        if self.chkbox2.isChecked():
            self.lb2.setText('Relação de Frequências: (decimal)')
            self.le2.setPlaceholderText('0.9')
        else:
            self.lb2.setText('Frequência: (rad/s)')
            self.le2.setPlaceholderText('30')

    def add_excitation(self):
        exct_type = get_text(self.combox0)

        if exct_type == 'Seno':
            amplitude = float(get_text(self.le1))
            frequency = float(get_text(self.le2))
            relativeFrequency = float(self.chkbox2.isChecked())
            exctDuration = float(get_text(self.le3))
            anlyDuration = float(get_text(self.le4))

            if relativeFrequency and (inputData.stories == {} or inputData.tlcd is None):
                icon = QStyle.SP_MessageBoxWarning
                self.error01 = QMessageBox()
                self.error01.setText('Para utilizar a opção de frequência relativa é necessário ' +
                                            'adicionar a estrutura e o TLCD previamente.')
                self.error01.setWindowTitle('Erro 01')
                self.error01.setWindowIcon(self.error01.style().standardIcon(icon))
                self.error01.setIcon(QMessageBox.Warning)
                self.error01.show()
            elif anlyDuration < exctDuration:
                icon = QStyle.SP_MessageBoxWarning
                self.error02 = QMessageBox()
                self.error02.setText('Tempo de análise não pode ser menor do que o tempo de excitação.')
                self.error02.setWindowTitle('Erro 02')
                self.error02.setWindowIcon(self.error02.style().standardIcon(icon))
                self.error02.setIcon(QMessageBox.Warning)
                self.error02.show()
            else:
                excitation = Excitation(exct_type, amplitude, frequency, relativeFrequency, exctDuration, anlyDuration,
                                        structure=inputData.stories, tlcd=inputData.tlcd)
                inputData.excitation = excitation

                tAnly = np.arange(0, anlyDuration+inputData.configurations.timeStep, inputData.configurations.timeStep)
                tExct = np.arange(0, exctDuration+inputData.configurations.timeStep, inputData.configurations.timeStep)
                a = amplitude*np.sin(excitation.frequency*tExct)
                a = np.hstack((a, np.array([0 for i in range(len(tAnly)-len(tExct))])))

                self.excitationCanvas.plot_excitation(tAnly, a)


class ReportTab(QWidget):
    def __init__(self, parent):
        super(ReportTab, self).__init__(parent)

        self.te1 = QTextBrowser(self)
        self.te1.setText("""Relatório ainda não gerado.
Preencha todos os dados e utilize o  comando "Calcular" para gerar o relatório.""")
        self.te1.setFont(QFont("Times", 14))

        self.grid = QGridLayout()
        self.grid.addWidget(self.te1, 1, 1)
        self.setLayout(self.grid)

    def generate_report_simulation(self):
        self.title = "DynaPy TLCD Analyser - Relatório\nAnálise do Sistema Estrutura-TLCD Sob Único Caso de Excitação"

        self.h1_vars = "Variáveis de Entrada"

        self.h2_struct = "Estrutura"

        self.struct_num = "Número de pavimentos: {}".format(len(inputData.stories))

        self.storiesTable = []

        for i in range(1, len(inputData.stories) + 1):
            self.storiesTable.append([i,
                                      inputData.stories[i].mass/1000,
                                      inputData.stories[i].height,
                                      inputData.stories[i].width*100,
                                      inputData.stories[i].depth*100,
                                      inputData.stories[i].E/1e9,
                                      inputData.stories[i].vinculum])

        self.storiesData = ''

        for i in self.storiesTable:
            self.storiesData += """Pavimento {}:
Massa: {} ton
Altura: {} m
Largura dos pilares: {} cm
Profundidade dos pilares: {} cm
Módulo de elasticidade dos pilares: {} GPa

""".format(i[0], i[1], i[2], i[3], i[4], i[5])

        self.h2_TLCD = 'TLCD'

        if inputData.tlcd.type == 'TLCD Simples':
            self.tlcdData = """Tipo: {}
Diâmetro: {} cm
Altura da lamina d'água: {} cm
Largura: {} m""".format(inputData.tlcd.type, inputData.tlcd.diameter*100,
                        inputData.tlcd.waterHeight*100, inputData.tlcd.width)

        self.h2_exct = 'Excitação'

        if inputData.excitation.type == 'Seno':
            if inputData.excitation.relativeFrequency:
                self.freq = '{} * (frequência natural do último pavimento)'.format(
                    inputData.excitation.frequencyInput) + ' = {:.2f} rad/s'.format(inputData.excitation.frequency)
            else:
                self.freq = '{} rad/s'.format(inputData.excitation.frequency)
            self.exctData = """Tipo de excitação: {}
Amplitude: {} m/s²
Frequência: {}
Duração da excitação: {} s
Tempo de análise: {} s""".format(inputData.excitation.type, inputData.excitation.amplitude, self.freq,
                                 inputData.excitation.exctDuration, inputData.excitation.anlyDuration)

        self.h2_config = 'Configurações'

        self.configData = """Método: {}
Passo de tempo: {} s
Deslocamento inicial: {} m
Velocidade inicial: {} m
Taxa de amortecimento da estrutura: {}
Massa específica do líquido: {} (kg/m3)
Viscosidade cinemática: {} (m²/s)
Aceleração da gravidade: {} (m/s²)""".format(inputData.configurations.method, inputData.configurations.timeStep,
                                             inputData.configurations.initialDisplacement,
                                             inputData.configurations.initialVelocity,
                                             inputData.configurations.relativeDampingRatio,
                                             inputData.configurations.liquidSpecificMass,
                                             inputData.configurations.kineticViscosity,
                                             inputData.configurations.gravity)

        self.h1_matrices = 'Equação de Movimento'

        self.equation = '[M]{a} + [C]{v} + [k]{x} = {F(t)}'

        self.h2_M = 'Matriz de Massa ([M] em kg)'

        self.h2_C = 'Matriz de Amortecimento ([C] em kg/s)'

        self.h2_K = 'Matriz de Rigidez ([K] em N/m)'

        self.h2_F = 'Vetor de Força em função do Tempo ({F(t)} em N)'

        self.h1_dynResp = 'Resposta Dinâmica'

        self.dmf = 'Fator de amplificação dinâmica (DMF): {:.2f}'.format(outputData.DMF)

        self.plot = "Vide gráficos na aba Resposta Dinâmica"

        # In-app report assembly
        report = """{}
---------------------------------------------------------------------------------------

### {} ###

# {}

{}

{}# {}

{}

# {}

{}

# {}

{}

### {} ###

{}

{}
{}

{}
{}

{}
{}

{}
{}

### {} ###

{}
{}

        """.format(self.title, self.h1_vars,
                   self.h2_struct, self.struct_num, self.storiesData,
                   self.h2_TLCD, self.tlcdData,
                   self.h2_exct, self.exctData,
                   self.h2_config, self.configData,
                   self.h1_matrices, self.equation,
                   self.h2_M, outputData.massMatrix,
                   self.h2_C, outputData.dampingMatrix,
                   self.h2_K, outputData.stiffnessMatrix,
                   self.h2_F, outputData.forceMatrix,
                   self.h1_dynResp, self.dmf, self.plot)

        self.te1.setText(report)


class DynRespTab(QWidget):
    def __init__(self, parent):
        super(DynRespTab, self).__init__(parent)

        self.label1 = QLabel('Lista geral de graus de liberdade', self)
        self.label2 = QLabel('Lista de graus de liberdade a serem plotados', self)
        self.list1 = QListWidget(self)
        self.list2 = QListWidget(self)
        self.addButton = QPushButton('+', self)
        self.addButton.clicked.connect(self.add_list2_item)
        self.removeButton = QPushButton('-', self)
        self.removeButton.clicked.connect(self.remove_list2_item)
        self.buttonsSpacer = QSpacerItem(20, 40, QSizePolicy.Minimum, QSizePolicy.Expanding)

        self.midButtonsLayout = QVBoxLayout()
        self.midButtonsLayout.addWidget(self.addButton)
        self.midButtonsLayout.addWidget(self.removeButton)
        self.midButtonsLayout.addSpacerItem(self.buttonsSpacer)

        self.formMid = QGridLayout()
        self.formMid.addWidget(self.label1, 1, 1)
        self.formMid.addWidget(self.label2, 1, 3)
        self.formMid.addWidget(self.list1, 2, 1)
        self.formMid.addLayout(self.midButtonsLayout, 2, 2)
        self.formMid.addWidget(self.list2, 2, 3)

        self.plotTypeLabel = QLabel('Tipo de gráfico:', self)

        self.plotTypeCombox = QComboBox(self)
        self.plotTypeCombox.addItem('Deslocamento')
        self.plotTypeCombox.addItem('Velocidade')
        self.plotTypeCombox.addItem('Aceleração')

        self.plotButton = QPushButton('Plotar', self)
        self.plotButton.clicked.connect(self.plot_dyn_resp)
        self.infSpacer = QSpacerItem(20, 40, QSizePolicy.Expanding, QSizePolicy.Minimum)

        self.formInf = QHBoxLayout()
        self.formInf.addWidget(self.plotTypeLabel)
        self.formInf.addWidget(self.plotTypeCombox)
        self.formInf.addSpacerItem(self.infSpacer)
        self.formInf.addWidget(self.plotButton)

        self.form = QVBoxLayout()
        self.form.addLayout(self.formMid, 1)
        self.form.addLayout(self.formInf, 1)

        self.dynRespCanvas = PltCanvas()
        self.mpl_toolbar = NavigationToolbar(self.dynRespCanvas, self)
        self.gridLabel = QLabel('Mostrar Grade', self)
        self.gridChkBox = QCheckBox(self)
        self.gridChkBox.stateChanged.connect(self.grid_change)

        self.canvas = QGridLayout()
        self.canvas.addWidget(self.dynRespCanvas, 1, 1, 1, 3)
        self.canvas.addWidget(self.gridLabel, 2, 1)
        self.canvas.addWidget(self.gridChkBox, 2, 2)
        self.canvas.addWidget(self.mpl_toolbar, 2, 3)

        self.grid = QHBoxLayout()
        self.grid.addLayout(self.form, 8)
        self.grid.addLayout(self.canvas, 10)
        self.setLayout(self.grid)

    def grid_change(self):
        """ Toggles plot grid on and off

        :return: None
        """
        self.dynRespCanvas.axes.grid(self.gridChkBox.isChecked())
        self.dynRespCanvas.draw()

    def add_list1_items(self):
        """ Adds all stories and the TLCD to list 1. Takes from inputData.

        :return: None
        """
        self.list1.clear()

        for i in inputData.stories.keys():
            self.list1.addItem('Pavimento {}'.format(i))

        self.list1.addItem('TLCD')

    def add_list2_item(self):
        """ Adds the item selected on list 1 to list 2 without making duplicates. If successfull, advances one row on
        list 1 and sorts list 2 alphabetically.

        :return: None
        """
        try:
            item = get_text(self.list1)
            row = self.list1.row(self.list1.currentItem())
        except AttributeError:
            return

        if not self.list2.findItems(item, Qt.MatchExactly):
            self.list2.addItem(item)

        if row < self.list1.count() - 1:
            self.list1.setCurrentRow(row + 1)
        self.list2.sortItems(Qt.AscendingOrder)

    def remove_list2_item(self):
        """ Removes the selected item from list 2

        :return: None
        """
        item = self.list2.currentItem()
        self.list2.takeItem(self.list2.row(item))

    def plot_dyn_resp(self):
        """ Reads the plot type and the QListWidget of DOFs to plot. Makes a list of DOFs to plot and send
        outputData.dynamicResponse and plotList to plot_displacement

        :return:
        """
        plotType = get_text(self.plotTypeCombox)
        plotList = []

        for i in range(self.list1.count()):
            self.list1.setCurrentRow(i)
            item = get_text(self.list1)
            if not self.list2.findItems(item, Qt.MatchExactly):
                plotList.append((get_text(self.list1), False))
            else:
                plotList.append((get_text(self.list1), True))

        if plotType == 'Deslocamento':
            self.dynRespCanvas.plot_displacement(outputData.dynamicResponse, plotList)
        elif plotType == 'Velocidade':
            self.dynRespCanvas.plot_velocity(outputData.dynamicResponse, plotList)
        elif plotType == 'Aceleração':
            self.dynRespCanvas.plot_acceleration(outputData.dynamicResponse, plotList)


class DMFTab(QWidget):
    def __init__(self, parent):
        super(DMFTab, self).__init__(parent)

        self.dmfCanvas = PltCanvas()
        self.mpl_toolbar = NavigationToolbar(self.dmfCanvas, self)
        self.gridLabel = QLabel('Mostrar Grade', self)
        self.gridChkBox = QCheckBox(self)
        self.gridChkBox.stateChanged.connect(self.grid_change)

        self.canvas = QGridLayout()
        self.canvas.addWidget(self.dmfCanvas, 1, 1, 1, 3)
        self.canvas.addWidget(self.gridLabel, 2, 1)
        self.canvas.addWidget(self.gridChkBox, 2, 2)
        self.canvas.addWidget(self.mpl_toolbar, 2, 3)

        self.holdLabel = QLabel(self)
        self.holdCheckBox = QCheckBox('Manter curvas do gráfico: ', self)
        self.holdCheckBox.stateChanged.connect(self.dmfCanvas.axes.hold)
        self.clearButton = QPushButton('Limpar o gráfico', self)
        self.clearButton.clicked.connect(self.dmfCanvas.reset_canvas)
        self.progressBar = QProgressBar(self)
        self.progressBar.setValue(0)

        self.form = QGridLayout()
        self.form.addWidget(self.progressBar, 1, 1)
        self.form.addWidget(self.holdLabel, 1, 2)
        self.form.addWidget(self.holdCheckBox, 1, 3)
        self.form.addWidget(self.clearButton, 3, 1, 1, 3)

        self.grid = QGridLayout()
        self.grid.addLayout(self.form, 1, 1)
        self.grid.addLayout(self.canvas, 1, 2)
        self.setLayout(self.grid)

    def grid_change(self):
        """ Toggles plot grid on and off

        :return: None
        """
        self.dmfCanvas.axes.grid(self.gridChkBox.isChecked())
        self.dmfCanvas.draw()


class AnimationTab(QWidget):
    def __init__(self, parent):
        super(AnimationTab, self).__init__(parent)
        self.le1 = QLineEdit(self)

        self.animationCanvas = AnimationCanvas(self)

        self.form = QGridLayout()
        self.form.addWidget(self.le1, 1, 1)

        self.grid = QGridLayout()
        self.grid.addLayout(self.form, 1, 1)
        self.grid.addWidget(self.animationCanvas, 1, 2)
        self.setLayout(self.grid)


def main():
    app = QApplication(sys.argv)
    GUI = MainWindow()
    sys.exit(app.exec_())


if __name__ == '__main__':
    main()
