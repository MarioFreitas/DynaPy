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
import re
import os
from DynaPy.TLCD.GUI.mainWindowGUI import Ui_MainWindow
from DynaPy.TLCD.GUI.DpInputData import InputData
from DynaPy.TLCD.GUI.DpConfigurations import Configurations
from DynaPy.TLCD.GUI.DpOutputData import OutputData
from DynaPy.TLCD.GUI.DpOutputDMF import OutputDMF
from DynaPy.TLCD.GUI.DpStory import Story
from DynaPy.TLCD.GUI.DpTLCD import TLCD
from DynaPy.TLCD.GUI.DpExcitation import Excitation
from DynaPy.TLCD.GUI.DpPltCanvas import PltCanvas
from DynaPy.TLCD.GUI.DpStructureCanvas import StructureCanvas
from DynaPy.TLCD.GUI.DpTLCDCanvas import TLCDCanvas
from DynaPy.TLCD.GUI.DpAnimationCanvas import AnimationCanvas
from DynaPy.TLCD.excitationGenerator import MainWindow as ExcitationGenerator
from DynaPy.lib import get_text
from DynaPy.DynaSolver import *

inputData = InputData()
inputData.configurations = Configurations()

outputData = None
outputDMF = None

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

    def __init__(self, inputData_, frequencies, parent=None):
        super(RunSetOfSimulationsThread, self).__init__(parent)
        self.inputData = inputData_
        self.frequencies = frequencies

    def run(self):
        displacmentList = []
        dmfList = []
        totalIter = len(self.frequencies)

        self.mass = assemble_mass_matrix(self.inputData.stories, self.inputData.tlcd)
        self.damping = assemble_damping_matrix(self.inputData.stories, self.inputData.tlcd)
        self.stiffness = assemble_stiffness_matrix(self.inputData.stories, self.inputData.tlcd)

        for i, j in zip(self.frequencies, range(len(self.frequencies))):
            resp = self.simulation(self.inputData, i)
            x = resp[0]
            dmf = resp[1]
            displacmentList.append(x)
            dmfList.append(dmf)

            percentageDone = (j + 1) / totalIter * 100
            self.percentageSignal.emit(percentageDone)
        signal = [self.frequencies, displacmentList, dmfList]
        self.mySignal.emit(signal)

    def simulation(self, inputData_, frequency):
        inputData_.excitation.frequencyInput = frequency
        inputData_.excitation.relativeFrequency = False
        inputData_.excitation.calc_frequency()

        force = assemble_force_matrix(inputData_.excitation, self.mass, inputData_.configurations)

        outputData_ = OutputData(self.mass, self.damping, self.stiffness, force, inputData_.configurations)
        return [outputData_.maxDisplacement, outputData_.DMF]


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
        self.setWindowIcon(QIcon('icon_64.ico'))
        self.setGeometry(100, 100, 800, 600)
        self.statusBar()
        self.dark_blue_theme()

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
        self.actionDMFSettings.triggered.connect(self.dmf_settings)
        self.actionRunDynamicResponse.triggered.connect(self.run_dynamic_response)
        self.actionDynamicMagnificationFactor.triggered.connect(self.run_dmf)

        # (Themes)
        self.actionAqua.triggered.connect(self.aqua_theme)
        self.actionBasicWhite.triggered.connect(self.basic_white_theme)
        self.actionBlueGlass.triggered.connect(self.blue_glass_theme)
        self.actionDarcula.triggered.connect(self.darcula_theme)
        self.actionDark.triggered.connect(self.dark_theme)
        self.actionDarkBlue.triggered.connect(self.dark_blue_theme)
        self.actionDarkBlueFreeCAD.triggered.connect(self.dark_blue_freeCad_theme)
        self.actionDarkGreen.triggered.connect(self.dark_green_theme)
        self.actionDarkGreenFreeCAD.triggered.connect(self.dark_green_freeCad_theme)
        self.actionDarkOrange.triggered.connect(self.dark_orange_theme)
        self.actionDarkOrangeFreeCAD.triggered.connect(self.dark_orange_freeCad_theme)
        self.actionLight.triggered.connect(self.light_theme)
        self.actionLightBlueFreeCAD.triggered.connect(self.light_blue_freeCad_theme)
        self.actionLightGreenFreeCAD.triggered.connect(self.light_green_freeCad_theme)
        self.actionLightOrangeFreeCAD.triggered.connect(self.light_orange_freeCad_theme)
        self.actionMachinery.triggered.connect(self.machinery_theme)
        self.actionMinimalist.triggered.connect(self.minimalist_theme)
        self.actionNightMapping.triggered.connect(self.night_mapping_theme)
        self.actionWombat.triggered.connect(self.wombat_theme)

        # Connect Actions (continued)
        self.actionMaximize.triggered.connect(self.showMaximized)
        self.actionFullScreen.triggered.connect(self.toggle_full_screen)
        self.actionAbout.triggered.connect(self.about)
        self.actionDevelopmentTool.triggered.connect(self.dev_tool)

        # TODO Implement export and optimize actions
        self.actionExportReport.setDisabled(True)
        self.actionOptimization.setDisabled(True)

        # Structure Canvas
        # self.splitter.setSizes([400, 400])
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
        self.dynRespWidget.exportBtn = QPushButton('Export CSV', self)
        self.dynRespWidget.gridLabel = QLabel('Show Grid', self)
        self.dynRespWidget.gridChkBox = QCheckBox(self)
        self.dynRespWidget.gridChkBox.stateChanged.connect(self.dynamic_response_grid_toggle)
        self.dynRespWidget.exportBtn.clicked.connect(self.dynamic_response_export_csv)

        self.dynRespWidget.gridLayout = QGridLayout()
        self.dynRespWidget.gridLayout.addWidget(self.dynRespWidget.dynRespCanvas, 1, 1, 1, 4)
        self.dynRespWidget.gridLayout.addWidget(self.dynRespWidget.gridLabel, 2, 1)
        self.dynRespWidget.gridLayout.addWidget(self.dynRespWidget.gridChkBox, 2, 2)
        self.dynRespWidget.gridLayout.addWidget(self.dynRespWidget.mpl_toolbar, 2, 3)
        self.dynRespWidget.gridLayout.addWidget(self.dynRespWidget.exportBtn, 2, 4)

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
        self.addToDMFPlot.clicked.connect(self.dmf_add_list4_item)
        self.removeFromDMFPlot.clicked.connect(self.dmf_remove_list4_item)
        self.dmfPlotButton.clicked.connect(self.plot_dmf)

        # Connect ComboBoxes Value Changed
        self.storyNumberComboBox.currentIndexChanged.connect(self.set_structure_text_change)
        self.tlcdModelComboBox.currentIndexChanged.connect(self.change_tlcd_option)
        self.excitationTypeComboBox.currentIndexChanged.connect(self.excitation_type_change)

        # Connect Checkboxes
        self.sineFrequencyRatioCheckBox.stateChanged.connect(self.excitation_frequency_label_change)

        # Show GUI
        self.showMaximized()

    def aqua_theme(self):
        self.check_theme('actionAqua')

    def basic_white_theme(self):
        self.check_theme('actionBasicWhite')

    def blue_glass_theme(self):
        self.check_theme('actionBlueGlass')

    def darcula_theme(self):
        self.check_theme('actionDarcula')

    def dark_theme(self):
        self.check_theme('actionDark')

    def dark_blue_theme(self):
        self.check_theme('actionDarkBlue')

    def dark_blue_freeCad_theme(self):
        self.check_theme('actionDarkBlueFreeCAD')

    def dark_green_theme(self):
        self.check_theme('actionDarkGreen')

    def dark_green_freeCad_theme(self):
        self.check_theme('actionDarkGreenFreeCAD')

    def dark_orange_theme(self):
        self.check_theme('actionDarkOrange')

    def dark_orange_freeCad_theme(self):
        self.check_theme('actionDarkOrangeFreeCAD')

    def light_theme(self):
        self.check_theme('actionLight')

    def light_blue_freeCad_theme(self):
        self.check_theme('actionLightBlueFreeCAD')

    def light_green_freeCad_theme(self):
        self.check_theme('actionLightGreenFreeCAD')

    def light_orange_freeCad_theme(self):
        self.check_theme('actionLightOrangeFreeCAD')

    def machinery_theme(self):
        self.check_theme('actionMachinery')

    def minimalist_theme(self):
        self.check_theme('actionMinimalist')

    def night_mapping_theme(self):
        self.check_theme('actionNightMapping')

    def wombat_theme(self):
        self.check_theme('actionWombat')

    def check_theme(self, theme):
        themes = {'actionAqua': './css/aqua/aqua.qss',
                  'actionBasicWhite': './css/basicWhite/basicWhite.qss',
                  'actionBlueGlass': './css/blueGlass/blueGlass.qss',
                  'actionDarcula': './css/darcula/darcula.qss',
                  'actionDark': './css/dark/darkstyle.qss',
                  'actionDarkBlue': './css/darkBlue/style.qss',
                  'actionDarkBlueFreeCAD': './css/darkBlue(FreeCAD)/stylesheet.qss',
                  'actionDarkGreen': './css/darkGreen/darkGreen.qss',
                  'actionDarkGreenFreeCAD': './css/darkGreen(FreeCAD)/stylesheet.qss',
                  'actionDarkOrange': './css/darkOrange/darkOrange.qss',
                  'actionDarkOrangeFreeCAD': './css/darkOrange(FreeCAD)/stylesheet.qss',
                  'actionLight': './css/light/light.qss',
                  'actionLightBlueFreeCAD': './css/lightBlue(FreeCAD)/stylesheet.qss',
                  'actionLightGreenFreeCAD': './css/lightGreen(FreeCAD)/stylesheet.qss',
                  'actionLightOrangeFreeCAD': './css/lightOrange(FreeCAD)/stylesheet.qss',
                  'actionMachinery': './css/machinery/machinery.qss',
                  'actionMinimalist': './css/minimalist/Minimalist.qss',
                  'actionNightMapping': './css/nightMapping/style.qss',
                  'actionWombat': './css/wombat/stylesheet.qss',
                  }
        for i in themes.keys():
            eval('self.{}.setChecked(False)'.format(i))

        eval('self.{}.setChecked(True)'.format(theme))
        qss = self.open_qss(themes[theme])
        # self.setStyleSheet(qss)
        app.setStyleSheet(qss)

    def open_qss(self, path):
        """
        opens a Qt stylesheet with a path relative to the project

        Note: it changes the urls in the Qt stylesheet (in memory), and makes these urls relative to the project
        Warning: the urls in the Qt stylesheet should have the forward slash ('/') as the pathname separator
        """
        with open(path) as f:
            qss = f.read()
            pattern = r'url\((.*?)\);'
            for url in sorted(set(re.findall(pattern, qss)), key=len, reverse=True):
                directory, basename = os.path.split(path)
                new_url = os.path.join(directory, *url.split('/'))
                new_url = os.path.normpath(new_url)
                new_url = new_url.replace(os.path.sep, '/')
                qss = qss.replace(url, new_url)
            return qss

    def new_file(self):
        """ Resets all GUI inputs, inputData variable and save file.

        :return: None
        """

        quit_msg = "This operation will erase all unsaved data. Are you sure you want to open a new file?"
        reply = QMessageBox.question(self, 'Confirm New File',
                                     quit_msg, QMessageBox.Yes, QMessageBox.No)

        if reply == QMessageBox.No:
            return

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
            self.widthSimpleTlcdLineEdit.setText(str(inputData.tlcd.width * 100))
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
            error03_title = "Error 03"
            error03_msg = "Fill in all data in the Structures, TLCD and Excitation tabs before saving."
            QMessageBox.warning(self, error03_title, error03_msg, QMessageBox.Ok)
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
        self.fileName = QFileDialog.getSaveFileName(self, 'Save as', './save', filter="DynaPy File (*.dpfl)")[0]
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
        self.timeStepDialog.setWindowIcon(QIcon('icon_64.ico'))
        self.timeStepDialog.grid = QGridLayout()
        self.timeStepDialog.label = QLabel('Time step: (s)', self)
        self.timeStepDialog.le = QLineEdit(self)
        self.timeStepDialog.le.setPlaceholderText('0.001')
        self.timeStepDialog.le.setText(str(inputData.configurations.timeStep))
        self.timeStepDialog.button = QPushButton('Ok', self)
        self.timeStepDialog.button.clicked.connect(self.time_step_config)
        self.timeStepDialog.grid.addWidget(self.timeStepDialog.label, 1, 1)
        self.timeStepDialog.grid.addWidget(self.timeStepDialog.le, 1, 2)
        self.timeStepDialog.grid.addWidget(self.timeStepDialog.button, 2, 1, 1, 2)
        self.timeStepDialog.setLayout(self.timeStepDialog.grid)
        self.timeStepDialog.setWindowTitle('Time Step Configuration')
        self.timeStepDialog.setGeometry(300, 300, 300, 200)
        self.timeStepDialog.show()

    def time_step_config(self):
        try:
            inputData.configurations.timeStep = float(get_text(self.timeStepDialog.le))
            self.timeStepDialog.hide()
        except ValueError:
            error05_title = "Error 05"
            error05_msg = "Time step must be a float."
            QMessageBox.warning(self, error05_title, error05_msg, QMessageBox.Ok)

    def boundary_conditions(self):
        self.boundaryConditionsDialog = QWidget()
        self.boundaryConditionsDialog.setWindowIcon(QIcon('icon_64.ico'))
        self.boundaryConditionsDialog.grid = QGridLayout()
        self.boundaryConditionsDialog.label1 = QLabel('Initial displacement: (m)')
        self.boundaryConditionsDialog.label2 = QLabel('Initial velocity: (m/s)')
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
        self.boundaryConditionsDialog.setWindowTitle('Boundary Conditions Configuration')
        self.boundaryConditionsDialog.setGeometry(300, 300, 300, 200)
        self.boundaryConditionsDialog.show()

    def boundary_conditions_config(self):
        try:
            inputData.configurations.initialDisplacement = float(get_text(self.boundaryConditionsDialog.le1))
            inputData.configurations.initialVelocity = float(get_text(self.boundaryConditionsDialog.le2))
            self.boundaryConditionsDialog.hide()
        except ValueError:
            error06_title = "Error 6"
            error06_msg = "Initial displacement and initial velocity must be float."
            QMessageBox.warning(self, error06_title, error06_msg, QMessageBox.Ok)

    def structure_damping(self):
        self.structureDampingDialog = QWidget()
        self.structureDampingDialog.setWindowIcon(QIcon('icon_64.ico'))
        self.structureDampingDialog.grid = QGridLayout()
        self.structureDampingDialog.label = QLabel('Structure damping ratio:', self)
        self.structureDampingDialog.le = QLineEdit(self)
        self.structureDampingDialog.le.setPlaceholderText('0.02')
        self.structureDampingDialog.le.setText(str(inputData.configurations.dampingRatio))
        self.structureDampingDialog.button = QPushButton('Ok', self)
        self.structureDampingDialog.button.clicked.connect(self.structure_damping_config)
        self.structureDampingDialog.grid.addWidget(self.structureDampingDialog.label, 1, 1)
        self.structureDampingDialog.grid.addWidget(self.structureDampingDialog.le, 1, 2)
        self.structureDampingDialog.grid.addWidget(self.structureDampingDialog.button, 2, 1, 1, 2)
        self.structureDampingDialog.setLayout(self.structureDampingDialog.grid)
        self.structureDampingDialog.setWindowTitle('Structure Damping Ratio Configuration')
        self.structureDampingDialog.setGeometry(300, 300, 300, 200)
        self.structureDampingDialog.show()

    def structure_damping_config(self):
        try:
            inputData.configurations.dampingRatio = float(get_text(self.structureDampingDialog.le))
            self.structureDampingDialog.hide()
        except ValueError:
            error07_title = "Error 07"
            error07_msg = "Structure damping ratio must be float."
            QMessageBox.warning(self, error07_title, error07_msg, QMessageBox.Ok)

    def fluid_parameters(self):
        self.fluidParametersDialog = QWidget()
        self.fluidParametersDialog.setWindowIcon(QIcon('icon_64.ico'))
        self.fluidParametersDialog.grid = QGridLayout()
        self.fluidParametersDialog.label1 = QLabel('Specific mass: (kg/m³)')
        self.fluidParametersDialog.label2 = QLabel('Kinetic viscosity: (m²/s)')
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
        self.fluidParametersDialog.setWindowTitle('Fluid Parameters Configuration')
        self.fluidParametersDialog.setGeometry(300, 300, 300, 200)
        self.fluidParametersDialog.show()

    def fluid_parameters_config(self):
        try:
            inputData.configurations.liquidSpecificMass = float(get_text(self.fluidParametersDialog.le1))
            inputData.configurations.kineticViscosity = float(get_text(self.fluidParametersDialog.le2))
            self.fluidParametersDialog.hide()
        except ValueError:
            error08_title = "Error 08"
            error08_msg = "Specific mass and kinetic viscosity must be float."
            QMessageBox.warning(self, error08_title, error08_msg, QMessageBox.Ok)

    def dmf_settings(self):
        self.dmfSettingsDialog = QWidget()
        self.dmfSettingsDialog.setWindowIcon(QIcon('icon_64.ico'))
        self.dmfSettingsDialog.grid = QGridLayout()
        self.dmfSettingsDialog.label1 = QLabel('Discretization points:')
        self.dmfSettingsDialog.label2 = QLabel('Upper limit factor: ')
        self.dmfSettingsDialog.le1 = QLineEdit(self)
        self.dmfSettingsDialog.le1.setPlaceholderText('200')
        self.dmfSettingsDialog.le1.setText(str(inputData.configurations.dmfDiscretizationPoints))
        self.dmfSettingsDialog.le2 = QLineEdit(self)
        self.dmfSettingsDialog.le2.setPlaceholderText('2')
        self.dmfSettingsDialog.le2.setText(str(inputData.configurations.dmfUpperLimitFactor))
        self.dmfSettingsDialog.btn = QPushButton('Ok', self)
        self.dmfSettingsDialog.btn.clicked.connect(self.dmf_settings_config)
        self.dmfSettingsDialog.grid.addWidget(self.dmfSettingsDialog.label1, 1, 1)
        self.dmfSettingsDialog.grid.addWidget(self.dmfSettingsDialog.label2, 2, 1)
        self.dmfSettingsDialog.grid.addWidget(self.dmfSettingsDialog.le1, 1, 2)
        self.dmfSettingsDialog.grid.addWidget(self.dmfSettingsDialog.le2, 2, 2)
        self.dmfSettingsDialog.grid.addWidget(self.dmfSettingsDialog.btn, 3, 1, 1, 2)
        self.dmfSettingsDialog.setLayout(self.dmfSettingsDialog.grid)
        self.dmfSettingsDialog.setWindowTitle('DMF Discretization Settings')
        self.dmfSettingsDialog.setGeometry(300, 300, 300, 200)
        self.dmfSettingsDialog.show()

    def dmf_settings_config(self):
        try:
            inputData.configurations.dmfDiscretizationPoints = int(get_text(self.dmfSettingsDialog.le1))
            inputData.configurations.dmfUpperLimitFactor = float(get_text(self.dmfSettingsDialog.le2))
            self.dmfSettingsDialog.hide()
        except ValueError:
            error10_title = "Error 10"
            error10_msg = "Discretization points must be int and Upper limit factor must be float."
            QMessageBox.warning(self, error10_title, error10_msg, QMessageBox.Ok)

    def set_method_mdf(self):
        self.actionFiniteDifferenceMethod.setChecked(True)
        self.actionLinearAccelerationMethod.setChecked(False)

    def set_method_lin_accel(self):
        self.actionFiniteDifferenceMethod.setChecked(False)
        self.actionLinearAccelerationMethod.setChecked(True)

    def run_dynamic_response(self):
        if inputData.stories == {} or inputData.excitation is None:
            error04A_title = "Error 04A"
            error04A_msg = "Fill in all data in Structure, TLCD and Excitation tabs before trying" + \
                           " to calculate dynamic response."
            QMessageBox.warning(self, error04A_title, error04A_msg, QMessageBox.Ok)
        else:
            # Confirm tlcd
            # self.add_tlcd()

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

    def run_dmf(self):
        if inputData.stories == {} or inputData.excitation is None:
            error04B_title = "Error 04B"
            error04B_msg = "Fill in all data in Structure, TLCD and Excitation tabs before trying" + \
                           " to calculate dynamic magnification factor."
            QMessageBox.warning(self, error04B_title, error04B_msg, QMessageBox.Ok)
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

            naturalFrequencies = []
            for i in inputData.stories.values():
                naturalFrequencies.append(i.naturalFrequency)

            n = inputData.configurations.dmfDiscretizationPoints
            upperFrequency = inputData.configurations.dmfUpperLimitFactor * max(naturalFrequencies)
            frequencies = np.linspace(0.0001, upperFrequency, n)

            def process(signalMessage):
                global outputDMF
                frequenciesList = signalMessage[0]
                displacementList = signalMessage[1]
                displacementList = np.mat(displacementList)
                dmfList = signalMessage[2]
                dmfList = np.mat(dmfList)
                outputDMF = OutputDMF(frequenciesList, displacementList, dmfList)

                # Generate plot
                self.dmf_add_list3_items()
                self.list3.setCurrentRow(self.list3.count() - 1)
                # if inputData.tlcd is not None:
                #     self.list3.setCurrentRow(self.list3.count() - 2)
                # else:
                #     self.list3.setCurrentRow(self.list3.count() - 1)
                self.dmf_add_list4_item()
                self.plot_dmf()

            self.runSetOfSimulationsThread = RunSetOfSimulationsThread(inputData, frequencies)
            self.runSetOfSimulationsThread.mySignal.connect(process)
            self.runSetOfSimulationsThread.percentageSignal.connect(self.dmfProgressBar.setValue)
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
        about_title = "DynaPy TLCD Analyser - Version 1.2.3"
        about_msg = "This software takes the input data of a shear-build equipped with a Tuned Liquid Column " + \
                    "Damper (TLCD) and calculates the dynamic response at each story. Furthermore, this software " + \
                    "is capable of making analysis for different frequencies, performing optimizations and making " + \
                    "animated representations of the structure. This software is intended for educational use. " + \
                    "The author does not take responsibility for any sort of misuse of the software or for its " + \
                    "results. The user of this software is responsible for any conclusion taken using " + \
                    "this software. There is no commitment or warranty implied in the use of the software"
        QMessageBox.information(self, about_title, about_msg, QMessageBox.Ok)
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

        s = 'compare_anal_sol(3)'
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
            error09_title = "Error 09"
            error09_msg = "Remove the last story first."
            QMessageBox.warning(self, error09_title, error09_msg, QMessageBox.Ok)

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
        elif tlcdType == 'Pressurized TLCD':
            self.tlcdStackedWidget.setCurrentIndex(2)

    def add_tlcd(self):
        inputData.tlcd = None
        tlcdType = get_text(self.tlcdModelComboBox)

        if tlcdType == 'Basic TLCD':
            diameter = float(get_text(self.diameterSimpleTlcdLineEdit)) / 100  # float (cm -> m)
            width = float(get_text(self.widthSimpleTlcdLineEdit)) / 100  # float (cm -> m)
            waterHeight = float(get_text(self.waterLevelSimpleTlcdLineEdit)) / 100  # float (cm -> m)
            amount = int(get_text(self.amountSimpleTlcdLineEdit))
            tlcd = TLCD(tlcdType, diameter, width, waterHeight,
                        configurations=inputData.configurations, amount=amount)
            inputData.tlcd = tlcd
            self.tlcdWidget.tlcdCanvas.painter(inputData.tlcd)
        elif tlcdType == 'Pressurized TLCD':
            diameter = float(get_text(self.diameterPressureTlcdLineEdit)) / 100  # float (cm -> m)
            width = float(get_text(self.widthPressureTlcdLineEdit)) / 100  # float (cm -> m)
            waterHeight = float(get_text(self.waterLevelPressureTlcdLineEdit)) / 100  # float (cm -> m)
            gasHeight = float(get_text(self.gasHeightPressureTlcdLineEdit)) / 100  # float (cm -> m)
            gasPressure = float(get_text(self.gasPressurePressureTlcdLineEdit)) * 101325  # float (atm -> Pa)
            amount = int(get_text(self.amountPressureTlcdLineEdit))
            tlcd = TLCD(tlcdType, diameter, width, waterHeight,
                        gasHeight=gasHeight, gasPressure=gasPressure,
                        configurations=inputData.configurations, amount=amount)
            inputData.tlcd = tlcd
            self.tlcdWidget.tlcdCanvas.painter(inputData.tlcd)
        else:
            self.tlcdWidget.tlcdCanvas.painter(None)

    # Excitation Methods
    def import_excitation(self):
        fileName = QFileDialog.getOpenFileName(self, 'Load File', './save/Excitations', filter="Text File (*.txt)")[0]
        self.excitationFileLineEdit.setText(fileName)
        self.confirmExcitationButton.click()

    def generate_excitation(self):
        fileName = get_text(self.excitationFileLineEdit)
        self.excitationGenerator = ExcitationGenerator(fileName=fileName)
        self.excitationGenerator.nameSignal.connect(self.excitationFileLineEdit.setText)
        self.excitationGenerator.nameSignal.connect(self.confirmExcitationButton.click)

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
                error01_title = "Error 01"
                error01_msg = "Structure and TLCD must be added before adding excitation with realtive frequency."
                QMessageBox.warning(self, error01_title, error01_msg, QMessageBox.Ok)
            elif anlyDuration < exctDuration:
                error02_title = "Error 02"
                error02_msg = "Analysis duration must be greater or equal to excitation duration."
                QMessageBox.warning(self, error02_title, error02_msg, QMessageBox.Ok)
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
            try:
                file = open(fileName, 'r')
            except FileNotFoundError:
                return
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

            self.excitationWidget.excitationCanvas.plot_excitation(inputData.excitation.t_input,
                                                                   inputData.excitation.a_input)

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
        elif inputData.tlcd.type == 'Pressurized TLCD':
            tlcdData = """Model: {}
Diameter: {} cm
Water level: {} cm
Width: {} m
Gas Height: {} cm
Gas Pressure: {} atm""".format(inputData.tlcd.type, inputData.tlcd.diameter * 100,
                               inputData.tlcd.waterHeight * 100, inputData.tlcd.width,
                               inputData.tlcd.gasHeight * 100, inputData.tlcd.gasPressure / 101325)

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

    def dynamic_response_export_csv(self):
        """ Exports CSV of the plotted data 

        :return: None
        """
        dataList = []

        plotList = []

        for i in range(self.list1.count()):
            self.list1.setCurrentRow(i)
            item = get_text(self.list1)
            if not self.list2.findItems(item, Qt.MatchExactly):
                plotList.append((get_text(self.list1), False))
            else:
                plotList.append((get_text(self.list1), True))

        t = outputData.dynamicResponse.t
        dataList.append(t)
        for i, j in plotList:
            if j:
                if i != 'TLCD':
                    n = int(i.split('Story ')[1]) - 1
                    x = outputData.dynamicResponse.x[n, :].A1
                else:
                    n = len(plotList) - 1
                    x = outputData.dynamicResponse.x[n, :].A1
                dataList.append(list(x))

        dataList = list(zip(*dataList))

        filename = QFileDialog.getSaveFileName(self, 'Save as', './save', filter="CSV File (*.csv)")[0]
        with open(filename, 'w') as file:
            for i in dataList:
                line = str(i)
                line = line.strip('(')
                line = line.strip(')')
                file.write('{}\n'.format(line))

    def dynamic_response_add_list1_items(self):
        """ Adds all stories and the TLCD to list 1. Takes from inputData.

        :return: None
        """
        self.list1.clear()

        for i in inputData.stories.keys():
            self.list1.addItem('Story {}'.format(i))

        if inputData.tlcd is not None:
            for i in range(inputData.tlcd.amount):
                self.list1.addItem('TLCD {}'.format(i + 1))

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

        if plotType == 'Displacement Vs. Time':
            self.dynRespWidget.dynRespCanvas.plot_displacement(outputData.dynamicResponse, plotList,
                                                               numberOfStories=len(inputData.stories))
        elif plotType == 'Velocity Vs. Time':
            self.dynRespWidget.dynRespCanvas.plot_velocity(outputData.dynamicResponse, plotList)
        elif plotType == 'Acceleration Vs. Time':
            self.dynRespWidget.dynRespCanvas.plot_acceleration(outputData.dynamicResponse, plotList)
        elif plotType == 'Displacement Vs. Velocity':
            self.dynRespWidget.dynRespCanvas.plot_dis_vel(outputData.dynamicResponse, plotList)

    # DMF Methods
    def dmf_grid_toggle(self):
        """ Toggles plot grid on and off

        :return: None
        """
        self.dmfWidget.dmfCanvas.axes.grid(self.dmfWidget.gridChkBox.isChecked())
        self.dmfWidget.dmfCanvas.draw()

    def dmf_add_list3_items(self):
        """ Adds all stories and the TLCD to list 1. Takes from inputData.

        :return: None
        """
        self.list3.clear()

        for i in inputData.stories.keys():
            self.list3.addItem('Story {}'.format(i))

        if inputData.tlcd is not None:
            pass
            # self.list3.addItem('TLCD')

    def dmf_add_list4_item(self):
        """ Adds the item selected on list 1 to list 2 without making duplicates. If successfull, advances one row on
        list 1 and sorts list 2 alphabetically.

        :return: None
        """
        try:
            item = get_text(self.list3)
            row = self.list3.row(self.list3.currentItem())
        except AttributeError:
            return

        if not self.list4.findItems(item, Qt.MatchExactly):
            self.list4.addItem(item)

        if row < self.list3.count() - 1:
            self.list3.setCurrentRow(row + 1)
        self.list4.sortItems(Qt.AscendingOrder)

    def dmf_remove_list4_item(self):
        """ Removes the selected item from list 2

        :return: None
        """
        item = self.list4.currentItem()
        self.list4.takeItem(self.list4.row(item))

    def plot_dmf(self):
        """ Reads the plot type and the QListWidget of DOFs to plot. Makes a list of DOFs to plot and send
        outputData.dynamicResponse and plotList to plot_displacement

        :return:
        """
        plotType = get_text(self.dmfPlotTypeComboBox)
        plotList = []

        for i in range(self.list3.count()):
            self.list3.setCurrentRow(i)
            item = get_text(self.list3)
            if not self.list4.findItems(item, Qt.MatchExactly):
                plotList.append((get_text(self.list3), False))
            else:
                plotList.append((get_text(self.list3), True))

        if plotType == 'DMF Vs Excitation Frequency':
            self.dmfWidget.dmfCanvas.plot_dmf(outputDMF, plotList)
        elif plotType == 'Max. Displacement Vs. Excitation Frequency':
            self.dmfWidget.dmfCanvas.plot_displacement_frequency(outputDMF, plotList)


def main():
    global app
    app = QApplication(sys.argv)
    GUI = MainWindow()
    if debugOption:
        # DEBUG OPTION - LOAD IMMEDIATELY
        # fileName = './save/Validations/Caso 1 (1 andar sem amort).dpfl'
        fileName = './save/tlcd-general.dpfl'
        GUI.open_file(fileName=fileName)
        GUI.run_dynamic_response()
    sys.exit(app.exec_())


def compare_anal_sol(case):
    if case == 1:
        """
        1 andar, vibração forçada ou livre, com ou sem amortecimento da estrutura e sem tlcd.
        qualquer frequência, qualquer CC
        """
        m = inputData.stories[1].mass
        # c = 0
        # k = 24 * 25e9 * (0.35 * 0.35 ** 3 / 12) / (3 ** 3)  # 24EI/L^3 (engastado-engastado)
        k = inputData.stories[1].stiffness
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

    elif case == 3:
        M = outputData.massMatrix

        ksi = inputData.configurations.dampingRatio

        K = outputData.stiffnessMatrix

        F0 = inputData.excitation.amplitude
        omega = inputData.excitation.frequency
        F = np.mat([[F0 * M[i, i]] for i in range(len(M[0, :].A1))])

        t_lim = inputData.excitation.anlyDuration

        phi = assemble_modes_matrix(M, K)
        M_ = assemble_modal_mass_vector(phi, M)
        K_ = assemble_modal_stiffness_vector(phi, K)
        F_ = assemble_modal_force_vector(phi, F)

        x_mod_i = []
        for i in range(len(phi[0].A1)):
            m = float(M_[i].A1)
            k = float(K_[i].A1)
            f = float(F_[i].A1)
            x_mod_i.append(solve_sdof_system(m, ksi, k, f, omega, t_lim))

        x_pav_i = []
        for i in range(len(phi[0].A1)):
            x_pav_i.append(sum([j * k for j, k in zip(x_mod_i, phi[i, :].A1)]))

        t = np.linspace(0, t_lim, 2000)

        with open('./save/Validations/SB/Deslocamentos aceleração na base.txt', 'r') as dados:
            t_sap = []
            xpav1_sap = []
            xpav2_sap = []
            xpav3_sap = []
            for i in range(16):
                dados.readline()
            for line in dados:
                line = line.strip('/n')
                line = line.replace(',', '.')
                dado = line.split()
                t_sap.append(float(dado[0]))
                xpav1_sap.append(float(dado[1]))
                xpav2_sap.append(float(dado[2]))
                xpav3_sap.append(float(dado[3]))

            xpav1_sap = np.array(xpav1_sap)
            xpav2_sap = np.array(xpav2_sap)
            xpav3_sap = np.array(xpav3_sap)

        t_num = outputData.dynamicResponse.t
        x_num = outputData.dynamicResponse.x[0, :].A1
        plt.plot(t, x_pav_i[0], '-r', label='Solução Analítica', marker='d')
        plt.plot(t_num, x_num, '-xb', label='Solução Numérica')
        # plt.plot(t_sap[0: len(t_sap)//2], -xpav1_sap[0: len(t_sap)//2], '-sg', label='Solução SAP 2000')
        plt.legend()
        plt.title('Deslocamento em Função do Tempo')
        plt.xlabel('t (s)')
        plt.ylabel('x (m)')
        plt.show()


if __name__ == '__main__':
    main()
