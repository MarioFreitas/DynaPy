"""
Script name: TLCD Analyser GUI
Author: Mario Raul Freitas

This script contains the Graphical User Interface code for the TLCD Analyser software.
It utilises PyQt5 as the GUI framework.
This is the main script of the project and will be used to generate the .exe file for
distribution.
"""
from PyQt5.QtCore import *
from PyQt5.QtGui import *
from PyQt5.QtWidgets import *
from matplotlib.backends.backend_qt4agg import NavigationToolbar2QT as NavigationToolbar
import numpy as np
import sys
from DynaPy.TLCD.GUI.mainWindowGUI import Ui_MainWindow
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

        outputData_ = OutputData(mass, damping, stiffness, force, self.inputData.configurations)
        self.mySignal.emit(outputData_)


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
            percentageDone = (j + 1) / totalIter * 100
            self.percentageSignal.emit(percentageDone)
        self.mySignal.emit(dmfList)

    def simulation(self, inputData_, relativeFrequency):
        inputData_.excitation.frequencyInput = relativeFrequency
        inputData_.excitation.relativeFrequency = True
        inputData_.excitation.calc_frequency()

        mass = assemble_mass_matrix(inputData_.stories, inputData_.tlcd)
        damping = assemble_damping_matrix(inputData_.stories, inputData_.tlcd)
        stiffness = assemble_stiffness_matrix(inputData_.stories, inputData_.tlcd)
        force = assemble_force_matrix(inputData_.excitation, mass, inputData_.configurations)

        outputData = OutputData(mass, damping, stiffness, force, inputData_.configurations)
        return outputData.DMF


class MainWindow(QMainWindow, Ui_MainWindow):
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

        # Setup GUI
        self.setupUi(self)
        self.setWindowIcon(QIcon(None))
        self.setGeometry(100, 100, 800, 600)
        # with open('./GUI/styleSheet.qss', 'r') as css:
        #     self.setStyleSheet(css.read())

        # Declare save file
        self.fileName = None

        # Connect Actions
        self.actionNewFile.triggered.connect(self.new_file)
        self.actionOpenFile.triggered.connect(self.open_file)
        self.actionSaveFile.triggered.connect(self.save_file)
        self.actionSaveAs.triggered.connect(self.save_file_as)
        self.actionQuit.triggered.connect(self.close)
        self.actionFiniteDifferenceMethod.triggered.connect(self.set_method_mdf)
        self.actionLinearAccelerationMethod.triggered.connect(self.set_method_lin_accel)
        self.actionStepSize.triggered.connect(self.time_step)
        self.actionBoundaryConditions.triggered.connect(self.boundary_conditions)
        self.actionStructureDamping.triggered.connect(self.structure_damping)
        self.actionFluidParameters.triggered.connect(self.fluid_parameters)
        self.actionRunDynamicResponse.triggered.connect(self.run_simulation)
        self.actionDynamicMagnificationFactor.triggered.connect(self.run_set_of_simulations)
        self.actionMaximize.triggered.connect(self.showMaximized)
        self.actionFullScreen.triggered.connect(self.toggle_full_screen)
        self.actionAbout.triggered.connect(self.about)
        self.actionDevelopmentTool.triggered.connect(self.dev_tool)

        # TODO Implement export, optimize and animation actions
        self.actionExportAnimation.setDisabled(True)
        self.actionExportReport.setDisabled(True)
        self.actionOptimization.setDisabled(True)
        self.actionAnimation.setDisabled(True)

        # Structure Canvas
        self.structureWidget.structureCanvas = StructureCanvas(self.structureWidget)
        self.structureWidget.grid = QGridLayout()
        self.structureWidget.grid.addWidget(self.structureWidget.structureCanvas, 1, 1)
        self.structureWidget.setLayout(self.structureWidget.grid)

        # TLCD Canvas
        self.tlcdWidget.tlcdCanvas = TLCDCanvas(self.tlcdWidget)
        self.tlcdWidget.grid = QGridLayout()
        self.tlcdWidget.grid.addWidget(self.tlcdWidget.tlcdCanvas, 1, 1)
        self.tlcdWidget.setLayout(self.tlcdWidget.grid)

        # Excitation Canvas
        self.excitationWidget.excitationCanvas = PltCanvas()
        self.excitationWidget.mpl_toolbar = NavigationToolbar(self.excitationWidget.excitationCanvas, self)
        self.excitationWidget.gridLabel = QLabel('Show Grid', self)
        self.excitationWidget.gridChkBox = QCheckBox(self)
        self.excitationWidget.gridChkBox.stateChanged.connect(self.excitation_grid_toggle)

        self.excitationWidget.gridLayout = QGridLayout()
        self.excitationWidget.gridLayout.addWidget(self.excitationWidget.excitationCanvas, 1, 1, 1, 3)
        self.excitationWidget.gridLayout.addWidget(self.excitationWidget.gridLabel, 2, 1)
        self.excitationWidget.gridLayout.addWidget(self.excitationWidget.gridChkBox, 2, 2)
        self.excitationWidget.gridLayout.addWidget(self.excitationWidget.mpl_toolbar, 2, 3)

        self.excitationWidget.setLayout(self.excitationWidget.gridLayout)

        # Dynamic Response Canvas
        self.dynRespWidget.dynRespCanvas = PltCanvas()
        self.dynRespWidget.mpl_toolbar = NavigationToolbar(self.dynRespWidget.dynRespCanvas, self)
        self.dynRespWidget.gridLabel = QLabel('Show Grid', self)
        self.dynRespWidget.gridChkBox = QCheckBox(self)
        self.dynRespWidget.gridChkBox.stateChanged.connect(self.dynamic_response_grid_toggle)

        self.dynRespWidget.gridLayout = QGridLayout()
        self.dynRespWidget.gridLayout.addWidget(self.dynRespWidget.dynRespCanvas, 1, 1, 1, 3)
        self.dynRespWidget.gridLayout.addWidget(self.dynRespWidget.gridLabel, 2, 1)
        self.dynRespWidget.gridLayout.addWidget(self.dynRespWidget.gridChkBox, 2, 2)
        self.dynRespWidget.gridLayout.addWidget(self.dynRespWidget.mpl_toolbar, 2, 3)

        self.dynRespWidget.setLayout(self.dynRespWidget.gridLayout)

        # DMF Canvas
        self.dmfWidget.dmfCanvas = PltCanvas()
        # self.dmfWidget.setMinimumWidth(700)
        self.dmfWidget.mpl_toolbar = NavigationToolbar(self.dmfWidget.dmfCanvas, self)
        self.dmfWidget.gridLabel = QLabel('Show Grid', self)
        self.dmfWidget.gridChkBox = QCheckBox(self)
        self.dmfWidget.gridChkBox.stateChanged.connect(self.dmf_grid_toggle)

        self.dmfWidget.canvas = QGridLayout()
        self.dmfWidget.canvas.addWidget(self.dmfWidget.dmfCanvas, 1, 1, 1, 4)
        self.dmfWidget.canvas.addWidget(self.dmfWidget.gridLabel, 2, 1)
        self.dmfWidget.canvas.addWidget(self.dmfWidget.gridChkBox, 2, 2)
        self.dmfWidget.canvas.addWidget(self.dmfWidget.mpl_toolbar, 2, 3)
        self.dmfWidget.setLayout(self.dmfWidget.canvas)

        self.holdPlotCheckBox.stateChanged.connect(self.dmfWidget.dmfCanvas.axes.hold)
        self.cleanPlotButton.clicked.connect(self.dmfWidget.dmfCanvas.reset_canvas)

        # Connect Buttons
        self.addStoryBtn.clicked.connect(self.add_story)
        self.removeStoryBtn.clicked.connect(self.remove_story)
        self.confirmTlcdBtn.clicked.connect(self.add_tlcd)
        self.confirmExcitationButton.clicked.connect(self.add_excitation)
        self.importExcitationButton.clicked.connect(self.import_excitation)
        self.generateExcitationButton.clicked.connect(self.generate_excitation)
        self.addToPlotButton.clicked.connect(self.dynamic_response_add_list2_item)
        self.removeFromPlotButton.clicked.connect(self.dynamic_response_remove_list2_item)
        self.plotButton.clicked.connect(self.plot_dyn_resp)

        # Connect ComboBoxes Value Changed
        self.storyNumberComboBox.currentIndexChanged.connect(self.set_structure_text_change)
        self.tlcdModelComboBox.currentIndexChanged.connect(self.change_tlcd_option)
        self.excitationTypeComboBox.currentIndexChanged.connect(self.excitation_type_change)

        # Connect Checkboxes
        self.sineFrequencyRatioCheckBox.stateChanged.connect(self.excitation_frequency_label_change)

        # Show GUI
        self.showMaximized()

    def new_file(self):
        """ Resets all GUI inputs, inputData variable and save file.

        :return: None
        """

        # Set stories combobox index to 0
        self.storyNumberComboBox.setCurrentIndex(0)

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
        for i in range(self.storyNumberComboBox.count() - 1, 0, -1):
            self.storyNumberComboBox.removeItem(i)
        self.storyMassLineEdit.setText('')
        self.storyHeightLineEdit.setText('')
        self.columnWidthLineEdit.setText('')
        self.columnDepthLineEdit.setText('')
        self.elasticityModuleLineEdit.setText('')
        self.structureWidget.structureCanvas.painter(inputData.stories)

        self.tlcdModelComboBox.setCurrentIndex(0)
        self.diameterSimpleTlcdLineEdit.setText('')
        self.waterLevelSimpleTlcdLineEdit.setText('')
        self.widthSimpleTlcdLineEdit.setText('')
        self.tlcdWidget.tlcdCanvas.painter(inputData.tlcd)

        self.excitationTypeComboBox.setCurrentIndex(0)
        self.sineAmplitudeLineEdit.setText('')
        self.sineFrequencyLineEdit.setText('')
        self.sineAnalysisDurationLineEdit.setText('')
        self.sineExcitationDurationLineEdit.setText('')
        self.sineFrequencyRatioCheckBox.setChecked(True)
        self.excitationWidget.excitationCanvas.plot_excitation([], [])
        self.excitationFileLineEdit.setText('')

        self.reportTextBrowser.setText("""Relatório ainda não gerado.
Preencha todos os dados e utilize o  comando "Calcular" para gerar o relatório.""")
        self.reportTextBrowser.setFont(QFont("Times", 14))

        self.list1.clear()
        self.list2.clear()
        self.dynRespWidget.dynRespCanvas.reset_canvas()

        self.actionExportReport.setDisabled(True)
        self.actionExportAnimation.setDisabled(True)

    def open_file(self, triggered=False, fileName=None):
        """ Calls self.new_file to reset everything. Then, brings a open file dialog box and save the directory to
        self.fileName. Reads the file send all data to inputData. Finally, set texts and plot figures to GUI.

        :return: None
        """
        if fileName is not None:
            self.fileName = fileName
        else:
            fileName = QFileDialog.getOpenFileName(self, 'Open File', './save', filter="DynaPy File (*.dpfl)")[0]
            if fileName == '':
                return None
            self.new_file()
            self.fileName = fileName
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
            self.storyNumberComboBox.addItem(str(i + 1))

        if tlcdData is not None:
            inputData.tlcd = TLCD(tlcdData[0], tlcdData[1], tlcdData[2], tlcdData[3])
        if excitationData[0] == 'Sine Wave':
            inputData.excitation = Excitation(excitationData[0], excitationData[1], excitationData[2],
                                              excitationData[3], excitationData[4], excitationData[5],
                                              inputData.stories, inputData.tlcd)
        elif excitationData[0] == 'General Excitation':
            inputData.excitation = Excitation(excitationData[0], t=excitationData[1], a=excitationData[2],
                                              fileName=excitationData[3],
                                              structure=inputData.stories, tlcd=inputData.tlcd)
        inputData.configurations = Configurations(configurationsData[0], configurationsData[1], configurationsData[2],
                                                  configurationsData[3], configurationsData[4], configurationsData[5],
                                                  configurationsData[6])

        self.set_structure_text_change()
        self.structureWidget.structureCanvas.painter(inputData.stories)

        if inputData.tlcd is None:
            tlcdTypeIndex = self.tlcdModelComboBox.findText('None')
            self.tlcdModelComboBox.setCurrentIndex(tlcdTypeIndex)
        elif inputData.tlcd.type == 'Basic TLCD':
            tlcdTypeIndex = self.tlcdModelComboBox.findText(str(inputData.tlcd.type))
            self.tlcdModelComboBox.setCurrentIndex(tlcdTypeIndex)
            self.diameterSimpleTlcdLineEdit.setText(str(inputData.tlcd.diameter * 100))
            self.widthSimpleTlcdLineEdit.setText(str(inputData.tlcd.width))
            self.waterLevelSimpleTlcdLineEdit.setText(str(inputData.tlcd.waterHeight * 100))
            self.tlcdWidget.tlcdCanvas.painter(inputData.tlcd)

        exctTypeIndex = self.excitationTypeComboBox.findText(str(inputData.excitation.type))
        self.excitationTypeComboBox.setCurrentIndex(exctTypeIndex)
        if inputData.excitation.type == 'Sine Wave':
            self.sineAmplitudeLineEdit.setText(str(inputData.excitation.amplitude))
            self.sineFrequencyLineEdit.setText(str(inputData.excitation.frequencyInput))
            self.sineExcitationDurationLineEdit.setText(str(inputData.excitation.exctDuration))
            self.sineAnalysisDurationLineEdit.setText(str(inputData.excitation.anlyDuration))
            self.sineFrequencyRatioCheckBox.setChecked(inputData.excitation.relativeFrequency)
            tAnly = np.arange(0, inputData.excitation.anlyDuration + inputData.configurations.timeStep,
                              inputData.configurations.timeStep)
            tExct = np.arange(0, inputData.excitation.exctDuration + inputData.configurations.timeStep,
                              inputData.configurations.timeStep)
            a = inputData.excitation.amplitude * np.sin(inputData.excitation.frequency * tExct)
            a = np.hstack((a, np.array([0 for i in range(len(tAnly) - len(tExct))])))
            self.excitationWidget.excitationCanvas.plot_excitation(tAnly, a)
        elif inputData.excitation.type == 'General Excitation':
            self.excitationFileLineEdit.setText(inputData.excitation.fileName)
            self.excitationWidget.excitationCanvas.plot_excitation(inputData.excitation.t_input,
                                                                                inputData.excitation.a_input)

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
        elif inputData.stories == {} or inputData.excitation is None:
            icon = QStyle.SP_MessageBoxWarning
            self.error03 = QMessageBox()
            self.error03.setText('Preencha e confirme todos os dados nas abas Estrutura, TLCD e Excitação antes ' +
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
                                                                            j.depth, j.E, j.support)})
            self.file.write('{}\n'.format(stories))

            self.file.write('\nTLCD: \n-------------------\n')
            tlcd = inputData.tlcd
            if tlcd is None:
                tlcdData = None
            else:
                tlcdData = (tlcd.type, tlcd.diameter, tlcd.width, tlcd.waterHeight)
            self.file.write('{}\n'.format(tlcdData))

            self.file.write('\nExcitation: \n-------------------\n')
            excitation = inputData.excitation
            if excitation.type == 'Sine Wave':
                excitationData = (excitation.type, excitation.amplitude, excitation.frequencyInput,
                                  excitation.relativeFrequency, excitation.exctDuration, excitation.anlyDuration)
            elif excitation.type == 'General Excitation':
                excitationData = (excitation.type, excitation.t_input, excitation.a_input, excitation.fileName)
            self.file.write('{}\n'.format(excitationData))

            self.file.write('\nConfigurations: \n-------------------\n')
            configurations = inputData.configurations
            configurationsData = (configurations.method, configurations.timeStep, configurations.initialDisplacement,
                                  configurations.initialVelocity, configurations.dampingRatio,
                                  configurations.liquidSpecificMass, configurations.kineticViscosity,
                                  configurations.gravity)
            self.file.write('{}\n'.format(configurationsData))

            self.file.close()

    def save_file_as(self):
        """ Brings a file save dialog box, saves the file directory to self.fileName and calls self.save_file()

        :return: None
        """
        self.fileName = QFileDialog.getSaveFileName(self, 'Salvar como', './save', filter="DynaPy File (*.dpfl)")[0]
        if self.fileName == '':
            self.fileName = None
            return
        self.setWindowTitle('Dynapy TLCD Analyser - [{}]'.format(self.fileName))
        self.save_file()

    def closeEvent(self, event):
        quit_msg = "Are you sure you want to exit the program?"
        reply = QMessageBox.question(self, 'Confirm Exit',
                                     quit_msg, QMessageBox.Yes, QMessageBox.No)

        if reply == QMessageBox.Yes:
            event.accept()
        else:
            event.ignore()

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

    def structure_damping(self):
        self.structureDampingDialog = QWidget()
        self.structureDampingDialog.grid = QGridLayout()
        self.structureDampingDialog.label = QLabel('Taxa de amortecimento da estrutura:', self)
        self.structureDampingDialog.le = QLineEdit(self)
        self.structureDampingDialog.le.setPlaceholderText('0.02')
        self.structureDampingDialog.le.setText(str(inputData.configurations.dampingRatio))
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
            inputData.configurations.dampingRatio = float(get_text(self.structureDampingDialog.le))
            self.structureDampingDialog.hide()
        except ValueError:
            icon = QStyle.SP_MessageBoxWarning
            self.error07 = QMessageBox()
            self.error07.setText('A taxa de amortecimento da estrutura deve ser um número real')
            self.error07.setWindowTitle('Erro 07')
            self.error07.setWindowIcon(self.error07.style().standardIcon(icon))
            self.error07.setIcon(QMessageBox.Warning)
            self.error07.show()

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
        self.actionFiniteDifferenceMethod.setChecked(True)
        self.actionLinearAccelerationMethod.setChecked(False)

    def set_method_lin_accel(self):
        self.actionFiniteDifferenceMethod.setChecked(False)
        self.actionLinearAccelerationMethod.setChecked(True)

    def run_simulation(self):
        if inputData.stories == {} or inputData.excitation is None:
            icon = QStyle.SP_MessageBoxWarning
            self.error04 = QMessageBox()
            self.error04.setText('Preencha e confirme todos os dados nas abas Estrutura, TLCD e Excitação antes ' +
                                 'de acionar a rotina de cálculo.')
            self.error04.setWindowTitle('Erro 04')
            self.error04.setWindowIcon(self.error04.style().standardIcon(icon))
            self.error04.setIcon(QMessageBox.Warning)
            self.error04.show()
        else:
            # Confirm tlcd
            self.add_tlcd()

            # Add the tlcd to the last story
            lastStory = inputData.stories[len(inputData.stories)]
            inputData.stories[len(inputData.stories)] = Story(lastStory.mass, lastStory.height, lastStory.width,
                                                              lastStory.depth, lastStory.E, lastStory.support,
                                                              inputData.tlcd)

            # Calculate the damping ratio of each story
            for i in inputData.stories.values():
                i.calc_damping_coefficient(inputData.configurations.dampingRatio)

            # Confirm excitation
            self.add_excitation()

            # Calculate response
            def process(outputSignal):
                global outputData
                outputData = outputSignal

                # Generate plot
                self.dynamic_response_add_list1_items()
                if inputData.tlcd is not None:
                    self.list1.setCurrentRow(self.list1.count() - 2)
                else:
                    self.list1.setCurrentRow(self.list1.count() - 1)
                self.dynamic_response_add_list2_item()
                self.plot_dyn_resp()

                # Generate report
                self.generate_report_dynamic_response()

            self.runSimulationThread = RunSimulationThread(inputData)
            self.runSimulationThread.mySignal.connect(process)
            self.runSimulationThread.start()

    def run_set_of_simulations(self):
        if inputData.stories == {} or inputData.excitation is None:
            icon = QStyle.SP_MessageBoxWarning
            self.error04 = QMessageBox()
            self.error04.setText('Preencha e confirme todos os dados nas abas Estrutura, TLCD e Excitação antes ' +
                                 'de acionar a rotina de cálculo.')
            self.error04.setWindowTitle('Erro 04')
            self.error04.setWindowIcon(self.error04.style().standardIcon(icon))
            self.error04.setIcon(QMessageBox.Warning)
            self.error04.show()
        else:
            # Confirm tlcd
            self.add_tlcd()

            # Add the tlcd to the last story
            lastStory = inputData.stories[len(inputData.stories)]
            inputData.stories[len(inputData.stories)] = Story(lastStory.mass, lastStory.height, lastStory.width,
                                                              lastStory.depth, lastStory.E, lastStory.support,
                                                              inputData.tlcd)

            # Calculate the damping ratio of each story
            for i in inputData.stories.values():
                i.calc_damping_coefficient(inputData.configurations.dampingRatio)

            # Confirm excitation
            self.add_excitation()

            relativeFrequencies = np.arange(0.01, 2.01, 0.01)

            def process(signalMessage):
                global DMFPlotList
                dmfList = signalMessage
                DMFPlotList = [relativeFrequencies, dmfList]
                self.dmfWidget.dmfCanvas.plot_dmf(relativeFrequencies, dmfList)

            self.runSetOfSimulationsThread = RunSetOfSimulationsThread(inputData, relativeFrequencies)
            self.runSetOfSimulationsThread.mySignal.connect(process)
            progressBar = self.dmfProgressBar
            self.runSetOfSimulationsThread.percentageSignal.connect(progressBar.setValue)
            self.runSetOfSimulationsThread.start()

    def toggle_full_screen(self):
        """
        Method that checks if application is on full screen or not and toggles state.
        :return: None
        """
        if self.isFullScreen():
            self.showMaximized()
        else:
            self.showFullScreen()

    def about(self):
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
        self.aboutmsg.exec_()
        # TODO Fix about text. Include icon, name, version, author, date and description.

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

        s = 'compare_anal_sol(1)'
        self.devDialog.textEdit.setText(s)

        self.devDialog.show()

    def dev_tool_exec(self):
        exec(get_text(self.devDialog.textEdit))

    # Structure Methods
    def add_story(self):
        storyNumber = int(get_text(self.storyNumberComboBox))  # integer
        mass = float(get_text(self.storyMassLineEdit)) * 1e3  # float (ton -> kg)
        height = float(get_text(self.storyHeightLineEdit))  # float (m -> m)
        width = float(get_text(self.columnWidthLineEdit))  # float (m -> m)
        depth = float(get_text(self.columnDepthLineEdit))  # float (m -> m)
        E = float(get_text(self.elasticityModuleLineEdit)) * 1e9  # float (GPa -> Pa)
        support = str(get_text(self.supportTypeComboBox))  # string

        story = Story(mass, height, width, depth, E, support)
        inputData.stories.update({storyNumber: story})
        self.structureWidget.structureCanvas.painter(inputData.stories)

        if self.storyNumberComboBox.currentIndex() + 1 == self.storyNumberComboBox.count():
            self.storyNumberComboBox.addItem(str(int(get_text(self.storyNumberComboBox)) + 1))
            self.storyNumberComboBox.setCurrentIndex(self.storyNumberComboBox.currentIndex() + 1)
        else:
            self.storyNumberComboBox.setCurrentIndex(self.storyNumberComboBox.currentIndex() + 1)

    def remove_story(self):
        if self.storyNumberComboBox.currentIndex() + 1 == self.storyNumberComboBox.count() - 1:
            storyNumber = int(get_text(self.storyNumberComboBox))
            inputData.stories.pop(storyNumber)
            self.storyNumberComboBox.removeItem(storyNumber)
            self.structureWidget.structureCanvas.painter(inputData.stories)
            if self.storyNumberComboBox.currentIndex() != 0:
                self.storyNumberComboBox.setCurrentIndex(self.storyNumberComboBox.currentIndex() - 1)
        else:
            icon = QStyle.SP_MessageBoxWarning
            self.msgRemoveStory = QMessageBox()
            self.msgRemoveStory.setText('Remova primeiro o último andar adicionado.')
            self.msgRemoveStory.setWindowTitle('Erro de Remoção')
            self.msgRemoveStory.setWindowIcon(self.msgRemoveStory.style().standardIcon(icon))
            self.msgRemoveStory.show()

    def set_structure_text_change(self):
        i = int(get_text(self.storyNumberComboBox))
        if i <= len(inputData.stories):
            self.storyMassLineEdit.setText(str(inputData.stories[i].mass / 1e3))
            self.storyHeightLineEdit.setText(str(inputData.stories[i].height))
            self.columnWidthLineEdit.setText(str(inputData.stories[i].width))
            self.columnDepthLineEdit.setText(str(inputData.stories[i].depth))
            self.elasticityModuleLineEdit.setText(str(inputData.stories[i].E / 1e9))
            self.supportTypeComboBox.setCurrentIndex(
                self.supportTypeComboBox.findText(str(inputData.stories[i].support)))

        else:
            self.storyMassLineEdit.setText(str(inputData.stories[i - 1].mass / 1e3))
            self.storyHeightLineEdit.setText(str(inputData.stories[i - 1].height))
            self.columnWidthLineEdit.setText(str(inputData.stories[i - 1].width))
            self.columnDepthLineEdit.setText(str(inputData.stories[i - 1].depth))
            self.elasticityModuleLineEdit.setText(str(inputData.stories[i - 1].E / 1e9))
            self.supportTypeComboBox.setCurrentIndex(
                self.supportTypeComboBox.findText(str(inputData.stories[i - 1].support)))

    # TLCD Methods
    def change_tlcd_option(self):
        tlcdType = get_text(self.tlcdModelComboBox)
        if tlcdType == 'None':
            self.tlcdStackedWidget.setCurrentIndex(0)
        elif tlcdType == 'Basic TLCD':
            self.tlcdStackedWidget.setCurrentIndex(1)

    def add_tlcd(self):
        inputData.tlcd = None
        tlcdType = get_text(self.tlcdModelComboBox)

        if tlcdType == 'Basic TLCD':
            diameter = float(get_text(self.diameterSimpleTlcdLineEdit)) / 100  # float (cm -> m)
            width = float(get_text(self.widthSimpleTlcdLineEdit)) / 100  # float (cm -> m)
            waterHeight = float(get_text(self.waterLevelSimpleTlcdLineEdit)) / 100  # float (cm -> m)
            tlcd = TLCD(tlcdType, diameter, width, waterHeight, configurations=inputData.configurations)
            inputData.tlcd = tlcd
            self.tlcdWidget.tlcdCanvas.painter(inputData.tlcd)
        else:
            self.tlcdWidget.tlcdCanvas.painter(None)

    # Excitation Methods
    def import_excitation(self):
        fileName = QFileDialog.getOpenFileName(self, 'Load File', './save/Excitations', filter="Text File (*.txt)")[0]
        self.excitationFileLineEdit.setText(fileName)

    def generate_excitation(self):
        pass

    def excitation_type_change(self):
        excitationType = get_text(self.excitationTypeComboBox)

        if excitationType == 'Sine Wave':
            self.excitationStackedWidget.setCurrentIndex(0)
        elif excitationType == 'General Excitation':
            self.excitationStackedWidget.setCurrentIndex(1)

    def excitation_frequency_label_change(self):
        if self.sineFrequencyRatioCheckBox.isChecked():
            self.sineFrequencyLabel.setText('Frequency Ratio: (decimal)')
            self.sineFrequencyLineEdit.setPlaceholderText('0.9')
        else:
            self.sineFrequencyLabel.setText('Frequency: (rad/s)')
            self.sineFrequencyLineEdit.setPlaceholderText('30')

    def add_excitation(self):
        exct_type = get_text(self.excitationTypeComboBox)

        if exct_type == 'Sine Wave':
            amplitude = float(get_text(self.sineAmplitudeLineEdit))
            frequency = float(get_text(self.sineFrequencyLineEdit))
            relativeFrequency = self.sineFrequencyRatioCheckBox.isChecked()
            exctDuration = float(get_text(self.sineExcitationDurationLineEdit))
            anlyDuration = float(get_text(self.sineAnalysisDurationLineEdit))

            if (relativeFrequency == True) and (inputData.stories == {}):
                icon = QStyle.SP_MessageBoxWarning
                self.error01 = QMessageBox()
                self.error01.setText('Para utilizar a opção de frequência relativa é necessário ' +
                                     'adicionar a estrutura e o TLCD previamente.')
                self.error01.setWindowTitle('Erro 01')
                self.error01.setWindowIcon(self.error01.style().standardIcon(icon))
                self.error01.setIcon(QMessageBox.Warning)
                self.error01.exec()
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

                tAnly = np.arange(0, anlyDuration + inputData.configurations.timeStep,
                                  inputData.configurations.timeStep)
                tExct = np.arange(0, exctDuration + inputData.configurations.timeStep,
                                  inputData.configurations.timeStep)
                a = amplitude * np.sin(excitation.frequency * tExct)
                a = np.hstack((a, np.array([0 for i in range(len(tAnly) - len(tExct))])))

                self.excitationWidget.excitationCanvas.plot_excitation(tAnly, a)
        elif exct_type == 'General Excitation':
            fileName = get_text(self.excitationFileLineEdit)
            file = open(fileName, 'r')
            unit = file.readline()
            lines = int(file.readline())
            g = inputData.configurations.gravity

            t = []
            a = []

            for i in range(lines):
                line = file.readline()
                line = line.split(', ')
                line[0] = float(line[0])
                line[1] = float(line[1])
                t.append(line[0])
                if unit == 'unit: g\n':
                    a.append(line[1] * g)
                elif unit == 'unit: m/s2\n':
                    a.append(line[1])

            excitation = Excitation(exct_type, t=t, a=a, structure=inputData.stories, tlcd=inputData.tlcd,
                                    fileName=fileName)
            inputData.excitation = excitation

            self.excitationWidget.excitationCanvas.plot_excitation(inputData.excitation.t_input, inputData.excitation.a_input)

    def excitation_grid_toggle(self):
        """ Toggles plot grid on and off

        :return: None
        """
        self.excitationWidget.excitationCanvas.axes.grid(self.excitationWidget.gridChkBox.isChecked())
        self.excitationWidget.excitationCanvas.draw()

    # Report Methods
    def generate_report_dynamic_response(self):
        title = "DynaPy TLCD Analyser - Report\nAnalysis of the System Structure-TLCD Under Single Excitation Case"

        h1_vars = "Input Variables"

        h2_struct = "Structure"

        struct_num = "Number of Stories: {}".format(len(inputData.stories))

        storiesTable = []

        for i in range(1, len(inputData.stories) + 1):
            storiesTable.append([i,
                                      inputData.stories[i].mass / 1000,
                                      inputData.stories[i].height,
                                      inputData.stories[i].width * 100,
                                      inputData.stories[i].depth * 100,
                                      inputData.stories[i].E / 1e9,
                                      inputData.stories[i].support])

        storiesData = ''

        for i in storiesTable:
            storiesData += """Story {}:
Mass: {} ton
Height: {} m
Column width: {} cm
Column depth: {} cm
Column Elasticity Module: {} GPa

""".format(i[0], i[1], i[2], i[3], i[4], i[5])

        h2_TLCD = 'TLCD'

        if inputData.tlcd is None:
            tlcdData = """Model: None"""
        elif inputData.tlcd.type == 'Basic TLCD':
            tlcdData = """Model: {}
Diameter: {} cm
Water level: {} cm
Width: {} m""".format(inputData.tlcd.type, inputData.tlcd.diameter * 100,
                        inputData.tlcd.waterHeight * 100, inputData.tlcd.width)

        h2_exct = 'Excitation'

        if inputData.excitation.type == 'Sine Wave':
            if inputData.excitation.relativeFrequency:
                freq = '{} * (last story natural frequency)'.format(
                    inputData.excitation.frequencyInput) + ' = {:.2f} rad/s'.format(inputData.excitation.frequency)
            else:
                freq = '{} rad/s'.format(inputData.excitation.frequency)
            exctData = """Excitation type: {}
Amplitude: {} m/s²
Frequency: {}
Excitation duration: {} s
Analysis duration: {} s""".format(inputData.excitation.type, inputData.excitation.amplitude, freq,
                                 inputData.excitation.exctDuration, inputData.excitation.anlyDuration)
        elif inputData.excitation.type == 'General Excitation':
            exctData = """Excitation type: {}
File: {}""".format(inputData.excitation.type, inputData.excitation.fileName)

        h2_config = 'Configurations'

        configData = """Method: {}
Time step: {} s
Initial displacement: {} m
Initial velocity: {} m
Structure damping ratio: {}
Fluid specific mass: {} (kg/m3)
Kinetic viscosity: {} (m²/s)
Gravity acceleration: {} (m/s²)""".format(inputData.configurations.method, inputData.configurations.timeStep,
                                             inputData.configurations.initialDisplacement,
                                             inputData.configurations.initialVelocity,
                                             inputData.configurations.dampingRatio,
                                             inputData.configurations.liquidSpecificMass,
                                             inputData.configurations.kineticViscosity,
                                             inputData.configurations.gravity)

        h1_matrices = 'Movement Equation'

        equation = '[M]{a} + [C]{v} + [k]{x} = {F(t)}'

        h2_M = 'Mass Matrix ([M] em kg)'

        h2_C = 'Damping Matrix ([C] em kg/s)'

        h2_K = 'Stiffness Matrix ([K] em N/m)'

        h2_F = 'Force Vector Over Time ({F(t)} em N)'

        h1_dynResp = 'Dynamic Response'

        dmf = 'Dynamic Magnification Ratio (DMF): {}'.format(outputData.DMF)

        plot = "See plots in Dynamic Response Tab"

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

        """.format(title, h1_vars,
                   h2_struct, struct_num, storiesData,
                   h2_TLCD, tlcdData,
                   h2_exct, exctData,
                   h2_config, configData,
                   h1_matrices, equation,
                   h2_M, outputData.massMatrix,
                   h2_C, outputData.dampingMatrix,
                   h2_K, outputData.stiffnessMatrix,
                   h2_F, outputData.forceMatrix,
                   h1_dynResp, dmf, plot)

        self.reportTextBrowser.setText(report)

    # Dynamic Response Methods
    def dynamic_response_grid_toggle(self):
        """ Toggles plot grid on and off

        :return: None
        """
        self.dynRespWidget.dynRespCanvas.axes.grid(self.dynRespWidget.gridChkBox.isChecked())
        self.dynRespWidget.dynRespCanvas.draw()

    def dynamic_response_add_list1_items(self):
        """ Adds all stories and the TLCD to list 1. Takes from inputData.

        :return: None
        """
        self.list1.clear()

        for i in inputData.stories.keys():
            self.list1.addItem('Story {}'.format(i))

        if inputData.tlcd is not None:
            self.list1.addItem('TLCD')

    def dynamic_response_add_list2_item(self):
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

    def dynamic_response_remove_list2_item(self):
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
        plotType = get_text(self.plotTypeComboBox)
        plotList = []

        for i in range(self.list1.count()):
            self.list1.setCurrentRow(i)
            item = get_text(self.list1)
            if not self.list2.findItems(item, Qt.MatchExactly):
                plotList.append((get_text(self.list1), False))
            else:
                plotList.append((get_text(self.list1), True))

        if plotType == 'Displacement':
            self.dynRespWidget.dynRespCanvas.plot_displacement(outputData.dynamicResponse, plotList)
        elif plotType == 'Velocity':
            self.dynRespWidget.dynRespCanvas.plot_velocity(outputData.dynamicResponse, plotList)
        elif plotType == 'Acceleration':
            self.dynRespWidget.dynRespCanvas.plot_acceleration(outputData.dynamicResponse, plotList)

    # DMF Methods
    def dmf_grid_toggle(self):
        """ Toggles plot grid on and off

        :return: None
        """
        self.dmfWidget.dmfCanvas.axes.grid(self.dmfWidget.gridChkBox.isChecked())
        self.dmfWidget.dmfCanvas.draw()


def main():
    app = QApplication(sys.argv)
    GUI = MainWindow()
    if debugOption:
        # DEBUG OPTION - LOAD IMMEDIATELY
        # fileName = './save/Validations/Caso 1 (1 andar sem amort).dpfl'
        fileName = './save/Validations/Caso 1 (1 andar sem amort).dpfl'
        GUI.open_file(fileName=fileName)
        # GUI.add_story()
        # GUI.add_excitation()
        GUI.run_simulation()
    sys.exit(app.exec_())


def compare_anal_sol(case):
    if case == 1:
        """
        1 andar, vibração forçada ou livre, com ou sem amortecimento da estrutura e sem tlcd.
        qualquer frequência, qualquer CC
        """
        m = inputData.stories[1].mass
        # c = 0
        k = 24 * 25e9 * (0.35 * 0.35 ** 3 / 12) / (3 ** 3)  # 24EI/L^3 (engastado-engastado)
        # print(m, c, k)
        omega_n = np.sqrt(k / m)
        ksi = inputData.configurations.dampingRatio  # c/(2*m*omega_n)
        omega_d = omega_n * np.sqrt(1 - ksi ** 2)

        amplitude = inputData.excitation.amplitude
        p0 = amplitude * m
        frequencyInput = inputData.excitation.frequencyInput
        omega = frequencyInput * omega_n  # ressonância

        C = (p0 / k) * (
            (1 - (omega / omega_n) ** 2) / ((1 - (omega / omega_n) ** 2) ** 2 + (2 * ksi * (omega / omega_n)) ** 2))
        D = (p0 / k) * (
            (-2 * ksi * (omega / omega_n)) / ((1 - (omega / omega_n) ** 2) ** 2 + (2 * ksi * (omega / omega_n)) ** 2))

        x0 = inputData.configurations.initialDisplacement
        x10 = inputData.configurations.initialVelocity
        # print(x0, x10)
        A = x0 - D  # x(0) = 0
        B = (x10 + ksi * omega_n * A - omega * C) / omega_d  # x'(0) = 0

        t = np.linspace(0, 3, 2000)
        x = np.exp(-ksi * omega_n * t) * (A * np.cos(omega_d * t) + B * np.sin(omega_d * t)) + C * np.sin(
            omega * t) + D * np.cos(omega * t)
        dmf = (max(list(x))) / (p0 / k)
        # print(dmf)

        t_num = outputData.dynamicResponse.t
        x_num = outputData.dynamicResponse.x[0, :].A1
        plt.plot(t, x, '-r', label='Solução Analítica')
        plt.plot(t_num, x_num, '-b', label='Solução Numérica')
        plt.legend()
        plt.title('Deslocamento em Função do Tempo')
        plt.xlabel('t (s)')
        plt.ylabel('x (m)')
        plt.show()

    elif case == 2:
        # Calculate the damping ratio of each story
        ksi = [0.02, 0.03, 0.044, 0.052]
        for i, j in zip(inputData.stories.values(), ksi):
            i.calc_damping_coefficient(j)

        mass = assemble_mass_matrix(inputData.stories, inputData.tlcd)
        damping = assemble_damping_matrix(inputData.stories, inputData.tlcd)
        stiffness = assemble_stiffness_matrix(inputData.stories, inputData.tlcd)
        force = assemble_force_matrix(inputData.excitation, mass, inputData.configurations)

        outputData_ = OutputData(mass, damping, stiffness, force, inputData.configurations)

        from matplotlib.figure import Figure

        t_num = outputData_.dynamicResponse.t
        x_num = outputData_.dynamicResponse.x[3, :].A1
        v_num = outputData_.dynamicResponse.v[3, :].A1
        a_num = outputData_.dynamicResponse.a[3, :].A1

        plt.plot(t_num, a_num, '-b', label='Solução Numérica')
        plt.legend()
        plt.title('Deslocamento em Função do Tempo')
        plt.xlabel('t (s)')
        plt.ylabel('x (m)')
        plt.grid()
        plt.show()


if __name__ == '__main__':
    main()
