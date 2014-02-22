#!usr/bin/python
# -*- coding: utf-8 -*-


from _bisect import bisect_left
from os import path
from PyQt4.QtCore import Qt, SIGNAL, pyqtSlot, QModelIndex, QObject, QByteArray
from PyQt4.QtGui import (QTableView, QApplication, QColorDialog, QColor, QStandardItem, 
                         QBrush, QLinearGradient, QInputDialog, QItemSelectionModel, QIcon, QAction,
                         QToolTip, QCursor, QMovie, QLabel, QSizePolicy, QDialog, QVBoxLayout, QMessageBox, qApp)
import sip

from controller.MetBaseControl import MSBaseController, MSDialogController, ChoosenOne
from core.MetObjects import MSPeakList, MSSample, MSSampleList
from gui.dialog.MetIdentificationGui import MSIdentificationDialog
from controller.dialog.MetIdentificationControl import MSIdentificationController
#from core.MetProcessing import massExtractionBisectAlgo
from graphics.MetGLCanvas2D import MSGLCanvas2D
from graphics.MetMplCanvas import MSView, MSQtCanvas, ClusterWidget

#from gui.MetBaseGui import MSTableView

class MSDockController(MSBaseController, ChoosenOne):
    """
    class to handle events the main dock widget
    
    """    
    def __init__(self, model, view):
        """
        the _buildConnections is called in super__init__()
        
        """
        MSBaseController.__init__(self, model, view)
        self.useGL = self.qApp.useGL
        self.currentSample = [None]*3 #each treeView can have different active sample now
        self.hideIndexIcon = True

    def _buildConnections(self):
        """
        make connections
        
        """
        trees = (self.view.treeView_2, self.view.treeView_3, self.view.sampleTableView)        
        QObject.connect(self.view.sampleModel, SIGNAL("itemChanged(QStandardItem *)"), self.itemChanged)
    
        #QObject.connect(self.view.changeColor, SIGNAL('clicked()'), self.updateColor)
        #QObject.connect(self.view.showTic, SIGNAL('clicked()'), self.plotTICS)
        #QObject.connect(self.view.showPeakTable, SIGNAL('clicked()'), self.showPeakTable)
        
        QObject.connect(self.view.sampleTableView, SIGNAL('doubleClicked(const QModelIndex &)'), self.actualizeModels)
        
        
        QObject.connect(self.view.treeView, SIGNAL("doubleClicked(const QModelIndex &)"), self.plotSelection)
        QObject.connect(self.view.treeView_2, SIGNAL("doubleClicked(const QModelIndex &)"), self.plotPeakSelection)
        QObject.connect(self.view.treeView_3, SIGNAL("doubleClicked(const QModelIndex &)"), self.plotClusterSelection)
        
        QObject.connect(self.view.hideItem, SIGNAL('triggered()'), self.hideItem)
        QObject.connect(self.view.markAsGood, SIGNAL("triggered()"), self.markAsGood)
        QObject.connect(self.view.markAsBad, SIGNAL("triggered()"), self.markAsBad)
        
        #to see if we can use 
        #QObject.connect(self.view.treeView_3, SIGNAL("updateClusterModelRequested"), self.updateClusterModel)
        QObject.connect(self.view.removeButton, SIGNAL('clicked()'), self.updateModels)
        for tree in trees:
            QObject.connect(tree, SIGNAL("customContextMenuRequested(const QPoint &)"), tree.showContextMenu)
    
    
    def setCurrentSample(self, sample, idx):
        if sample.shortName() not in [s.shortName() for s in self.qApp.model]:
            print ("Can not set sample...")
            return
        self.currentSample[idx-1] = sample
        if idx == 1:
            goodLabel = self.view.spectraLabel
        elif idx == 2:
            goodLabel = self.view.peakLabel
        elif idx == 3:
            goodLabel = self.view.clusterLabel
        else:
            print ("Error, must return")
            return
        goodLabel.setText(": ".join([str(goodLabel.text().split(':')[0]), 
                                    self.currentSample[idx-1].shortName()]))
        color =QColor.fromRgbF(*sample.color+(1.,))
        palette = goodLabel.palette()
        palette.setColor(goodLabel.foregroundRole(), color)
        goodLabel.setPalette(palette) #works well !
    
    
    
    def activeTree(self, integer):
        """
        manage tue activation of the maingui's treeViews
        
        """
        MSBaseController.activeTree(self, integer)
        if self.acTree != self.view.treeView_2:
            self.view.markAsGood.setVisible(False)
            self.view.markAsBad.setVisible(False)
        else:
            self.view.markAsGood.setVisible(True)
            self.view.markAsBad.setVisible(True)
            
        if self.acTree != self.view.treeView_3:
            self.view.hideItem.setVisible(False)
        else:
            self.view.hideItem.setVisible(True)
    
    
    #===========================================================================
    # INDEX SELECTION MANAGEMENT
    #===========================================================================
    
    @pyqtSlot(QStandardItem)    
    def itemChanged(self, item):
        sample = self.model.sample(item.text(), fullNameEntry=False)
        if sample is None:
            return
        if item.checkState():
            sample.checked=True
        else:
            sample.checked=False
        self.qApp.emit(SIGNAL('redraw()'))
    
                            
    def hideItem(self):
        """
        hide row in the cluster model
        if selected peak has no cluster
        
        """
        n = self.view.clusterModel.rowCount()
        if self.hideIndexIcon:
            for i in xrange(n):
                item = self.view.clusterModel.item(i, 0)
                if not item.hasChildren():
                    self.view.treeView_3.setRowHidden(i, self.view.treeView_3.model().indexFromItem(item.parent()), True)
            self.view.hideItem.setIcon(QIcon(path.normcase("gui/icons/list_add.png")))
        else:
            for i in xrange(n):
                item = self.view.clusterModel.item(i, 0)
                self.view.treeView_3.setRowHidden(i, self.view.treeView_3.model().indexFromItem(item.parent()), False)
            self.view.hideItem.setIcon(QIcon(path.normcase("gui/icons/list_remove.png")))
        self.hideIndexIcon = not self.hideIndexIcon
        self.view.treeView_3.update()
    
    
    def actualizeModels(self, idx):
        """
        will update several models to fit with the selected
        sample
        
        """
        sample = self.model.sample(idx.data().toString(), fullNameEntry=False)
        if sample is None:
            return
        self.qApp.view.sampleDockWidget.cursor().setShape(Qt.WaitCursor)
        MSDialogController.actualizeSpectraModel(sample)
        self.setCurrentSample(sample, 1)
        if sample.rawPeaks:
            MSDialogController.actualizePeakModel(sample)
            self.setCurrentSample(sample, 2)
        if sample.mappedPeaks:
            MSDialogController.actualizeClusterModel(sample)
            self.setCurrentSample(sample, 3)
        self.qApp.view.sampleDockWidget.cursor().setShape(Qt.ArrowCursor)        

    
    def removeSample(self):
        if not self.view.sampleTableView.selectedIndexes():
            self.view.showErrorMessage("Error", "Please select when sample")
            return
        idx = self.view.sampleTableView.selectedIndexes()[0]
        if not idx.isValid():
            print "index is not valid..."
            return
        n = str(idx.data().toString())
        print "to remove", n
        self.model.removeSample(self.model.sample(n, fullNameEntry=False))
        self.view.sampleTableView.removeSelected()
    
    
    @pyqtSlot()
    def updateModels(self):
        """
        repercute les modifications du treeView sur le model
        notamment when erasing sample, peak or cluster
        
        """
        #rows: list of QModelIndex
        #erase the sample [only chrom model, spectr model]
        if self.acTree is None or self.acTree.selectionModel() is None or \
        not self.acTree.selectionModel().hasSelection():
            return
        selection = self.acTree.selectionModel().selectedRows()
        model=self.acTree.model()#self.acModel
        for idx in selection:#normally just one item is selected
            if model==self.view.spectraModel:
                s= self.currentSample[0]
                sp=s.spectrumAt(float(idx.data().toString()))
                try:                    
                    s.spectra.remove(sp)
                except ValueError:
                    print "Error when trying to erase one spectrum"
                #TODO:maybe erase all the peaklist and mapped peaks
                #self.selectLeave((self.view.treeView,), s.shortName(), str(sp))
                self.view.treeView.removeSelected()
                
            elif model==self.view.peakModel:
                s= self.currentSample[1]
                data=idx.data().toString()
                p=s.peakAt(*map(float,data.split('/')))
                s.rawPeaks.remove(p)
                try:
                    s.mappedPeaks.remove(p)
                except ValueError:
                    pass
                #self.selectLeave((self.view.treeView_2,), s.shortName(), str(p))
                self.view.treeView_2.removeSelected()
                
            else:#cluster
                p=idx.parent()
                if p.data().toString() in ("fragments/adducts:","isotopic cluster:"):
                    p = idx.parent().parent().parent()
                s= self.currentSample[2]
                data=idx.data().toString()[:2]
                p=s.peakAt(*map(float,data.split('/')))
                try:
                    s.mappedPeaks.remove(p)
                except ValueError:
                    pass
                #self.selectLeave((self.view.treeview_3,), s.shortName(), str(p))
                self.view.treeView_3.removeSelected()

                    
    
    def selectRoot(self, treeViews, match):
        for k, m in enumerate([t.model() for t in treeViews]):
            if m is None: 
                continue
            selector= treeViews[k].selectionModel()
            for i in xrange(m.rowCount()):
                idx=m.index(i, 0)
                if str(idx.data().toString())==match:
                    selector.select(idx, QItemSelectionModel.Select)
    
    
    def selectLeave(self, treeViews, sample, match):
        #"""
        #TODO:debug
        #
        #"""
        #generally only one treeView is sent        
        if not isinstance(sample, str) and not isinstance(match, str):
            raise TypeError("sample and match argument must be string object")
        for k, m in enumerate([t.model() for t in treeViews]):    
            if m is None:
                continue
            selector= treeViews[k].selectionModel()
            for i in xrange(m.rowCount()):
                if str(m.index(i, 0).data().toString())==sample:
                    item=m.itemFromIndex(m.index(i, 0))
                    for j in xrange(item.row()):
                        if item.child(j, 0).text()==match:
                            selector.select(m.indexFromItem(item), QItemSelectionModel.Select)
                            break
#                        #for the third model
#                        for k in xrange(item.child(j, 0).row()):
#                            if item.child(j, 0).child(k, 0).text()==match:
#                                selector.select(m.indexFromItem(item.child(j, 0).child(k, 0)), 
#                                                QItemSelectionModel.Select)
#                                break
                            
                        
                        
    @pyqtSlot(QAction)
    def addPeakToOneCluster(self, action):
        #if action.text() == 'Identification':
            #print "launch Identification"
        #    return
        idx=self.view.treeView_3.selectedIndexes()[0]
        model=idx.model()
        
        s=self.currentSample[2]#self.model.sample(idx.parent().data().toString(), fullNameEntry=False)
        peak= s.peakAt(str(idx.data().toString()))
        peakToAdd=s.peakAt(str(action.text()))
        peak.fragCluster += [peakToAdd]#first add the parent        
        peak.fragCluster += peakToAdd.fragCluster+peakToAdd.isoCluster#then add its child
                
        #add item
        item=QStandardItem(action.text())
        gotFragItem=False        
        for i in xrange (model.itemFromIndex(idx).rowCount()):
            if model.itemFromIndex(idx).child(i).text() == "fragments/adducts:":
                gotFragItem = True
                fragItem = model.itemFromIndex(idx).child(i)
                fragItem.appendRow(item)
                break
        if not gotFragItem:
            fragItem = QStandardItem("fragments/adducts:")
            fragItem.appendRow(item)
            model.itemFromIndex(idx).appendRow(fragItem)
        #remove the entry peakToAdd
        for i in xrange(model.rowCount()):
            item_=model.item(i, 0)
            if item_.text()==s.shortName():
                for j in xrange(item_.rowCount()):
                    if item_.child(j).text()==action.text():
                        selector=self.view.treeView_3.selectionModel()
                        for idx in self.view.treeView_3.selectedIndexes():
                            selector.select(idx ,QItemSelectionModel.Deselect)
                        item.setIcon(item_.child(j).icon())
                        selector.select(model.indexFromItem(item_.child(j)), QItemSelectionModel.Select)                        
                        self.view.treeView_3.removeSelected()
                        break
            break
  
    @pyqtSlot()
    def removePeakFromOneCluster(self):
        idx=self.view.treeView_3.selectedIndexes()[0]#supposed the selection exists 
        if not idx.isValid():
            return
        model=idx.model()
        #copy the item
        itemToDelete = model.itemFromIndex(idx)
        item = QStandardItem(itemToDelete)
        #no need to select already selected, then removing
        self.view.treeView_3.removeSelected()
        #putting the copied item in view
        parentIndex = idx.parent().parent().parent()
        sample = self.currentSample[3]#self.model.sample(parentIndex.data().toString(), 
                                   #fullNameEntry=False)
        if sample is None:
            print "Unknown error"            
            return
        
        data = map(str, item.text().split('/'))[:2]
        dataParent = map(str, idx.parent().parent().data().toString().split('/'))
        sample.mappedPeaks.sample=sample; sample.rawPeaks.sample=sample#du to one bug don't know why        
        goodPeak = sample.mappedPeaks.peakAt(*map(float, dataParent))
        fragPeak = sample.rawPeaks.peakAt(*map(float, data))
        try:        
            goodPeak.fragCluster.remove(fragPeak)
            goodPeak.isoCluster.remove(fragPeak)
        except ValueError:
            pass            
        #adding item to the treeView
        parentItem = model.itemFromIndex(parentIndex)   
        index = bisect_left(sample.mappedPeaks.masses(), float(item.text().split('/')[0]))
        #model.insertRow(index, item)
        parentItem.insertRow(index, item)      
        self.view.treeView_3.update()
    
    
    @pyqtSlot()
    def markAsGood(self):
        #if self.acTree not in (self.view.treeView_2, self.view.treeView_3):
        #    return
        if not self.acTree.selectedIndexes():
            msgBox = QMessageBox()
            msgBox.setText("All Peaks will be set to be good")
            msgBox.setInformativeText("Do you want to continue ?")
            msgBox.setStandardButtons(QMessageBox.Ok | QMessageBox.Cancel)
            msgBox.setDefaultButton(QMessageBox.Save)
            ret = msgBox.exec_()
            if ret == QMessageBox.Ok:
                n = self.acModel.rowCount()
                for i in xrange(n):
                    idx = self.acModel.index(i, 0)
                    p = self.currentSample[1].peakAt(*map(float, idx.data().toString().split('/')))
                    if not p.isGood:
                        i=self.acTree.model().itemFromIndex(idx)
                        i.setIcon(QIcon('gui/icons/green.svg.png'))
                        p.isGood =True
            return
            
        idx=self.acTree.selectedIndexes()[0]
        if not idx.isValid():
            return
        s=self.currentSample[1]#self.model.sample(idx.parent().data().toString(), fullNameEntry=False)
        p=s.peakAt(*map(float, idx.data().toString().split('/')))
        if p is None:
            print "Unable to find the wanted peak..."
            return
        if p.isGood:
            self.view.showInformationMessage("Information", 
                                             "Peak is supposed to be already a good peak")
        else:
            p.isGood=True
            i=self.acTree.model().itemFromIndex(idx)
            i.setIcon(QIcon('gui/icons/green.svg.png'))
            #self.view.showInStatusbar("Peak at %s is now a GOOD peak"%idx.data().toString())
            self.view.showInformationMessage("Information", 
                                             "Peak at %s is now a <b>good peak</b>"%idx.data().toString())
    
    
    @pyqtSlot()
    def markAsBad(self):
       
        idx=self.acTree.selectedIndexes()[0]
        if not idx.isValid():
            return
        
        s=self.currentSample[1]#self.model.sample(idx.parent().data().toString(), fullNameEntry=False)
        p=s.peakAt(*map(float, idx.data().toString().split('/')))
        if not p.isGood:
            self.view.showInformationMessage("Information", 
                                             "Peak is supposed to be already a bad peak")
        else:
            p.isGood=False

            i=self.acTree.model().itemFromIndex(idx)
            i.setIcon(QIcon('gui/icons/red.png'))
            self.view.showInformationMessage("Information", 
                                             "Peak at %s is now a <b>bad peak</b>"%idx.data().toString())

    
    
    def showInformationToolTip(self, idx):
        """
        Show an informative string about one sample
        
        """
        sample = self.model.sample(idx.data().toString(), fullNameEntry=False)
        if sample is None:
            return
        QToolTip.showText(QCursor.pos(), sample.getInfos())
    
    
    
    
    @pyqtSlot()
    def updateColor(self):
        """
        Update the color on the sampleModel
        modify to fit to the actual view
        
        """
        if not self.view.sampleTableView.selectedIndexes():#not self.acTree.selectedIndexes():
            return
        
        idx = self.view.sampleTableView.selectedIndexes()[0]
        sample = self.model.sample(idx.data().toString(), fullNameEntry=False)
        
        if sample is None:
            self.view.showErrorMessage('Error', 'Please choose only one file...')            
            return
        
        color = QColorDialog.getColor()
        if not color.isValid():
            return
            
        sample.color=color.getRgbF()[:-1]
        
        #make the gradient color here to
        color =QColor.fromRgbF(*(sample.color+(1.,)))
        colorr=QColor.fromRgbF(*(sample.color+(.5,)))
        gradient=QLinearGradient(-100, -100, 100, 100)
        gradient.setColorAt(0.7, colorr)
        gradient.setColorAt(1, color)
        
        #for m in (self.view.sampleModel, self.view.spectraModel, self.view.peakModel, 
        #          self.view.clusterModel):#self.view.chromaModel,
        for i in xrange(self.view.sampleModel.rowCount()):
            item=self.view.sampleModel.item(i,0)
            if item.text()== sample.shortName():
                item.setBackground(QBrush(gradient))
    
    
    
    #===========================================================================
    # GL 3D View NOT USED HERE ANYMORE I THINK
    #===========================================================================
   

        
    #===============================================================================
    # PLOTTING METHODS
    #===============================================================================
    def showPeakTable(self):
        """
        TODO: write little function to check if sample is None or good
        or write exception with good code
        
        """
        if not self.view.sampleTableView.selectedIndexes():#not self.acTree.selectedIndexes():
            s, b = QInputDialog.getItem(self.view, "Select one sample", "Select one sample :", 
                                     [spl.shortName() for spl in self.model])
            if not b:
                return
            sample = self.model.sample(str(s), fullNameEntry=False)
        else:
            idx = self.view.sampleTableView.selectedIndexes()[0]
            sample = self.model.sample(idx.data().toString(), fullNameEntry=False)
        if sample is None:
            print ("sample not found...")
            return
        if not sample.rawPeaks:
            self.view.showErrorMessage("No peaks found", 
                                       "This sample does not have peaks, please do peak picking before")
        view=QTableView()
        view.horizontalHeader().setStretchLastSection(True)
        view.setSortingEnabled(True)
        model=MSDialogController.getSampleModel(sample, flags='peak')
        view.setModel(model)           
        self.view.addMdiSubWindow(view, " ".join(["PeakList of", str(sample.shortName())]))
        
    
    def showClusterTable(self):
        if not self.view.sampleTableView.selectedIndexes():#not self.acTree.selectedIndexes():
            s, b = QInputDialog.getItem(self.view, "Select one sample", "Select one sample :", 
                                     [spl.shortName() for spl in self.model])
            if not b:
                return
            sample = self.model.sample(str(s), fullNameEntry=False)
        else:
            idx = self.view.sampleTableView.selectedIndexes()[0]
            sample = self.model.sample(idx.data().toString(), fullNameEntry=False)
        if sample is None:
            print ("sample not found...")
            return
        if not sample.mappedPeaks:
            self.view.showErrorMessage("No peaks found", 
                                       "This sample does not have peaks, please do peak picking before")
        view= QTableView()
        view.setSortingEnabled(True)
        view.horizontalHeader().setStretchLastSection(True)
        view.setModel(MSDialogController.getSampleModel(sample, flags='cluster'))
        self.view.addMdiSubWindow(view, "ClusterList of%s"%str(sample.shortName()))
      
        
    
    def plotTICS(self):
        chromas=self.getElementsToPlot(flags='chroma')
        title="TICS"
        legend={'bottom':'RT(s)', 'left':'INTENSITY'}
        flags='chroma'
        pw = MSQtCanvas(chromas, title, labels=legend, flags=flags)#, useOpenGL=useOpenGL)
        
        QObject.connect(qApp.instance(), SIGNAL('redraw()'), pw.redraw)            
        a=self.view.mdiArea.activeSubWindow()
        isMax=False
        if a is not None:
            isMax=a.isMaximized()
            w=a.widget()
            w.setParent(None)
            sip.delete(w)
            a.setWidget(pw)
        else:
            self.view.addMdiSubWindow(MSView(pw), title, isMax)
            self.view.mdiArea.tileSubWindows()
    
    
    
    
    @pyqtSlot(QModelIndex)    
    def plotSelection(self, index, boolean=False):
        """
        Allow to plot spectrum
        
        """
        if not index.isValid():
            return
        chromas=self.getElementsToPlot(flags='spectra', index=index.row())
        title="Spectrum@%s"%str(chromas[0].rtmin)
        legend={'bottom':'m/z', 'left':'INTENSITY'}
        flags='spectra'
        #useOpenGL=False                
        pw = MSQtCanvas(chromas, title, labels=legend, flags=flags)#, useOpenGL=useOpenGL)
        QObject.connect(qApp.instance(), SIGNAL('redraw()'), pw.redraw)            
        a=self.view.mdiArea.activeSubWindow()
        isMax=False
        if a is not None and boolean:
            isMax=a.isMaximized()
            w=a.widget()
            #w.connect(w, SIGNAL('destroyed (QObject *)'), self.destroyed)
            #w.setParent(None)
            #print "parent of w just before elimination", w.parent()
            sip.delete(w)#; del w
            del w
            a.setWidget(pw)
            #a.close()
        else:
            self.view.addMdiSubWindow(pw, title, isMax)
            self.view.mdiArea.tileSubWindows()

    
    def destroyed(self):
        print "destruction"
                    
    @pyqtSlot(QModelIndex)
    def plotPeakSelection(self, index, boolean=False):
        """
        Allow to plot peak and peak tables
        
        """                
        if not index.isValid():
            return
        data = index.data().toString().split("/")
        prec, rt =float(data[0]), float(data[1])
        peaks=self.getElementsToPlot(flags='peak', prec=prec, rt=rt)
        pw = MSQtCanvas(peaks, "peak@%s/%s"%(str(prec), str(rt)),
                        labels={'bottom':'RT(s)', 'left':'INTENSITY'}, 
                        flags='peak')
        
        QObject.connect(qApp.instance(), SIGNAL('redraw()'), pw.redraw)
        title="peak@%s/%s"%(str(prec), str(rt))
        win=self.view.mdiArea.activeSubWindow()
        isMax=False
        if win is not None and boolean:
            isMax=win.isMaximized()
            w=win.widget()
            #w.connect(w, SIGNAL('destroyed (QObject *)'), self.destroyed)
            #w.setParent(None)
            sip.delete(w)
            del w
            win.setWidget(MSView(pw))
            #win.close()
        else:
            self.view.addMdiSubWindow(MSView(pw), title, isMax)
            self.view.mdiArea.tileSubWindows()
          
        
    
    @pyqtSlot(QModelIndex)    
    def plotClusterSelection(self, index, boolean=False):
        """
        Allow to plot peak and cluster tables
        
        """
        if not index.isValid():
            return
        string = str(index.data().toString())#.model().data(index.parent(), Qt.DisplayRole).toString()
        if string in ("fragments/adducts:","isotopic cluster:"):
            return
        
        data = string.split('/')
        #print data
        prec=float(data[0])
        rt = float(data[1])
        #print prec, rt
        peaks=self.getElementsToPlot(flags='peak', prec=prec, rt=rt)
        pw = ClusterWidget(peaks, self.view)#MSQtCanvas(peaks, "peak@%s/%s"%(str(prec), str(rt)), labels={'bottom':'RT(s)', 'left':'INTENSITY'}, flags='peak')
        QObject.connect(qApp.instance(), SIGNAL('redraw()'), pw.widget.mainWidget.redraw)
        title="peak@%s/%s"%(str(prec), str(rt))
        win=self.view.mdiArea.activeSubWindow()
        isMax=False
        if win is not None and boolean:
            isMax=win.isMaximized()
            w=win.widget()
            #w.setParent(None)
            sip.delete(w)#
            #del w
            win.setWidget(pw)
        else:
            self.view.addMdiSubWindow(MSView(pw), title, isMax)
            self.view.mdiArea.tileSubWindows()
        
    
    def identify(self):
        idx=self.acTree.selectedIndexes()[0]
        
        if not idx.isValid():
            print "Error, index is not valid"
            return
        p = idx.parent()
        if p.data().toString() in ("fragments/adducts:","isotopic cluster:"):
            p = idx.parent().parent().parent()
        sample=self.currentSample[1 if self.acTree is self.view.treeView_2 else 2]#self.model.sample(p.data().toString(), fullNameEntry=False)
        if sample is None:
            print "Error, sample not found %s"%sample.shortName()
            return
        #data=None
        if len(idx.data().toString().split('/')) > 2:
            data=idx.data().toString().split('/')[:-1]
        else:
            data=idx.data().toString().split('/')
        peak=sample.peakAt(*map(float, data))
        if peak is None:
            self.view.showErrorMessage("Error", "Unable to find the corresponding peak...")
        
        spl=MSSampleList()
        s=MSSample("None")
        s.rawPeaks=MSPeakList([peak], sample=s)
        spl.addSample(s) 
        
        dial=MSIdentificationDialog(parent=self.view)
        dial.setAttribute(Qt.WA_DeleteOnClose)
        controller=MSIdentificationController(spl, dial, False, showDirectResult=True)


