#! usr/bin/python


"""
Module for drawing 2D plots of spectrum, chromatogram
to reimplement with subclassing
"""
import math, os

from PyQt4.QtOpenGL import QGLWidget
from PyQt4.QtGui import (QApplication, QWidget, QMenu, 
                         QVBoxLayout,  QComboBox,
                         QInputDialog, QSplitter, QDialog, 
                         QFormLayout, QSpinBox, QDialogButtonBox,
                         QToolButton, QPen, QBrush,
                         QIcon, QPixmap,QGraphicsTextItem, QFont, 
                         QGraphicsItem, QCursor, QColor, QGraphicsView, 
                         QGraphicsScene, QGraphicsEllipseItem, QGraphicsPixmapItem, 
                         QAction, QTableView, QTreeView, QStandardItemModel, QLabel,
                         QPushButton, QHBoxLayout, QStandardItem, qApp, QSizePolicy, QPalette)

from PyQt4.QtCore import (Qt, SIGNAL, pyqtSlot, pyqtSignal, QObject, QSize, QThread)
import numpy as np
import matplotlib
matplotlib.use('Qt4Agg')
from matplotlib.backends.backend_qt4agg import FigureCanvasQTAgg as FigureCanvas, NavigationToolbar2QT as MplToolBar
from matplotlib.figure import Figure

from controller.MetBaseControl import MSDialogController
from core.MetObjects import MSSample, MSSpectrum
from pyqtgraph.PlotWidget import PlotWidget          
from pyqtgraph.graphicsItems import BarPlot, SpectrumItem, PeakIndicator, Line, PeakArrowItem, ScatterPlotItem, ViewBox
from utils.bisection import max_l, min_f, max_f, abs





class MSView(QSplitter):
    modifiedContext = pyqtSignal(object)
    
    def __init__(self, widget, parent=None, **kw):
        QSplitter.__init__(self, Qt.Horizontal, parent)
        self.setFocusPolicy(Qt.StrongFocus)
        self.mainWidget = widget        
        self.addWidget(self.mainWidget)
        
        self.showHide = None        
        
        self.subsidiaryWidget = MSQtCanvas([], "", flags='spectrum')#, subsidiaryWidget=True)
        self.subsidiaryWidget.pw.plotItem.toolBar.hide()
        
        self.subsidiaryWidget.setContextMenuPolicy(Qt.CustomContextMenu)
        self.connect(self.subsidiaryWidget, SIGNAL("customContextMenuRequested(const QPoint &)"), self.showContextMenu)
        self.menu=QMenu(self.subsidiaryWidget)
        self.menu.addAction("&Hide...")        
        self.connect(self.menu.actions()[0], SIGNAL("triggered()"), self.subsidiaryWidget.hide)
        
        self.addWidget(self.subsidiaryWidget)
        self.subsidiaryWidget.hide()
        self.barplotdrawn = False
        
        self.connect(self.mainWidget, SIGNAL('drawSpectraRequested'), self.drawSpectrum)
        self.connect(self.mainWidget, SIGNAL('drawSpectra(PyQt_PyObject, PyQt_PyObject, PyQt_PyObject)'), self.drawSpectra)
        self.connect(self.mainWidget, SIGNAL('drawSpectrumByTime'), self.drawSpectrumByTime)        
        self.connect(self.mainWidget, SIGNAL('hideRequested'), self.subsidiaryWidget.hide)
    
    
    def showContextMenu(self, pos):
        if self.subsidiaryWidget.pw.plotItem.vb.hasMoved:
            return self.menu.exec_(QCursor.pos())
        
    @pyqtSlot()
    def drawSpectrum(self, p):
        if p is None:
            return
        mergedSpectra=p.merge(p.spectra)
        self.subsidiaryWidget.pw.clear()        
        self.subsidiaryWidget._plotting([mergedSpectra])
        self.subsidiaryWidget.pw.setTitle("Merged Spectrum@%s-%s"%(str(p.rtmin), str(p.rtmax)))        
        self.subsidiaryWidget.show()
    
    def drawSpectrumByTime(self, t, sample):
        if not sample or not t:
            print "unknown error..."            
            return
        spectra = sample.spectraInRTRange(t.x(), t.x()-2., t.x()+2.)
        if not spectra:
            print "No spectrum found at this retention time"
            return
        closest = sorted(spectra, key=lambda x: abs(t.x()-x.rtmin))[0]
        self.subsidiaryWidget.pw.clear()        
        self.subsidiaryWidget._plotting([closest])
        self.subsidiaryWidget.pw.setTitle("Spectrum@%s"%(str(closest.rtmin)))                        
        self.subsidiaryWidget.show()

    def drawSpectra(self, inf, sup, sample):
        if not sample:
            return
        spectra = sample.spectraInRTRange((inf+sup)/2., inf, sup)
        print [s.rtmin for s in spectra]
        spectrum = None        
        if not spectra:
            print "No spectrum found at this retention time"
            return
        elif len(spectra) > 1:
            ref = spectra[0]
            others = spectra[1:]
            spectrum = ref.merge(others)
        else:
            spectrum = spectra[0]
        self.subsidiaryWidget.pw.clear()        
        self.subsidiaryWidget._plotting([spectrum])
        self.subsidiaryWidget.pw.setTitle("Spectrum@%s"%(str(spectrum.rtmin)))                        
        self.subsidiaryWidget.show()




class MSQtCanvas(QWidget, MSDialogController):
    """
    DONE:the current peak is not updated while the user press up and down key on the treeView
    TODO: think about a mjor redesign of those classes
    
    """
    
    #linePlotted = pyqtSignal(object, str)
    #lineRemoved = pyqtSignal(object)
    
    def __init__(self, data, title, flags="chroma", parent=None, **k):
        QWidget.__init__(self, parent)
        MSDialogController.__init__(self, 0, parent)
        
        self.model = self.qApp.model
        self.view =  self.qApp.view
      
        self.data=data
        self.title=title
        self.flags=flags
        
        if self.flags == 'peak':
            if self.acTree not in (self.view.treeView_2, self.view.treeView_3):
                print "Unknown Error"
                return
            idx=self.acTree.selectedIndexes()[0]
            s = qApp.instance().dockControl.currentSample[1 if self.acTree is self.view.treeView_2 else 2]
            if s is None:
                print "unknow error"
                return            
            values = map(float, idx.data().toString().split('/')[:2])
            self.currentPeak = s.peakAt(*values)
            #connection to update the selected Peak object
            self.connect(self.acTree, SIGNAL("changedLine"), self.updateCurrentPeak)
        
        self.minX, self.maxX, self.maxY  = [0] * 3
        #if flags != 'peak':
        #    self.minX, self.maxX, self.maxY = self.getMax()
        self.pw = PlotWidget(self.minX, self.maxX, self.maxY,  parent=self, **k)#parent=self,
        #self.pw.setAttribute(Qt.WA_DeleteOnClose)#plotItem.setAttribute(Qt.WA_PaintOnScreen & Qt.WA_PaintUnclipped)
        if k.get('antialiased', False):
            self.pw.setRenderHint(0x01)#antialiasing i suppose
        self.pw.setTitle(title)
        self.pw.updateGrid()

        
        self._setupUi()        
        
        self.connect(self, SIGNAL('linePlotted'), self.updateContextMenu)
        self.connect(self.view.sampleTableView, SIGNAL("disHighlightRequested(QModelIndex)"), self.disHighlightOne)
        self.connect(self.view.sampleTableView, SIGNAL("highlightRequested(QModelIndex)"), self.highlight)
        self.connect(self.view.sampleTableView, SIGNAL("noHighlightRequested()"), self.disHighlight)
        self.connect(self.view.ppmEditer, SIGNAL('valueChanged(double)'), self.redrawAll)
        
        self.drawnItems = {} 
        self.trashItems=[]#why unecessary? nope to collect annotation stuff
        self.textLabels = []
        self.pixmaps = []
        self.dataPoints = None
        
        self._plotting(self.data)#initial plotting
          

    def getMax(self):
        localXmin =[]        
        localXmax = []
        localYmax = []        
        for el in self.data:
            if el is None:
                continue
            localXmin.append(min_f(el.x_data))
            localXmax.append(max_f(el.x_data))
            localYmax.append(max_l(el.y_data))
        return min_f(np.array(localXmin)), max_f(np.array(localXmax)), max_l(np.array(localYmax)) 
    
    
    
    def _plotting(self, data):
        """
        refactor this shit
        c = Line(chrom.x_data, chrom.y_data, 
                 QColor.fromRgbF(*(self.ref.sample.color+(.7,))),
                 parent=self.pw.plotItem.vb, 
                 scene=self.pw.scene())
        
        #test scatter plot
        self.scatter = ScatterPlotItem(x=chrom.x_data, y=chrom.y_data)
        self.pw.addDataItem(self.scatter)
        self.scatter.sigClicked.connect(self.requestSpectra)
        
        """
        if self.flags == 'peak':
            
            self.connect(self.pw.plotItem.vb, SIGNAL('showDiffOrSpectra(PyQt_PyObject)'), self.drawSpectra)
            self.ref = sorted([e for e in data if e is not None], key=lambda x:x.height)[-1]
            ppm = self.view.ppmEditer.value() if self.view.usePpm.isChecked() else self.ref.sample.ppm
            chrom = self.ref.sample.massExtraction(self.ref.mass(), 
                                                   ppm, 
                                                   asChromatogram=True) 
            #show labels
            self.textLabels += self.showTextLabel(chrom.x_data, chrom.y_data)
            #drawing
            color = QColor.fromRgbF(*self.ref.sample.color +(.5, ))

            c = self.pw.plotItem.plot(chrom.x_data, chrom.y_data, pen=color)
            self.drawnItems[self.ref.sample] = c
            # peak's pixmap on the ref peak
            pix= PeakArrowItem(self.ref, 
                               pen=color,
                               brush=color,
                               pos=(self.ref.rt, self.ref.height + (self.ref.height * 6) / 100.),
                               angle=-90,
                               parent=self.pw.plotItem.vb)
            pix.setZValue(1000)
            self.pw.addItem(pix)
            #both these connections are emitted 
            #in peak Indicator by effictivamente qApp
            self.connect(qApp.instance(), SIGNAL("highlightRequested"), c.setHighlighted)
            self.connect(qApp.instance(), SIGNAL('updateBarPlot'), self.barPlot.setPeakGroup) #
            self.emit(SIGNAL('linePlotted'), self.ref.sample.shortName())
     
            #if qApp.instance().lowMemory:
            #    chromatograms=[el.sample.loadAndExtract(el.mass(), el.sample.ppm, asChromatogram=True) \
            #                  for el in data if el != ref and el is not None]
            #else:
            ppm = self.view.ppmEditer.value() if self.view.usePpm.isChecked() else self.ref.sample.ppm
            chromatograms=[el.sample.massExtraction(el.mass(), ppm, asChromatogram=True) \
                          for el in data if el is not None and el != self.ref]
            self.drawEics(chromatograms)
            #initialisation zoom on the peak
            self.pw.setYRange(0., self.ref.height + (self.ref.height * 12) / 100.)
            self.pw.setXRange(self.ref.rtmin - 20, self.ref.rtmax + 20)
            
        elif self.flags == 'chroma':
            ref = [d for d in data if d is not None]
            if not ref:
                print "Error, empty data to plot"
                return 
            self.ref = ref[0] 
            self.textLabels+=self.showTextLabel(self.ref.x_data, self.ref.y_data)
            self.drawEics(data)
                        
        else:#spectrum
            if not data:
                #print "NOTHING TO PLOT"
                return
            self.ref = data[0]
            for el in data:
                c=SpectrumItem(el, centroid=True, scene=self.pw.scene())
                self.pw.addItem(c)
                self.drawnItems[el.sample] = c
                self.pw.plotItem.curves.append(c)    
                self.emit(SIGNAL('linePlotted'), el.sample.shortName()) 
            #just put time information
            if data:
                i=0
                while data[i] is None and i < len(data):
                    i+=1
                self.textLabels+=self.showTextLabel(data[i].x_data, data[i].y_data)
            #setting the range
            #warning: autoRange pw function does not work well
            #on spectrum item
            maxY = max([el.y_data.max() for el in data])
            minX, maxX = min([el.x_data.min() for el in data]), max([el.x_data.max() for el in data])
            self.pw.setXRange(minX, maxX, padding=0) 
            self.pw.setYRange(0., maxY, padding=0)

    
    def drawEics(self, data):
        for chrom in data:
            color = QColor.fromRgbF(*(chrom.sample.color+(.5,))) 
            c=self.pw.plotItem.plot(x=chrom.x_data, y=chrom.y_data, pen=color)
            #c = Line(chrom.x_data, chrom.y_data, 
            #         color,
            #         parent=self.pw.plotItem.vb, 
            #         scene=self.pw.scene())
            self.drawnItems[chrom.sample] = c
            #self.pw.addItem(c)
            #self.pw.plotItem.curves.append(c)
            self.emit(SIGNAL('linePlotted'), chrom.sample.shortName())
        if self.flags != 'peaks':
            self.pw.autoRange()
#===========================================================================
# UI stuffs
#===========================================================================
 

    def _setupUi (self):    
      
#        self.stop = QToolButton()
#        self.stop.setIcon(QIcon('gui/icons/tools_wizard.png'))
#        self.stop.setToolTip('Enable or disable the appearance of the contextMenu')
        layout=QVBoxLayout(self)
        
        self.smoothButton=QToolButton()
        #self.smoothButton.setToolButtonStyle(2)
        self.smoothButton.setPopupMode(2)
        self.smoothButton.setToolTip("Smooth the visualized data")
        #self.smoothButton.setText("Smooth...")
        self.smoothButton.setIcon(QIcon(os.path.normcase('gui/icons/smooth.png')))
        self.smoothMenu = QMenu()
        self.connect(self.smoothMenu, SIGNAL('triggered(QAction*)'), self.smooth)
        self.smoothButton.setMenu(self.smoothMenu)
        self.pw.plotItem.toolBar.addWidget(self.smoothButton)

        self.flipButton=QToolButton()
        #self.flipButton.setToolButtonStyle(2)
        self.flipButton.setIcon(QIcon(os.path.normcase('gui/icons/flip.png')))
        self.flipButton.setToolTip("Flip the visualized data")
        #self.flipButton.setText("Flip...")
        self.flipButton.setPopupMode(2)
        self.flipMenu = QMenu()
        self.connect(self.flipMenu, SIGNAL('triggered(QAction*)'), self.flip)
        self.flipButton.setMenu(self.flipMenu)
        self.pw.plotItem.toolBar.addWidget(self.flipButton)
                
        self.annotButton=QToolButton()
        #self.annotButton.setToolButtonStyle(2)
        self.annotButton.setPopupMode(2)
        #self.annotButton.setText("&Annotate...")
        self.annotButton.setIcon(QIcon(os.path.normcase('gui/icons/attach.png')))
        self.annotMenu = QMenu()
        self.annotMenu.addAction("&Add Annotation")
        self.annotMenu.addAction("&Remove last Annotation")
        self.annotMenu.addAction("&Remove All Annotation")
        self.annotButton.setMenu(self.annotMenu)
        self.connect(self.annotMenu.actions()[0], SIGNAL("triggered()"), self.annotate)
        self.connect(self.annotMenu.actions()[1], SIGNAL("triggered()"), self.removeLastAnnot)
        self.connect(self.annotMenu.actions()[2], SIGNAL("triggered()"), self.removeAllAnnot)
        self.pw.plotItem.toolBar.addWidget(self.annotButton)
        
        self.addPlotButton=QToolButton()
        #self.addPlotButton.setToolButtonStyle(2)
        self.addPlotButton.setText("Add...")
        self.addPlotButton.setIcon(QIcon(os.path.normcase('gui/icons/list_add.png')))
        self.addPlotButton.setToolTip("Add a new plot to the current figure")
        #self.addPlotButton.setText('&Add Plot')
        self.pw.plotItem.toolBar.addWidget(self.addPlotButton)
        
        self.showSpectra=QToolButton()
        self.showSpectra.setPopupMode(2)  #instant popup
        #self.showSpectra.setToolButtonStyle(2)   
        self.showSpectra.setIcon(QIcon(os.path.normcase('gui/icons/file_export.png')))   
        #self.showSpectra.setText('&Show /hide...')
        self.showSpectra.setToolTip('Show/hide ...')
        self.showMenu=QMenu()
        self.showTextLabels=QAction("&Show Labels", self.showMenu)
        self.showTextLabels.setCheckable(True)
        self.showTextLabels.setChecked(True)
        self.showMenu.addAction(self.showTextLabels)
        self.connect(self.showMenu.actions()[0], SIGNAL('toggled(bool)'), self.setTextLabelsVisibility)
        showSpectrum=QAction("&Merged Spectrum", self.showMenu)
        showSpectrum.setCheckable(True)
        if self.flags == 'chroma' or self.flags == 'spectra':
            showSpectrum.setEnabled(False)
        self.showMenu.addAction(showSpectrum)
        self.connect(self.showMenu.actions()[1], SIGNAL('toggled(bool)'), self.drawSpectraRequested)
        
        showNonXCMSPeak=QAction("&Show Non XCMS Peak", self.showMenu)
        showNonXCMSPeak.setCheckable(True)
        if self.flags == 'spectra':
            showNonXCMSPeak.setEnabled(False)
        self.showMenu.addAction(showNonXCMSPeak)
        self.connect(self.showMenu.actions()[2], 
                     SIGNAL('toggled(bool)'), 
                     self.setPixmapVisibility)
        
        showDataPoints = QAction("&Show DataPoints", self.showMenu)
        showDataPoints.setCheckable(True)
        showDataPoints.setChecked(False)
        self.showMenu.addAction(showDataPoints)
        self.connect(self.showMenu.actions()[3], 
                     SIGNAL('toggled(bool)'), 
                     self.setDataPointsVisibility)
        self.showSpectra.setMenu(self.showMenu)
        self.pw.plotItem.toolBar.addWidget(self.showSpectra)
        
        self.saveToPng = QToolButton()
        self.saveToPng.setIcon(QIcon(os.path.normcase('gui/icons/thumbnail.png')))
        #self.saveToPng.setToolButtonStyle(2)
        #self.saveToPng.setText("Save to Png...")
        self.pw.plotItem.toolBar.addWidget(self.saveToPng)
        self.connect(self.saveToPng, SIGNAL('clicked()'), self.pw.writeImage)
        #add bar plot even if we are plotting chroma
        #cause we can find non xcms peaks
        self.barPlot = BarPlot(scene=self.pw.sceneObj)
        #self.barPlot.rotate(-90.)
        if self.flags == 'peak':
            self.barPlot.setPeakGroup(self.data)
        #TODO modify to get this close to us
        #on the left part
        xpos = self.barPlot.scene().width()*3.5#-bwidth;
        ypos = self.barPlot.scene().height()*1.1
        self.barPlot.setPos(xpos,ypos)
        self.barPlot.setZValue(1000)

        layout.addWidget(self.pw)
        layout.addWidget(self.pw.plotItem.toolBar)

    
    
    def showTextLabel(self, x, y, secure=25):
        """
        add labels of principle peaks of spectrum or chroma
        on the plot, return the labels, that we can show hide
        
        """
        maxis=[]#will contain tuple(rt, intens)
        indexes=[]
        #from core.MetObjects import MSAbstractTypes
        from scipy.ndimage import gaussian_filter1d as gauss        
        z=gauss(y, 1)
        #z = MSAbstractTypes.computeBaseLine(z, 92., 0.8)
        i=0
        while i <len(z)-1:
            while z[i+1] >= z[i] and i < len(y)-2:
                i+=1
            maxis.append((x[i], y[i])) 
            indexes.append(i)
            while z[i+1] <= z[i] and i<len(z)-2:
                i+=1
            i+=1
        labels=[]    
        for t in sorted(maxis, key=lambda x:x[1])[-5:]:
            g=QGraphicsTextItem(str(t[0]))
            g.setFlag(QGraphicsItem.ItemIgnoresTransformations)
            font=QApplication.font()
            font.setPointSizeF(6.5)
            g.setFont(font)
            g.setDefaultTextColor(Qt.black)
            g.setPos(t[0], t[1])
            labels.append(g)
            self.pw.addItem(g)
        return labels
            

#===============================================================================
#SLOTS 
#===============================================================================
    def redrawAll(self, value):
        self.pw.clear()
        self._plotting(self.data)

    def disHighlightOne(self, idx):
        if not idx.isValid():
            return
        sample = self.model.sample(idx.data().toString(), fullNameEntry=False)
        if sample is None:
            return
        try:
            self.drawnItems[sample].setHighlighted(False)
        except KeyError:
            pass
        
    def highlight(self, idx):
        if not idx.isValid():
            return
        sample = self.model.sample(idx.data().toString(), fullNameEntry=False)
        if sample is None:
            return
        try:
            self.drawnItems[sample].setHighlighted(True)
        except KeyError:
            pass
            #print "sample not found"
        self.pw.plotItem.update()#works
    
    def disHighlight(self):
        for key in self.drawnItems.iterkeys():
            self.drawnItems[key].setHighlighted(False)
        self.pw.plotItem.update()
    

    def setTextLabelsVisibility(self, bool_):
        for t in self.textLabels:
            t.setVisible(bool_)
    
    
    def setDataPointsVisibility(self, b):
        if self.dataPoints is None:
            if self.flags == 'peak':
                chrom = self.ref.sample.massExtraction(self.ref.mass(), self.ref.sample.ppm, asChromatogram=True)
                self.dataPoints = ScatterPlotItem(x=chrom.x_data, y=chrom.y_data)
            else:
                self.dataPoints = ScatterPlotItem(x=self.ref.x_data, y=self.ref.y_data)
            if self.flags != 'spectra':
                self.dataPoints.sigClicked.connect(self.requestSpectra)
            self.pw.addDataItem(self.dataPoints)
        self.dataPoints.setVisible(b)
    
    
    def setPixmapVisibility(self, bool_):
        """
        draw other peaks than the xcms peak
        
        """
        if not self.pixmaps and bool_:
            ppm = 1. if self.ref.sample.kind=='MRM' else self.ref.sample.ppm
            chrom = self.ref.sample.massExtraction(self.ref.mass(), ppm, asChromatogram=True) \
            if self.flags == 'peak' else self.ref
            chrom.findNonXCMSPeaks()
            for p in chrom.peaks.ipeaks():
                if self.flags == 'peak':
                    diff=(p.height*10)/100
                    if abs(p.height-self.ref.height) < diff:
                        continue #we assume that they are the same peaks
                pix=PeakIndicator(p, icon='flags')
                #self.connect(pix, SIGNAL("highlightRequested"), c.setHighlighted)
                self.connect(pix, SIGNAL('updateBarPlot'), self.barPlot.setPeakGroup)
                pix.setPos(p.rt, p.height + (p.height * 10) / 100.)
                pix.setZValue(1000)
                self.pixmaps.append(pix)
                self.pw.addItem(pix)                
        if self.pixmaps:
            for t in self.pixmaps:
                t.setVisible(bool_)
    
    @pyqtSlot()
    def updateCurrentPeak(self):
        idx=self.acTree.selectedIndexes()[0]
        s=self.model.sample(idx.parent().data().toString(), fullNameEntry=False)
        if s is not None:
            self.currentPeak=s.peakAt(*map(float, idx.data().toString().split('/')))
    
    
    def requestSpectra(self, scatter, l):
        """
        idea plot all spectra between a time range
        and not only with only one spectra
        
        """
        if not l:
            return
        ref = l[0]
        self.emit(SIGNAL("drawSpectrumByTime"), ref.pos(), self.ref.sample)
        
        
    
    
    @pyqtSlot()
    def drawSpectraRequested(self, bool_):
        """
        i think this is for plotting merged spectrum
        
        """
        if bool_:
            self.emit(SIGNAL('drawSpectraRequested'), self.currentPeak)
        else:
            self.hideRequested()
    
    def drawSpectra(self, l):
        self.emit(SIGNAL('drawSpectra(PyQt_PyObject, PyQt_PyObject, PyQt_PyObject)'), l[0], l[1], self.ref.sample)        
    
    @pyqtSlot()
    def hideRequested(self):
        self.emit(SIGNAL('hideRequested'))
        self.showMenu.actions()[1].setChecked(False)
        
  

    @pyqtSlot()
    def redraw(self):
        """
        this is for updating the view port
        when hiding or not samples
        
        """
        chromas =[]
        for spl in self.model:
            if spl.checked:
                if spl in self.drawnItems.keys():
                    self.drawnItems[spl].setVisible(True)
                else:
                    chromas.append(spl.chroma[0])
            else:
                self.drawnItems[spl].setVisible(False)
        self._plotting(chromas)
        self.pw.plotItem.update()#works
   
   
    
    def cleanScene(self):
        """
        remove all items in the trash
        
        """
        for element in self.trashItems:
            self.pw.sceneObj.removeItem(element)
            

    @pyqtSlot()
    def updateContextMenu(self, line): 
        self.flipMenu.addAction(line)
        self.smoothMenu.addAction(line)
    


#===============================================================================
# CONTEXT MENU SLOTS
#===============================================================================
    @pyqtSlot(str)
    def flip(self, action):
        spl=self.model.sample(self.fullXmlPath(action.text()))
        if spl is None:
            print "can not flip, can not recognize the selected sample"
            return
        try:
            self.drawnItems[spl].updateData(-self.drawnItems[spl].getData()[1], 
                                            self.drawnItems[spl].getData()[0])
        except KeyError:
            pass
        if len(self.data) == 1:
            #we are flipping the text labels only
            #if only one dataset is flipped
            for item in self.textLabels:
                item.setPos(item.pos().x(), -item.pos().y())
    
    @pyqtSlot(str)
    def smooth(self, action):
        """
        TODO:
        would be good to reuse the widget in the menuControl
        
        """
        from core.MetObjects import MSAbstractTypes
        class Dial(QDialog):
            choices =['flat', 'hanning', 'hamming', 'bartlett', 'blackman']
            def __init__(self, parent):
                QDialog.__init__(self, parent)
                f =QFormLayout(self)
                self.a =QSpinBox(self)
                self.a.setValue(30)
                self.b = QComboBox(self)
                self.b.addItems(self.choices)
                self.c= QDialogButtonBox(self)
                self.c.setStandardButtons(QDialogButtonBox.Cancel|QDialogButtonBox.Ok)
                f.addRow("window:" ,self.a)
                f.addRow("method:", self.b)
                f.addRow("", self.c)
                self.connect(self.c, SIGNAL("accepted()"), self.sendData)
                self.connect(self.c, SIGNAL("rejected()"), self.reinitialize)
            
            def sendData(self):
                self.parent().window = self.a.value()
                self.parent().method = self.b.currentText()
                self.close()
            
            def reinitialize(self):
                self.parent().window = None
                self.parent().method = None
                self.close()
                
        Dial(self).exec_()
        if self.window and self.method:
            for spl in self.drawnItems.keys():
                if action.text() == spl.shortName():
                    self.drawnItems[spl].updateData(
                    MSAbstractTypes.averageSmoothing(self.drawnItems[spl].getData()[1],self.window , self.method),
                    self.drawnItems[spl].getData()[0])
           

    @pyqtSlot()
    def plotEIC(self):
        if self.flags == 'spectra':
            
            #show double combobox
            #select the good spectra then draw
            pass
        else:
            mass, ok = QInputDialog.getText(self.view, "EIC query", "mass:")
            if not (mass and ok):
                return
            xmlfile = self.fullXmlPath(self.selection[0].data().toString())
            if not xmlfile:
                xmlfile = self.fullXmlPath(self.selection[0].parent().data().toString())
            if not xmlfile:
                print "item clicked not recognized..."
                return
            sample = self.model.sample(xmlfile)
            if sample.kind =='HighRes':
                error=(sample.ppm/1e6)*float(mass)
                x, y = massExtraction(sample, float(mass), error)
                from core.MetObjects import MSChromatogram
                chrom = MSChromatogram(x_data=x, y_data=y, sample=sample)
            else:
                chrom = sample.getChromWithTrans(math.ceil(float(mass)))
        self.view.addMdiSubWindow(MSQtCanvas([chrom], "EIC %s"%str(mass), 
                                             labels={'bottom':'RT(s)', 'left':'INTENSITY'}))
        
    
    #===========================================================================
    # annotate stuff
    #===========================================================================
    @pyqtSlot()
    def annotate(self):
        text, bool_ = QInputDialog.getText(self.view, "Annotation dialog", "Annotation:")
        g=QGraphicsTextItem(str(text))
        g.setFlag(QGraphicsItem.ItemIgnoresTransformations)
        g.setFlag(QGraphicsItem.ItemIsMovable)
        g.setTextInteractionFlags(Qt.TextEditorInteraction)
        font=qApp.instance().font()
        font.setPointSizeF(10.)
        g.setFont(font)
        g.setDefaultTextColor(Qt.blue)
        g.setPos(500,1e4)
        self.trashItems.append(g)
        self.pw.addItem(g)
    
    def removeAllAnnot(self):
        if not self.trashItems:
            self.view.showErrorMessage("Error", "No annotation detected")
            return
        for i in self.trashItems:
            self.pw.removeItem(i)
    
    def removeLastAnnot(self):
        if not self.trashItems:
            self.view.showErrorMessage("Error", "No annotation detected")
        self.pw.removeItem(self.trashItems[-1])
    
    

from pyqtgraph.GraphicsView import GraphicsView
from pyqtgraph.graphicsItems import TinyPlot
class GalleryWidget(GraphicsView):
    
    def __init__(self, data, parent=None, useOpenGL=True):
        
        GraphicsView.__init__(self, parent, useOpenGL)
        
        self.scene().removeItem(self.centralWidget)
        self.enableMouse=True
        
        self.setViewport(QGLWidget() if useOpenGL else QWidget())
        self.setAlignment(Qt.AlignLeft | Qt.AlignTop);
        
        self.data=data
        self.hBox=20
        self.vBox=20
        self.maxItemPerRow=3
        self.setScene(QGraphicsScene)
        self.scene().setItemIndexMethod(QGraphicsScene.BspTreeIndex)
        
        
    def drawMap(self, data):
        for i in xrange(0, len(data), 3):
            item = TinyPlot([data[i]], parent=self, scene=self.scene())
            item.setPos(self.hbox, self.vbox)
            
        
    def addData(self, p):
        if not hasattr(p, 'x_data'):
            raise AttributeError("the data must have an x_data attribute or \
            must be a chromatographicPeak object")
        self.data.append(p)
            
        
class ClusterWidget(QSplitter):
    def __init__(self, peaks, parent=None):
        QSplitter.__init__(self, Qt.Vertical, parent)
        self.peaks = peaks
        self.choosenOne = [pe for pe in self.peaks if pe is not None][0]
        #self.peakModel = QStandardItemModel()
        self.identificationModel = QStandardItemModel()
        self.setupUi()
        self.setModel()
        self.connect(self.calcCorr, SIGNAL('pressed()'), self.setRankValue)
        #self.setRankValue()
    
    def setupUi(self):
        self.widget = MSView(MSQtCanvas(self.peaks, "peaks@%s"%str(self.peaks[0]), 
                                 labels={'bottom':'RT(s)', 'left':'INTENSITY'},
                                 flags='peak'))
        self.tableView = QTableView()
        self.tableView.horizontalHeader().setStretchLastSection(True)
        self.tableView.setSortingEnabled(True)

        self.corr = QLabel("Nan")
        self.calcCorr = QPushButton("r_coef:")
        #v = QVBoxLayout(self)
        self.addWidget(self.widget)
        
        self.wid = QWidget()        
        vb = QVBoxLayout()
        vb.addWidget(self.calcCorr)
        vb.addWidget(self.corr)
        hb = QHBoxLayout(self.wid)
        #if self.choosenOne.formulas:
        hb.addWidget(self.tableView)
        #else:
        #    hb.addWidget(QLabel("Identification not performed yet..."))
        hb.addLayout(vb)
        self.addWidget(self.wid)
    
    def setModel(self):
        from gui.MetBaseGui import MSStandardItem
        #we assume that the different peaks have the same identifiers
        #TODO: may have to merge several stuffs later
        if self.choosenOne.formulas:
            self.identificationModel.setHorizontalHeaderLabels(["score", "formula", "diff mass", "names"])
            for i, f in enumerate(self.choosenOne.formulas.iterkeys()):
                
                self.identificationModel.setItem(i, 0, MSStandardItem(str(self.choosenOne.formulas[f]["score"])))
                self.identificationModel.setItem(i, 1, QStandardItem(str(f)))
                self.identificationModel.setItem(i, 2, MSStandardItem(str(self.choosenOne.formulas[f]["diffmass"])))
                self.identificationModel.setItem(i, 3, QStandardItem(self.choosenOne.formulas[f]["names"]))
                if self.choosenOne.formulas[f]["names"] != 'Not Found':
                    for j in xrange(4):
                        self.identificationModel.item(i, j).setBackground(QBrush(Qt.green))
                else:
                    for j in xrange(4):
                        self.identificationModel.item(i, j).setBackground(QBrush(Qt.red))
            self.tableView.setModel(self.identificationModel)
    
    def setRankValue(self):
        #m = qApp.instance().model
        #m.pearsonIntraCalculation()
        #peaks =[]
        #for spl in m:
        #    peaks+=[p.r_coef for p in spl.mappedPeaks if p.r_coef]
        #if not self.choosenOne.r_coef:        
        self.choosenOne.pCalcBasedOnPeakShape()
        #from _bisect import bisect_left
        #x = bisect_left(sorted(peaks), self.choosenOne.r_coef)
        s = '<br><b>%f</b></br>'%np.round(self.choosenOne.r_coef, 4)
        #s+='<br><b>Rank: </b>%d</br>'%abs(len(peaks)-x)
        self.corr.setText(s)








class MSMplCanvas(QWidget):
    """
    Ultimately, this is a QWidget (as well as a FigureCanvasAgg, etc.).
    
    """
    def __init__(self, data, parent=None, width=5, height=4, dpi=100):
        self.data = data
        QWidget.__init__(self, parent)
        vb = QVBoxLayout(self)
        self.fig=Figure(figsize=(5, 4), dpi=76, facecolor='w')
        self.axes = self.fig.add_subplot(111, axisbg='w', xlabel="Retention Time", ylabel="mz")
        self.compute_initial_figure()
        can=FigureCanvas(self.fig)
        can.setParent(self)
        mpl_toolbar = MplToolBar(can,self)
        vb.addWidget(mpl_toolbar)
        vb.addWidget(can)
        self.colorBar = None

    def sizeHint(self):
        #w, h = self.get_width_height()
        return self.size()#QSize(w, h)

    def minimumSizeHint(self):
        return QSize(10, 10)

class MSSpectrogramCanvas(MSMplCanvas):
    """
    Simple canvas with a sine plot.
    
    """
    def compute_initial_figure(self, log=True):
        if isinstance(self.data, MSSample):
            spectra = self.data.spectra
        elif all([isinstance(x, MSSpectrum) for x in self.data]):
            #print "hola"
            spectra = self.data
        else:
            raise TypeError("not sure how to plot that kind of data...")
        x_data, y_data, intens =[], [], []
        #y_data = np.array([x.x_data.tolist() for x in spectra]).flatten()
        #intens = np.array([x.y_data.tolist() for x in spectra]).flatten()
        for i in xrange(len(spectra)):
            for j in xrange(spectra[i].x_data.shape[0]):
                x_data.append(spectra[i].rt)
            y_data += spectra[i].x_data.tolist()
            intens += spectra[i].y_data.tolist()
        #self.t = PointsCalc(spectra)
        #self.connect(self.t, SIGNAL('endCalculation(PyQt_PyObject, PyQt_PyObject, PyQt_PyObject)'), self.plotData)
        #self.t.begin()
        #print y_data
        
    #def plotData(self, x_data, y_data, intens):
        #print "plotting"
        p = self.axes.hexbin(x_data, y_data, C=np.log(intens))# if log else self.t.intens)
        self.colorBar = self.axes.figure.colorbar(p)
        self.colorBar.draw_all()
        #self.axes.colormap()

class MSDtwCanvas(MSMplCanvas):
    """
    Dtw canvas
    
    """
    def compute_initial_figure(self, imageShow=False):
        if imageShow:
            gsample = None
            for sample in self.data.iterkeys():
                if self.data[sample][2] is not None:
                    gsample = sample
                    break
            if gsample is None:
                print "Unknown error..."
                return
            self.axes.imshow(self.data[gsample][2], origin='lower', interpolation='bicubic')
        #self.colorBar = self.axes.figure.colorbar(p)
        #self.colorBar.draw_all()
        #self.axes.set_xlabel("")
        #self.axes.set_ylabel("Bonsoir paris")
        self.axes.set_title("Optimal Warping Path")
        for dtw in self.data.itervalues():
            self.axes.plot(dtw[0], dtw[1])
        self.data = None
        #self.axes.colormap()



class PointsCalc(QThread):
    """
    in fact the plotting time takes longer than
    the calculation point
    
    """
    def __init__(self, data, parent=None):
        QThread.__init__(self, parent)
        self.data = data
        
    def run(self):
        self.x_data, self.y_data, self.intens = [], [], []
        for i in xrange(len(self.data)):
            for j in xrange(self.data[i].x_data.shape[0]):
                self.x_data.append(self.data[i].rt)
            self.y_data += self.data[i].x_data.tolist()
            self.intens += self.data[i].y_data.tolist()
        self.emit(SIGNAL('endCalculation(PyQt_PyObject, PyQt_PyObject, PyQt_PyObject)'), self.x_data, self.y_data, self.intens)
    
    def begin(self):
        self.start()
        self.exec_()