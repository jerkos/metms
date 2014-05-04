# -*- coding: utf-8 -*-

"""
Module implementing a base controller and its derivative,
module depending one the gui used
"""

__author__ = ('marco', 'cram@hotmail.fr')

import os
import glob
from itertools import izip
import sip

from PyQt4.QtCore import (QObject, pyqtSlot, Qt, SIGNAL, QThread, QSettings)
from PyQt4.QtGui import (QFileDialog, QApplication, QDialogButtonBox, QStandardItem, QColor, QBrush, QIcon,
                         QLinearGradient, QStandardItemModel, qApp)
from numpy import array, round
#import sip

from core.MetObjects import MSSample, MSSampleList
from utils.decorators import deprecated


#==============================================================================
class WithPointerToQApp:
    """just add the pointer to the current qApp"""
    qApp = QApplication.instance()


# SINGLETON
#===============================================================================
class ChoosenOne(object):
    """
    simple class implementing a Singleton pattern
    Basically all the core controllers of the main gui

    """
    _instance = None

    def __new__(cls, *args, **kw):
        if not cls._instance:
            cls._instance = super(ChoosenOne, cls).__new__(cls, *args, **kw)
        return cls._instance


# MODEL NOT based on the gui toolkit
#===============================================================================
class MSModel(object):
    def __init__(self, model, **k):
        """
        object which hold data model: any kind of data
        has a parent ?
        not very useful class ? may be removed soon
        """
        #object.__init__(self)
        self.model = model
        self.parent = k.get('parent')


# CONTROLLER BASE GUI BASED
#===============================================================================
class MSBaseController(object, WithPointerToQApp):
    """
    base controller, allow basics operations on
    the model (MSSampleList)

    """
    def __init__(self, model, view):
        """constructor
        @parameter view: the view (dialog)
        @parameter model: the model, data to manipulate, string,
        file, sample, sampleList...
        @parent: it is admitted the view is the parent of her
        controller

        """
        self.view = view
        self.model = model

        self.acModel = None
        self.acTree = None

        window = self.qApp.view  #to avoid error when using a QDialogController
        self.activeTree(window.tabWidget.currentIndex())
        QObject.connect(window.tabWidget, SIGNAL('currentChanged(int)'), self.activeTree)
        QObject.connect(qApp.instance(), SIGNAL('modelChanged'), self.setModel)  #update model, used for loading a project
        self._buildConnections()

    def __del__(self):
        print "controller garbage collected"

    @pyqtSlot(MSSampleList)
    def setModel(self, model):
        self.model = model

    @pyqtSlot(int)
    def activeTree(self, integer):
        window = qApp.instance().view
        if integer not in (0, 1, 2):
            #raise ValueError("TreeView numeroted from 0 to 2")
            return #no raising an error....
        if integer == 0:
            self.acTree = window.treeView
            self.acModel = window.spectraModel
        elif integer == 1:
            self.acTree = window.treeView_2
            self.acModel = window.peakModel
        elif integer == 2:
            self.acTree = window.treeView_3
            self.acModel = window.clusterModel

    def fullXmlPath(self, end):
        """show short name but get long pathways"""
        for name in self.model.getFiles():
            if name.split('/')[-1] == end:
                return name
        return None

    def shortPathFiles(self, filename=None):
        """return short name of files existing in the model"""
        if filename:
            return filename.split('/')[-1]
        return [path.split("/")[-1] for path in self.model.getFiles()]

    @deprecated
    def viewFinder(self, view, attribute):
        """will try to find recursively a parent which have a 'parent' \
        attribute"""
        if not hasattr(view, attribute):
            try:
                self.attributeFinder(self.view.parent(), attribute)
            except Exception:
                print ("can not access to the parent while looking for an attribute")
            finally:
                return None
        else:
            return view

    def filesFromView(self, *args):
        selectedFiles = []
        for index in self.acTree.selectedIndexes():
            if index.isValid():
                xmlfile = index.data().toString()
                selectedFiles.append(self.fullXmlPath(xmlfile))
        return selectedFiles

    def getElementsToPlot(self, flags="chroma", prec=None, rt=None, index=None):
        """
        think about giving only index;should be lot simpler
        flags:
        @chroma: TIC in FACT for both MRM and highRes
        @peak: peak return Eic objects...
        @spectra: return spectra objects
        """

        if flags == "chroma":
            return [spl.chroma[0] for spl in self.model if spl.checked]
        elif flags == 'peak':
            return MSSampleList([spl for spl in self.model if spl.checked]).peakGroup(prec, rt)
        elif flags == 'spectra':
            if index is not None:
                l = []
                for spl in self.model:
                    try:
                        #if qApp.instance().lowMemory:
                        #    l.append(spl.loadSpectrum(index))
                        #else:
                        l.append(spl.spectra[index])
                    except IndexError:
                        pass
                return l

    def _buildConnections(self):
        """will be overloaded in subclasses"""
        pass


    # def launchThreadFor3D(self, sample):
    #     from core.MetProcessing import GLVertexCalculation
    #     self.view.showInStatusBar("3D plotting...May take some time for big dataset", 2000)
    #     thread = GLVertexCalculation(sample, parent=self.view)
    #     QObject.connect(thread, SIGNAL('started()'), self.view.to_indetermined_mode)
    #     QObject.connect(thread, SIGNAL('end_calc'), self.plot3D)
    #     QObject.connect(thread, SIGNAL('end_calc'), self.view.to_determined_mode)
    #     thread.start()
    #     thread.exec_()
    #
    #
    # @pyqtSlot(list, list)
    # def plot3D(self, vertex, colors):
    #     from OpenGL.arrays.vbo import VBO
    #     from graphics.MetGLCanvas3D import Test
    #     vertexes = VBO(array(vertex,'f'))
    #     colorsVBO = VBO(array(colors, 'f'))
    #     wid=Test(vertexes, colorsVBO)
    #     self.view.addMdiSubWindow(wid)

#==============================================================================
# Specialized Controller for dialog handling
#===============================================================================


class MSDialogController(MSBaseController):
    """
    specialized controller for dialogs
    experimental stuffs use with caution ;)
    contains 'model' stuffs

    """
    def __init__(self, model, view, creation=None):
        """
        @workingOn: initializing method for showing on which sample the processing will happen
        @initialize: initialize values  of the dialog
        @selectedFiles: files that will be treated
        @processingParameters: dictionnary objects supposed to contain all args value
        @thread: if the processing step have a thread to handle

        """
        MSBaseController.__init__(self, model, view)
        self.creation = creation #to move
        if not self.creation:
            self._workingOn()
        try:
            self._initialize()  #to initialize the dialog parameter
        except NotImplementedError:
            pass
            #print ('This function must be reimplemented in a subclass to initialize the dialog parameters')
        self.selectedFiles = None  #will be a list of files
        self.directory = None
        self.parameters={}
        self.sampleList = None  #!= from self.model, sampleList is a sublist of self.model
        self.task = None  #parser

    def _buildConnections(self):
        """
        function called in init by the super class
        try to automatize the connection process
        """
        for s in dir(self.view):
            widget = getattr(self.view, s)
            if isinstance(widget, QDialogButtonBox):
                QObject.connect(widget, SIGNAL("rejected()"), self.view.close)
                QObject.connect(widget, SIGNAL("accepted()"), self.startTask)
                #try:
                #except AttributeError:pass
#        try:
#            conn=getattr(self, '__specialsConn__')
#            for signal in conn:
#                self.connect(getattr(self.view, conn[signal][0]), SIGNAL(signal),getattr(self, conn[signal][1]))
#        except AttributeError:pass

    def getParameters(self):
        raise NotImplementedError("this function:%s must be reimplemented in a dialog subclass"%self.getParameters.__name__)

    def setModels(self):
        raise NotImplementedError("this function:%s must be reimplemented in a dialog subclass"%self.getParameters.__name__)

#    @pyqtSlot()
#    def closeView(self):
#        #try:
#        print "trying to close"
#        self.view.close()
#
#        #except Exception:
#        #    pass
#        #del self.view

    def showView(self):
        self.view.exec_()

    def _workingOn(self):
#        if self.acTree not in self.workingTrees: #can work by name too
#        qApp.instance().view.showErrorMessage("Error", """<br>Error when trying to select items from treeView</br>
#                                                        #<p>Select a tab corresponding to the action you want""")
        try:
            self.view.lineEdit.setText(self.stringFormatting([spl.xmlfile for spl in qApp.instance().model if spl.checked]))
        except AttributeError:
            pass

    @pyqtSlot()
    def _printing(self):
        self.view.lineEdit.setText(";".join(self.shortPathFiles()))

    @staticmethod
    def stringFormatting(list_):
        files = ""
        for i, s in enumerate(list_):
            if i < len(list_) - 1:
                files = files + str(s.split('/')[-1]) + ";"
            else:
                files += str(s.split('/')[-1])
        return files

    def _initialize(self):
        raise NotImplementedError("This function must reimplemented in a subclass")

    @pyqtSlot()
    def openFileDialog(self, filter_="*.mzXML;;*.CDF"):
        settings = QSettings('INRA/INSA', '-'.join([self.qApp.instance().APPLICATION_NAME_STR,
                                                    self.qApp.instance().VERSION_STR]))

        self.selectedFiles = QFileDialog.getOpenFileNames(self.view, "Select one or more files to open",
                                                          directory=settings.value("expDir", '').toString(),
                                                          filter=filter_)
        if not self.selectedFiles:
            return
        try:
            self.view.lineEdit.setText(self.stringFormatting(self.selectedFiles))
        except AttributeError:
            pass
        #set the setting value for retrieving the experiments dir
        settings.setValue("expDir", "/".join(map(str, self.selectedFiles)[0].split('/')[:-1]))
        return map(str, self.selectedFiles)

    @pyqtSlot()
    def openDirDialog(self, flags):
        directory = QFileDialog.getExistingDirectory(self.view, "Select one master directory")
        if directory:
            try:
                self.view.lineEdit.setText(directory)
            except AttributeError:
                pass
            if not glob.glob(os.path.normcase(str(directory)+'/'+flags)):
                subdir = os.listdir(directory)
                for d in subdir:
                    self.selectedFiles += glob.glob(os.path.normcase("".join([str(directory) + '/', d, '/' + flags])))
            else:
                self.selectedFiles += map(os.path.normcase, glob.glob(os.path.normcase(str(directory) + '/' + flags)))
            self.directory = str(directory)
        return self.directory

    @staticmethod
    def goodName(string):
        if '\\' in string:
            #string.replace('\\', '/')
        #if '\\\\' in string:
            #string.replace('\\\\', '/')
            s = ''
            for e in string:
                if e == '\\':# or e=='\\\\':
                    s += '/'
                else:
                    s+=e
            return s
        return string

    def _buildSampleList(self, creation=True):
        """
        to describe

        """
        from core import MetObjects as obj
        sampleList = obj.MSSampleList()
        if not self.creation:
            for spl in self.model:
                if spl.checked:
                    sampleList.append(spl)
        else:
            if self.selectedFiles:
                for xml in self.selectedFiles:
                    if str(xml) not in self.model.getFiles():
                        print xml
                        sample = obj.MSSample(xmlfile=self.goodName(str(xml)))
                        #sample.kind = kw.get('kind') if kw.get('kind') else ""
                        sample.directory = self.directory if self.directory else None
                        #self.model.append(sample)
                        sampleList.append(sample)
        return sampleList

    #experimental
    def mainProcessing(self):
        getattr(self, self.__getParam__).__call__()
        if hasattr(self, '__createSample__'):
            self.sampleList = self._buildSampleList(creation=bool(getattr(self, '__createSample__')))
        else:
            self.sampleList = self._buildSampleList()
        if not self.sampleList:
            return
        getattr(self, self.__specialsFunc__).__call__(self.sampleList)
        self.closeView()#self.view.close()
        if not self.task:
            if not hasattr(self, '__thread__'):print ('nothing found for treating thread stuffs');return
            self.task=getattr(self, '__thread__')(self.sampleList, **self.parameters)
        else:
            self.task.sampleList = self.sampleList
            self.task.parameters = self.parameters
        conn=getattr(self, '__threadConn__')
        for signal in conn.keys():
            try:
                self.connect(self.task, SIGNAL(signal), getattr(self.view.parent(), conn[signal]))
            except AttributeError:
                self.connect(self.task, SIGNAL(signal), getattr(self, conn[signal]))
                #print ("Error in automatical handling of the thread connections")
        self.connect(self.task, SIGNAL('finished()'), getattr(self, self.__endFunc__))
        QApplication.instance().taskManager.model.append(self.task)
        try:
            self.task.begin()
        except AttributeError:
            self.task.start();self.task.exec_()


    def startTask(self):
        self.getParameters()#update parameters
        #self.view.close()#self.closeView()
        self.sampleList = self._buildSampleList(creation=self.creation)
        if not self.sampleList:
            qApp.instance().view.showInformationMessage("Error", "Empty selection")
            return

    @staticmethod
    def buildModel(peak):
        labels=["mass:", "rt:", "intensity:", "rtmin:", "rtmax:"]
        values=[str(peak.mass()),str(peak.rt),str(peak.area),str(peak.rtmin),str(peak.rtmax)]
        string="<b>Peak Information:</b>\n"
        for l, v in izip(labels, values):
            string+="".join([l, v,"  "])
        return string


    @staticmethod
    def getSampleModel(spl, flags='peak', **kw):
        from gui.MetBaseGui import MSStandardItem
        if flags not in ('peak', 'cluster', 'id'):
            return
        model = QStandardItemModel()
        if flags=='peak':
            from utils.misc import Hot
            areas=[peak.area for peak in spl.rawPeaks.ipeaks()]
            mxInt=max(areas)
            model.setHorizontalHeaderLabels(MSSample.peakModelLabel)

            for i, peak in enumerate(spl.rawPeaks.ipeaks()):
                model.setItem(i, 0, MSStandardItem(str(peak.mass())))
                model.item(i, 0).setBackground(QBrush(Hot._get_color(areas[i]/mxInt, True, alpha=0.5)))

                model.setItem(i, 1, MSStandardItem(str(peak.rt)))
                model.item(i, 1).setBackground(QBrush(Hot._get_color(areas[i]/mxInt, True, alpha=0.5)))

                model.setItem(i, 2, MSStandardItem(str(peak.area)))
                model.item(i, 2).setBackground(QBrush(Hot._get_color(areas[i]/mxInt, True, alpha=0.5)))

                model.setItem(i, 3, MSStandardItem(str(peak.sn)))
                model.item(i, 3).setBackground(QBrush(Hot._get_color(areas[i]/mxInt, True, alpha=0.5)))

                model.setItem(i, 4, MSStandardItem(str(peak.r_coef)))
                model.item(i, 4).setBackground(QBrush(Hot._get_color(areas[i]/mxInt, True, alpha=0.5)))

        elif flags=='cluster':
            model.setHorizontalHeaderLabels(MSSample.clusterModelLabel)
            for i, peak in enumerate(spl.mappedPeaks.ipeaks()):
                model.setItem(i, 0, MSStandardItem(str(peak.mass())))
                model.setItem(i, 1, MSStandardItem(str(peak.rt)))
                model.setItem(i, 2, MSStandardItem(str(peak.area)))
                info_iso ="";info_frag=""
                for iso in peak.isoCluster:
                    info_iso += '%s/%s\t'%(str(iso.mass()),str(iso.rt))
                for add in peak.fragCluster:
                    info_frag += '%s/%s\t'%(str(add.mass()),str(add.rt))
                model.setItem(i, 3, MSStandardItem(info_iso))
                model.setItem(i, 4, MSStandardItem(info_frag))
        return model



    def getStandardItem(self, peak):
        m=qApp.instance().view.peakModel
        for i in range(qApp.instance().view.peakModel.rowCount()):
            it=m.item(i)
            if it.text()==self.shortPathFiles(peak.sample.xmlfile):
                for i in range(it.rowCount()):
                    if it.child(i).text()=='/'.join([str(peak.mass()), str(peak.rt)]):
                        return it.child(i)


    @staticmethod
    def actualizeSampleModel(sample):
        model = QApplication.instance().view.sampleModel
        nbrows = model.rowCount()
        rootItem = MSDialogController.getColouredRootItem(sample)
        rootItem.setToolTip(sample.getInfos())
        model.setItem(nbrows, 0, rootItem)
        classItem = QStandardItem("A")
        model.setItem(nbrows, 1, classItem)



    @staticmethod
    def getColouredRootItem(sample):
        """stable, may be subdivised in sub routines """
        root = QStandardItem(sample.shortName())
        #root.setIcon(QIcon(QPixmap(os.path.normpath('gui/icons/formula.png'))))
        color =QColor.fromRgbF(sample.color[0],sample.color[1], sample.color[2],1.)
        colorr=QColor.fromRgbF(sample.color[0],sample.color[1], sample.color[2],.5)
        gradient=QLinearGradient(-100, -100, 100, 100)
        gradient.setColorAt(0.7, colorr);gradient.setColorAt(1, color)
        root.setBackground(QBrush(gradient))
        root.setEditable(False)
        root.setCheckState(Qt.Checked)
        root.setCheckable(True)
        return root

    @staticmethod
    def actualizePeakModel(sample):
        model=QApplication.instance().view.peakModel
        if model.rowCount():
            model.clear()
        for peak in sample.rawPeaks.ipeaks():#sorted(sample.rawPeaks, key=lambda x:x.mass()):
            std_item =  QStandardItem(str(peak))
            MSDialogController.setRightIcon(peak, std_item)
            std_item.setEditable(False)
            model.appendRow(std_item)

    @staticmethod
    def actualizePeakModelComparative():
        model = QStandardItemModel()
        #root=MSDialogController.getColouredRootItem(sample)
        sampleList = QApplication.instance().model
        groups = sampleList.peaksGrouping()
        model.setVerticalHeaderLabels(["/".join(map(str, round([mass, rt], 4).tolist())) for mass, rt in sorted(groups.keys(), key=lambda x:x[0])])
        model.setHorizontalHeaderLabels([spl.shortName() for spl in sampleList.isamples()])
        for i, key in enumerate(sorted(groups.keys(), key=lambda x:x[0])):
            zeros = [0.] * len(sampleList)
            for peak in groups[key]:
                try:
                    idx = [spl.shortName() for spl in sampleList].index(peak.sample.shortName())
                except ValueError:
                    print "Error in %s"%MSDialogController.actualizePeakModelComparative.__name__
                zeros[idx] = peak
            for j in xrange(len(zeros)):
                item = QStandardItem()
                if not zeros[j]:
                    item.setBackground(QBrush(Qt.red))
                    item.setText("Not found")
                else:
                    MSDialogController.setRightIcon(zeros[j], item)#set the colour actually
                    item.setText(str(round(zeros[j].area, 2)))
                model.setItem(i, j, item)
        return model


    @staticmethod
    def actualizeSpectraModel(sample):
        #color =QColor.fromRgbF(sample.color[0],sample.color[1], sample.color[2], .4)
        model=QApplication.instance().view.spectraModel
        if model.rowCount():
            model.clear()

        for i, spectrum in enumerate(sample.ispectra()):
            std_item = QStandardItem(str(spectrum.rtmin))
            #std_item.setBackground(QBrush(color))
            s = "<b>rtmin</b>: %f<br/>"%spectrum.rt
            s += "<b>rtmax</b>: %f<br/>"%spectrum.rtmin
            s += "<b>nb Points</b>: %d"%spectrum.x_data.shape[0]
            std_item.setToolTip(s)
            std_item.setIcon(QIcon(os.path.normpath('gui/icons/spectrumicon.png')))
            std_item.setEditable(False)
            model.appendRow(std_item)

    @staticmethod
    def actualizeClusterModel(sample):
        model=QApplication.instance().view.clusterModel
        if model.rowCount():
            model.clear()

        idItems = []
        for peak in sample.imappedPeaks():
            std_item = QStandardItem(str(peak))
            std_item.setEditable(False)
            if peak.isFoundInDatabase:
                std_item.setBackground(QBrush(Qt.green))
                #put the formula with the best score
                o = QStandardItem(peak.formulas.keys()[0])
                o.setBackground(QBrush(Qt.green))
                idItems.append(o)
            else:
                idItems.append(QStandardItem("not found"))
            MSDialogController.setRightIcon(peak, std_item)
            if peak.isoCluster:
                iso_item = QStandardItem("isotopic cluster:")
                iso_item.setEditable(False)
                for iso in peak.isoCluster:
                    item = QStandardItem(str(iso))
                    item.setEditable(False)
                    MSDialogController.setRightIcon(iso, item)
                    iso_item.appendRow(item)
                std_item.appendRow(iso_item)
            if peak.fragCluster:
                frag_item = QStandardItem("fragments/adducts:")
                frag_item.setEditable(False)
                for frag in peak.fragCluster:
                    item =QStandardItem("/".join([str(frag.mass()), str(frag.rt), str(frag.annotation.values())[2:-2]]))
                    item.setEditable(False)
                    MSDialogController.setRightIcon(frag, item)
                    frag_item.appendRow(item)
                std_item.appendRow(frag_item)
            model.appendRow(std_item)
        model.appendColumn(idItems)



    @staticmethod
    def setRightIcon(peak, item):
        if peak.isoSpectra:
            if len(peak.isoSpectra)>1:
                item.setIcon(QIcon(os.path.normcase('gui/icons/green.svg.png')))
            elif len(peak.isoSpectra)==1:
                item.setIcon(QIcon(os.path.normcase('gui/icons/orange.png')))
        else:
            item.setIcon(QIcon(os.path.normcase('gui/icons/red.png')))



#===============================================================================
# base thread use in almost every dialog controller
#===============================================================================
class MSThreadBasis(QThread):
    """
    base thread, use QThread instead of standard python thread for
    higher compatibility

    """
    def __init__(self, parent=None, **k):
        """
        @jobs: jobs list, parallel python jobs
        @abort: boolean to stop threaded code to exec

        """
        QThread.__init__(self, parent)
        self.connect(self, SIGNAL('destroyed(QObject *)'), self.printinfo)
        self.jobs = [] #not used
        self.abort = False

    def run(self):
        """
        have to reimplement this function
        code that will be threaded

        """
        raise NotImplementedError


    def stop(self):
        """
        the attribute 'abort' is then check in the run
        function to stop the process
        """
        self.abort = True

    def begin(self):
        #print "thread begins"
        self.start()
        #self.exec_()
        #self.wait()

    def printinfo(self):
        print ("QThread garbage collected")

#===============================================================================
# still experimental not fully implemented
#===============================================================================
class MSTaskManager(object):
    """
    simplistic thread treatment

    """
    def __init__(self, controllers=[], tasks=[], parent=None):
        """
        @task is a list of thread
        """
        self.controllers=controllers
        self.tasks= tasks
        self.parent = parent#view is the parent and vice versa

    def abort(self, task, pid=None):
        if task is not None:
            if hasattr(task, 'stop'):
                QObject.connect(QApplication.instance(), SIGNAL('abort()'), task.stop)
            else:
                import warnings
                warnings.warn("No stop method in a thread...keep an eye on running processes",
                              RuntimeWarning)
            QApplication.instance().emit(SIGNAL("abort()"))
        else:
            #kill the subprocess giving his pid
            #some probleme are known on windows
            #so dont know what to do
            pass
            #try:
            #    impo
    def abortByName(self, t):
        for c in self.iterkeys:
            if c.title == str(t.text()):
                self.abort(self[c])
                break




    def deleteOneController(self, c):
        sip.delete(self[c])
        del self[c]
        QApplication.instance().view.updateStopProcessMenu()





#===============================================================================
# glue class for updating several view in the same time
#===============================================================================
class MSViewManager(MSBaseController):
    '''
    Manager taht repertories all the views, in order to update each views
    kind of trampolines class
    '''
    #not needed ?
    #requireUpdate = pyqtSignal(QWidget, object)

    def __init__(self, obj_to_manage=[], parent=None):
        from gui.MetBaseGui import MSView

        if not all([isinstance(obj,MSView) for obj in obj_to_manage]):
            raise TypeError("All objects must a MSView objects")
        MSBaseController.__init__(self, obj_to_manage, parent)

        for view in self.model:
            self.connect(view, SIGNAL("viewHasChanged"), self.updateView)


    def updateView(self, data):
        """launch the updates of all the others view with the appropriates data
        """
        try:
            pass
        except IndexError:pass


    def addView(self, view):
        if not isinstance(view, MSView):raise TypeError
        self.connect(view, SIGNAL("IChanged"), self.updateView)