from pluginmanager.MetPluginFactory import MSPlugin



from PyQt4.QtGui import QDockWidget, QLabel, QWidget, QFormLayout
from PyQt4.QtCore import SIGNAL
#from core.MetObjects import MSChromatogram

className='PluginManualIntegrator'
autoActivation=False


class PluginManualIntegrator(MSPlugin):
    def __init__(self, model, view, parent=None):
        MSPlugin.__init__(self, model, view, parent)
        #self.connect(self.view.mdiArea, SIGNAL('subWindowActivated(QMdiSubWindow*)'), self.updateCurrentWindow)
        self.guiWidget=[]
        
        self.view.mdiArea.subWindowActivated.connect(self.updateCurrentWindow)
        self.x1val=0
        
        self.dock=QDockWidget("Manual Integrator")
        self.guiWidget.append(self.dock)
        self.window=self.view.mdiArea.activeSubWindow() if self.view.mdiArea.activeSubWindow() else None
        if self.window is not None:
            #self.connect(self.window.widget().pw, 
            #            SIGNAL(self.window.widget().pw.sigMouseReleased), 
            #            self.pluginAlgorithm)
            self.window.widget().pw.plotItem.vb.sigClick.connect(self.pluginAlgorithm)            
        
        
        self.label=QLabel('Inactive') if not self.window else QLabel('Active')
        self.dock.setWidget(self.label)
        self._guiUpdate()
        
    
    def _guiUpdate(self):
        self.view.addDockWidget(0x1, self.dock)#showInformationMessage('test', "Hello From Integrator Plugin")
        
    
    def _buildConnections(self):pass
    
    
    
    def updateCurrentWindow(self, win):
        if win is None:return
        #print "update current window", win
        self.window=win
        #self.connect(self.window.widget().pw, 
        #            SIGNAL(self.window.widget().pw.sigMouseReleased), 
        #            self.pluginAlgorithm)
        self.window.widget().pw.plotItem.vb.sigClick.connect(self.pluginAlgorithm)
        self.dock.setWidget(Widget(self.dock))
        

    def pluginAlgorithm(self, e):
        """
        receive the event off release MouseEvent
        
        """
        if not self.x1val:
            self.x1val=e.x()
            self.dock.widget().x1.setText(str(self.x1val))
            self.dock.widget().x2.setText('')
            self.dock.widget().result.setText('')
            return
        
        x2=e.x()
        self.dock.widget().x2.setText(str(x2))
        chrom=self.window.widget().data[0] #take the first one
        res=chrom.integrationBtw(self.x1val, x2)
        self.dock.widget().result.setText(",success:".join([str(res[2]), str(res[3])]))
        self.x1val=0
        #self.reinitialize()
        
    def reinitialize(self):
        self.x1val=0
        self.dock.widget().x2.setText('')
        self.dock.widget().x1.setText('')
    
    
    def unload(self):
        for e in self.guiWidget:
            e.setParent(None)
            del e
        self.view.update()
         
    
class Widget(QWidget):
    def __init__(self, parent=None):
        QWidget.__init__(self, parent)
        self._setupUi()
    
    def _setupUi(self):
        self.x1=QLabel()
        self.x2=QLabel()
        self.result=QLabel()
        a=QFormLayout(self)
        a.addRow('x1:',self.x1)
        a.addRow('x2:', self.x2)
        a.addRow('result:', self.result)