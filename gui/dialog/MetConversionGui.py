# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'converter.ui'
#
# Created: Tue Jun 29 11:07:45 2010
#      by: PyQt4 UI code generator 4.7.2
#
# WARNING! All changes made in this file will be lost!

from PyQt4 import QtCore, QtGui

class MSConversionDialog(QtGui.QDialog):
    
    def __init__(self, parent =None):
        QtGui.QDialog.__init__(self, parent)
        self.setupUi()
        
    def setupUi(self):
        self.resize(450, 200)
        self.verticalLayout = QtGui.QVBoxLayout(self)
        self.verticalLayout.setSizeConstraint(QtGui.QLayout.SetMinimumSize)
        self.gridLayout = QtGui.QGridLayout()
        self.gridLayout.setSizeConstraint(QtGui.QLayout.SetMinimumSize)
        self.lineEdit = QtGui.QLineEdit(self)
        self.gridLayout.addWidget(self.lineEdit, 4, 1, 1, 1)
        self.lineEdit_2 = QtGui.QLineEdit(self)
        self.gridLayout.addWidget(self.lineEdit_2, 2, 1, 1, 1)
        self.label_2 = QtGui.QLabel(self)
        self.gridLayout.addWidget(self.label_2, 2, 0, 1, 1)
        self.label = QtGui.QLabel(self)
        self.gridLayout.addWidget(self.label, 4, 0, 1, 1)
        self.label_3 = QtGui.QLabel(self)
        self.gridLayout.addWidget(self.label_3, 0, 0, 1, 1)
        self.lineEdit_3 = QtGui.QLineEdit(self)
        self.gridLayout.addWidget(self.lineEdit_3, 0, 1, 1, 1)
        self.pushButton = QtGui.QPushButton(self)
        self.pushButton.setMaximumSize(QtCore.QSize(50, 16777215))
        self.gridLayout.addWidget(self.pushButton, 1, 0, 1, 1)
        self.verticalLayout.addLayout(self.gridLayout)
        self.textEdit_2 = QtGui.QTextEdit(self)
        font = QtGui.QFont()
        font.setItalic(True)
        self.textEdit_2.setFont(font)
        self.textEdit_2.setReadOnly(True)
        self.verticalLayout.addWidget(self.textEdit_2)
        self.label_2.setBuddy(self.lineEdit_2)
        self.label.setBuddy(self.lineEdit)
        
        self.buttonBox = QtGui.QDialogButtonBox(self)
        self.buttonBox.setStandardButtons(QtGui.QDialogButtonBox.Cancel|QtGui.QDialogButtonBox.Ok)
        self.verticalLayout.addWidget(self.buttonBox)
        
        self.retranslateUi()
        QtCore.QMetaObject.connectSlotsByName(self)

    def retranslateUi(self):
        self.setWindowTitle(QtGui.QApplication.translate("Frame", "Frame", None, QtGui.QApplication.UnicodeUTF8))
        self.label_2.setText(QtGui.QApplication.translate("Frame", "Enter files to convert (example:1 or 1,5 or 2-9):", None, QtGui.QApplication.UnicodeUTF8))
        self.label.setText(QtGui.QApplication.translate("Frame", "Enter special arguments :", None, QtGui.QApplication.UnicodeUTF8))
        self.label_3.setText(QtGui.QApplication.translate("Frame", "Files to convert :", None, QtGui.QApplication.UnicodeUTF8))
        self.pushButton.setText(QtGui.QApplication.translate("Frame", "...", None, QtGui.QApplication.UnicodeUTF8))

    def InstructionsOpt(self):

        return "Information options=\n \
            -G               use information recorded in wiff file default off  \n\
            \n\
General options=  \n\
            --compress, -z   use zlib to compress peaks  \n\
            --coordinate     report native scan refernce  \n\
            -s<num>-<num>   report only these range of sample ids \n\
                            -s1  : only sample#1  \n\
                            -s3- : only sample#3 onward  \n\
                            -s-6 : only sample#1 to sample#6  \n\
                            -s2-4 : only sample#2 to sample#4  \n\
                            \n\
Processing Operation options=  \n\
            -GC             determine precursor charge default off  \n\
            -PI<num>        where num is a float specifying min peak intensity to be  \n\
                            considered as signal default 0  \n\
            -PP<num>        where num is a float specifying min % of max peak \n\
                            intensity to be considered as signal default 0 (0-100) \n\
                            suggested: 10 (i.e. 10%) \n\
            -c1             centroid MS data default off  \n\
            --centroid, -c  centroid MS/MS data default off \n\
            --deisotope, -d deisotope MS/MS data default off \n\
                            \n\
MS/MS Averaging options=\n\
            -GPM<num>   where num is a float specifying the precursor mass tolerance  \n\
                        to be considered for grouping unit da default: 0, i.e.  \n\
                        no MS2 averaging suggested: 1  \n\
            -GMA<num>   where num is a int specifying the max cycles span allowed  \n\
                        within a group default 10 \n\
            -GMI<num>   where num is a int specifying the min cycles per group  \n\
                        within a group default 1  \n\
                        \n\
MS/MS Filtering options=  \n\
            -FPC<num>   where num is a int specifying the min peak count to include  \n\
                        a spectra in output default 10  \n\
                    \n\ "
