# -*- coding: utf-8 -*-


from PyQt4 import QtGui, QtCore



class MSAlignWidget(QtGui.QWidget):
    def __init__(self, parent=None):
        QtGui.QWidget.__init__(self, parent)
        self._setupUi()
    
    def _setupUi(self):
        gb = QtGui.QGroupBox("Alignement:", self)
        vl = QtGui.QVBoxLayout()
        hb = QtGui.QHBoxLayout()
        self.loess = QtGui.QCheckBox("use loess algorithm")
        hb.addWidget(self.loess)
        self.obiwarp = QtGui.QCheckBox("use Obiwarp algorithm")        
        hb.addWidget(self.obiwarp)
        vl.addLayout(hb)
        self.plot = QtGui.QCheckBox("Plot retention time shift") 
        vl.addWidget(self.plot)
        gb.setLayout(vl)        


class MSGroupingWidget(QtGui.QWidget):
    def __init__(self, parent=None):
        QtGui.QWidget.__init__(self, parent)
        self._setupUi()





class MSCentWaveDialog(QtGui.QDialog):
    def __init__(self, parent=None):
        QtGui.QDialog.__init__(self, parent)
        self.setWindowTitle('CentWave Algorithm parameters')
        self._setupUi()
        
    def _setupUi(self):
        vl = QtGui.QVBoxLayout(self)
        
        gb_1 = QtGui.QGroupBox("Working on:", self)     
        hl = QtGui.QHBoxLayout()
        self.lineEdit = QtGui.QLineEdit(self)
        self.lineEdit.setReadOnly(True)
        hl.addWidget(self.lineEdit)
        gb_1.setLayout(hl)
        vl.addWidget(gb_1)
                
        gb = QtGui.QGroupBox("Integrations using CentWave Algorihtm", self)
        self.gb_2 = QtGui.QGroupBox("Grouping methods", self)
        self.gb_2.setCheckable(True)
        hb = QtGui.QHBoxLayout()
        fl_1 = QtGui.QFormLayout()        
        fl_2 = QtGui.QFormLayout() 
        fl_3 = QtGui.QFormLayout()
        fl_4 = QtGui.QFormLayout()
        self.spinBox = QtGui.QSpinBox(self)
        self.spinBox.setToolTip("")
        self.spinBox.setMaximumSize(QtCore.QSize(100,200))
        self.spinBox_2 = QtGui.QSpinBox(self)
        self.spinBox_2.setToolTip("")
        self.spinBox_2.setMaximumSize(QtCore.QSize(100,200))
        self.lineEdit_2 = QtGui.QLineEdit(self)
        self.lineEdit_2.setMaximumSize(QtCore.QSize(100,200))
        self.lineEdit_3 = QtGui.QCheckBox('integrate',self)#QLineEdit(self)
        self.lineEdit_3.setMaximumSize(QtCore.QSize(100,200))        
        self.lineEdit_4 = QtGui.QLineEdit(self)
        self.lineEdit_4.setMaximumSize(QtCore.QSize(100,200))        
        self.lineEdit_5 = QtGui.QLineEdit(self)
        self.lineEdit_5.setMaximumSize(QtCore.QSize(100,200))        
        self.lineEdit_6 = QtGui.QLineEdit(self)
        self.lineEdit_6.setMaximumSize(QtCore.QSize(100,200))
        self.checkBox = QtGui.QCheckBox('fitGauss', self)
        self.checkBox.setMaximumSize(QtCore.QSize(100,200))
        self.lineEdit_7 = QtGui.QLineEdit(self)
        self.lineEdit_7.setMaximumSize(QtCore.QSize(100,200))
        self.lineEdit_8 = QtGui.QLineEdit(self)
        self.lineEdit_8.setMaximumSize(QtCore.QSize(100,200))        
        self.lineEdit_9 = QtGui.QLineEdit(self)
        self.lineEdit_9.setMaximumSize(QtCore.QSize(100,200))        
        self.lineEdit_10 = QtGui.QLineEdit(self)
        self.lineEdit_10.setMaximumSize(QtCore.QSize(100,200))        

        
        
        fl_1.addRow("ppm:", self.spinBox)        
        fl_1.addRow("scanrange:", self.lineEdit_2)
        fl_1.addRow("snthresh:", self.spinBox_2)
        fl_1.addRow("", self.lineEdit_3)
               
        fl_2.addRow("peakWidth:", self.lineEdit_4)
        fl_2.addRow("noise:", self.lineEdit_5)
        fl_2.addRow("", self.checkBox)
        fl_2.addRow("mzdiff", self.lineEdit_6)
        hb.addLayout(fl_1)         
        hb.addLayout(fl_2)        
        gb.setLayout(hb)        
        vl.addWidget(gb)
        
        hl =  QtGui.QHBoxLayout()     
        fl_3.addRow("minfrac:", self.lineEdit_7)
        fl_3.addRow("bw:", self.lineEdit_8)
        fl_4.addRow("max:", self.lineEdit_9)
        fl_4.addRow("mzwid:", self.lineEdit_10)
        hl.addLayout(fl_3);hl.addLayout(fl_4)
        self.gb_2.setLayout(hl)
        vl.addWidget(self.gb_2)
        
        
        #alignment        
        self.gb_3 = QtGui.QGroupBox("Alignement:", self)
        self.gb_3.setCheckable(True)
        vbox = QtGui.QVBoxLayout()
        hbox = QtGui.QHBoxLayout()
        self.loess = QtGui.QRadioButton("use loess algorithm", self)
        hbox.addWidget(self.loess)
        self.obiwarp = QtGui.QRadioButton("use Obiwarp algorithm", self)        
        hbox.addWidget(self.obiwarp)
        vbox.addLayout(hbox)
        self.plot = QtGui.QCheckBox("Plot retention time shift", self) 
        vbox.addWidget(self.plot)
        
        self.gb_3.setLayout(vbox)
        vl.addWidget(self.gb_3)
        self.parallel = QtGui.QPushButton("Send Work to a server", self)
        vl.addWidget(self.parallel)
        
        self.buttonBox = QtGui.QDialogButtonBox(self)
        self.buttonBox.setStandardButtons(QtGui.QDialogButtonBox.Ok|QtGui.QDialogButtonBox.Cancel)
       
        vl.addWidget(self.buttonBox)


class MSMatchedFilteredDialog(QtGui.QDialog):
    def __init__(self, parent=None):
        QtGui.QDialog.__init__(self, parent)
        self.setWindowTitle('MatchFiltered Algorithm parameters')
        self._setupUi()
        
    def _setupUi(self):
        vl = QtGui.QVBoxLayout(self)
        gb_1 = QtGui.QGroupBox("Working on:", self)     
        hl = QtGui.QHBoxLayout()
        self.lineEdit = QtGui.QLineEdit(self)
        self.lineEdit.setReadOnly(True)
        hl.addWidget(self.lineEdit)
        gb_1.setLayout(hl)
        vl.addWidget(gb_1)
                
        gb = QtGui.QGroupBox("Integrations using MatchedFiltered Algorihtm", self)
        hb = QtGui.QHBoxLayout()
        fl_1 = QtGui.QFormLayout()        
        fl_2 = QtGui.QFormLayout()        
        self.spinBox = QtGui.QSpinBox(self)
        self.spinBox.setToolTip("maximum peaks detected per chromatogram")
        self.spinBox.setMaximumSize(QtCore.QSize(100,200))
        self.lineEdit_2 = QtGui.QLineEdit(self)
        self.lineEdit_2.setToolTip("full width at half maximum of matched filtration gaussian model peak")
        self.lineEdit_2.setMaximumSize(QtCore.QSize(100,200))
        self.lineEdit_3 = QtGui.QLineEdit(self)
        self.lineEdit_3.setToolTip("step size to use for profile generation")        
        self.lineEdit_3.setMaximumSize(QtCore.QSize(100,200))        
        self.lineEdit_4 = QtGui.QLineEdit(self)
        self.lineEdit_4.setToolTip("number of steps to merge prior to filtration")        
        self.lineEdit_4.setMaximumSize(QtCore.QSize(100,200))        
        self.lineEdit_5 = QtGui.QLineEdit(self)
        self.lineEdit_5.setToolTip("minimum difference in m/z for peaks with overlapping retention times")
        self.lineEdit_5.setMaximumSize(QtCore.QSize(100,200))        
        self.lineEdit_6 = QtGui.QLineEdit(self)
        self.lineEdit_6.setToolTip("signal to noise ratio cutoff")
        self.lineEdit_6.setMaximumSize(QtCore.QSize(100,200))
        self.lineEdit_7 = QtGui.QLineEdit(self)
        self.lineEdit_7.setMaximumSize(QtCore.QSize(100,200))
        self.lineEdit_8 = QtGui.QLineEdit(self)
        self.lineEdit_8.setMaximumSize(QtCore.QSize(100,200))        
        self.lineEdit_9 = QtGui.QLineEdit(self)
        self.lineEdit_9.setMaximumSize(QtCore.QSize(100,200))        
        self.lineEdit_10 = QtGui.QLineEdit(self)
        self.lineEdit_10.setMaximumSize(QtCore.QSize(100,200))      
        
        fl_1.addRow("fwhm:", self.lineEdit_2)        
        fl_1.addRow("step:", self.lineEdit_3)
        fl_1.addRow("steps:", self.lineEdit_4)
        hb.addLayout(fl_1)        
        fl_2.addRow("mzdiff:", self.lineEdit_5)
        fl_2.addRow("sntresh:", self.lineEdit_6)
        fl_2.addRow("max:", self.spinBox)
        hb.addLayout(fl_2)        
        gb.setLayout(hb)        
        vl.addWidget(gb)
        
        #grouping
        self.gb_2=QtGui.QGroupBox('Grouping:')
        self.gb_2.setCheckable(True)
        self.gb_2.setChecked(QtCore.Qt.Unchecked)
        hl =  QtGui.QHBoxLayout()
        fl_4, fl_5 = QtGui.QFormLayout(),QtGui.QFormLayout()
        fl_4.addRow("minfrac:", self.lineEdit_7)
        fl_4.addRow("bw:", self.lineEdit_8)
        fl_5.addRow("max:", self.lineEdit_9)
        fl_5.addRow("mzwid:", self.lineEdit_10)
        hl.addLayout(fl_4);hl.addLayout(fl_5)
        self.gb_2.setLayout(hl)
        vl.addWidget(self.gb_2)
        
        
        #alignment        
        self.gb_3 = QtGui.QGroupBox("Alignement:", self)
        self.gb_3.setCheckable(True)
        vbox = QtGui.QVBoxLayout()
        hbox = QtGui.QHBoxLayout()
        self.loess = QtGui.QRadioButton("use loess algorithm", self)
        hbox.addWidget(self.loess)
        self.obiwarp = QtGui.QRadioButton("use Obiwarp algorithm", self)        
        hbox.addWidget(self.obiwarp)
        vbox.addLayout(hbox)
        self.plot = QtGui.QCheckBox("Plot retention time shift", self) 
        vbox.addWidget(self.plot)
        self.gb_3.setLayout(vbox)
        vl.addWidget(self.gb_3)
        """
        self.gb_4 = QtGui.QGroupBox("Merging:", self)
        self.gb_4.setCheckable(True)
        self.gb_4.setChecked(QtCore.Qt.Unchecked)
        vl_3 = QtGui.QVBoxLayout()
        self.merging = QtGui.QCheckBox("enable merging")
        vl_3.addWidget(self.merging)
        fl_3 = QtGui.QFormLayout()
        self.lineEdit_7 = QtGui.QLineEdit(self)
        self.lineEdit_8 = QtGui.QLineEdit(self)
        fl_3.addRow("File to merge:", self.lineEdit_7)
        fl_3.addRow("Name of the new sample:", self.lineEdit_8)        
        hl_3 = QtGui.QHBoxLayout()
        self.newSample = QtGui.QRadioButton("create a new sample")
        self.mergePeaks = QtGui.QRadioButton("merge peaks")
        self.mergePeaks.setChecked(True)
        hl_3.addWidget(self.newSample)
        hl_3.addWidget(self.mergePeaks)
        vl_3.addLayout(fl_3)
        vl_3.addLayout(hl_3)
        self.gb_4.setLayout(vl_3)
        vl.addWidget(self.gb_4)
        """  
        self.parallel = QtGui.QPushButton("Send Work to a server", self)
        vl.addWidget(self.parallel)
        
        self.buttonBox = QtGui.QDialogButtonBox(self)
        self.buttonBox.setStandardButtons(QtGui.QDialogButtonBox.Ok|QtGui.QDialogButtonBox.Cancel)
       
        vl.addWidget(self.buttonBox)         
        