#!usr/bin/python
# -*- coding: utf-8 -*-

__version__ = "$Revision:1" 
__author__ = ("marco", "cram@hotmail.fr")


import os.path as path
import os, glob

from PyQt4.QtGui import (QFileDialog, QApplication, QLineEdit, QComboBox, QCheckBox, QDialog,
                         QFormLayout, QDialogButtonBox, QPushButton, qApp)
from PyQt4.QtCore import (Qt, pyqtSlot, pyqtSignal, SIGNAL, QThread, QSettings, QObject)
paramikoSupport=True
try:
    from paramiko import (SSHClient, AutoAddPolicy, SSHException, 
                          AuthenticationException, BadHostKeyException)
except ImportError:
    paramikoSupport=False
from core.MetIntegration import MSIntegrationModel
from controller.MetBaseControl import MSDialogController , MSThreadBasis
#from core import MetProcessing as proc, MetObjects as obj
from gui.dialog.MetIntegrationGui import MSCentWaveDialog, MSMatchedFilteredDialog
from gui.MetBaseGui import MSWebBrowser


class MSIntegrationController(MSDialogController):
    """
    Class controller, (calls a class for peak_picking and alignment)    
    __specialsConn__ = {"clicked()":('fileDialogButton', 'dial')}
    __createSample__ = 'True'
    __specialsFunc__ = "setSampleColors"
    __getParam__ = 'getParameters'
    __threadConn__ = {'status_message': 'showInStatusBar', 'update_pb':'updateProgressBar'}
    __endFunc__ = "setModels"
    """
    
    plateformSite = 'http://serviclust.toulouse.inra.fr/ganglia/?r=hour&s=descending&c=compute'
    
    def __init__(self,lspl, win, creation):
        MSDialogController.__init__(self, lspl, win, creation)
        QObject.connect(self.view.lineEdit, SIGNAL("textChanged(const QString &)"), self.checkLineEdit)
        if paramikoSupport:
            try:
                QObject.connect(self.view.parallel, SIGNAL("clicked()"), self.showSSHConnect)
            except AttributeError:
                pass
        self.checkLineEdit("")
        self.view.exec_()

    
    def _initialize(self):
        """
        called in __init__ of msdialogcontroller
        
        """
        settings=QSettings('INRA/INSA', '-'.join([qApp.instance().APPLICATION_NAME_STR,
                                                  qApp.instance().VERSION_STR]))
        
        if isinstance(self.view, MSMatchedFilteredDialog):
            settings.beginGroup("matchedFilteredDialog")
            self.view.lineEdit_2.setText(settings.value("lineEdit_2", "30").toString())
            self.view.lineEdit_4.setText(settings.value("lineEdit_4", "2").toString())       
            self.view.lineEdit_5.setText(settings.value("lineEdit_5", "0.5").toString())
            self.view.lineEdit_6.setText(settings.value("lineEdit_6", "3").toString())
            self.view.lineEdit_3.setText(settings.value("lineEdit_3", "0.1").toString())
            self.view.spinBox.setValue(settings.value("spinBox", 5).toInt()[0])
            settings.endGroup()

        elif isinstance(self.view, MSCentWaveDialog):
            self.view.lineEdit_2.setText("300-3200")
            self.view.lineEdit_4.setText("10-22")       
            self.view.lineEdit_5.setText("1000")
            self.view.lineEdit_6.setText("1.2")
            self.view.spinBox.setValue(10)
            self.view.spinBox_2.setValue(10)
            self.view.checkBox.setChecked(True)
            
        self.view.lineEdit_7.setText("0.8")
        self.view.lineEdit_8.setText("5")
        self.view.lineEdit_9.setText("20")
        self.view.lineEdit_10.setText("0.002")
        self.view.obiwarp.setChecked(True)
        self.view.gb_2.setChecked(False)
        self.view.gb_3.setChecked(False)

    
    @pyqtSlot() 
    def showSSHConnect(self):
        self.view.close()
        qApp.instance().view.showInformationMessage("Check resources availability", 
                                              "Please, check resources of the cluster availability \
                                              in order to select the best queue")
        web = MSWebBrowser(self.plateformSite, parent=qApp.instance().view)
        qApp.instance().view.addMdiSubWindow(web)
        return SSHHandle(self, parent=self.view).show()
    
    
    @pyqtSlot(str)
    def checkLineEdit(self, string):
        line = str(self.view.lineEdit.text()).split(';')
        if len(line) <2:
            self.view.gb_2.setEnabled(False)
            self.view.gb_3.setEnabled(False)
        else:
            self.view.gb_2.setEnabled(True)
            self.view.gb_3.setEnabled(True)

    
    def getParameters(self):    
        """
        will get all the parameters, 
        make the difference between 
        the two integration algorithm
        
        """
        settings=QSettings('INRA/INSA', '-'.join([qApp.instance().APPLICATION_NAME_STR,
                                                  qApp.instance().VERSION_STR]))
        
        if isinstance(self.view, MSMatchedFilteredDialog):
            self.parameters["fwhm"]=str(self.view.lineEdit_2.text())
            self.parameters["step"]=str(self.view.lineEdit_3.text())
            self.parameters["steps"]=str(self.view.lineEdit_4.text())
            self.parameters["mzdiff"]=str(self.view.lineEdit_5.text())
            self.parameters["snthresh"]=str(self.view.lineEdit_6.text())
            self.parameters["max"]=str(self.view.spinBox.value())
            self.parameters["algorithm"]=0
            #start change
            settings.beginGroup("matchedFilteredDialog")
            settings.setValue("lineEdit_2", self.parameters["fwhm"])
            settings.setValue("lineEdit_4", self.parameters["steps"])       
            settings.setValue("lineEdit_5", self.parameters["mzdiff"])
            settings.setValue("lineEdit_6", self.parameters["snthresh"])
            settings.setValue("lineEdit_3", self.parameters["step"])
            settings.setValue("spinBox", int(self.parameters["max"]))
            settings.endGroup()
        
        elif isinstance(self.view, MSCentWaveDialog):
            self.parameters["scanrange"]=[float(x) for x in self.view.lineEdit_2.text().split('-')]
            self.parameters["integrate"]=1 if self.view.lineEdit_3.isChecked()else 0
            self.parameters["peakwidth"]=[float(x) for x in self.view.lineEdit_4.text().split('-')]
            self.parameters["noise"]=int(self.view.lineEdit_5.text())
            self.parameters["mzdiff"]=float(self.view.lineEdit_6.text())
            self.parameters["ppm"]=int(self.view.spinBox.value())
            self.parameters["snthresh"]=int(self.view.spinBox_2.value())
            self.parameters["fitgauss"]=[self.view.checkBox.isChecked()]
            self.parameters["algorithm"]=1
        #common parameters between the to algorithm
        self.parameters['doGrouping']=True if self.view.gb_2.isChecked()else False
        if self.parameters['doGrouping']:
            self.parameters["minfrac"]=float(self.view.lineEdit_7.text())
            self.parameters["bw"]=int(self.view.lineEdit_8.text())
            self.parameters["max"]=int(self.view.lineEdit_9.text())
            self.parameters["mzwid"]=float(self.view.lineEdit_10.text())
        self.parameters["doAlignment"]=True if self.view.gb_3.isChecked() else False
        if self.parameters["doAlignment"]:
            if self.view.obiwarp.isChecked():
                self.parameters["method"] ='obiwarp'
            if self.view.loess.isChecked():
                self.parameters["method"] ='loess'
        #setting parent
        #self.parameters['parent']= self.view.parent()


    @pyqtSlot()
    def startTask(self):  
        MSDialogController.startTask(self)
        self.task = MSIntegrationThread(self.sampleList, **self.parameters)
        
        def begin():
            self.view=None
            self.task.start()
            self.task.exec_()
        self.task.begin = begin
        
        #to avoid QObject::killTimers error, wait for the dialog to be deleted
        QObject.connect(self.view, SIGNAL('destroyed(QObject *)'), self.task.begin)
        QObject.connect(self.task, SIGNAL("started()"),qApp.instance().view.to_indetermined_mode)
        QObject.connect(self.task, SIGNAL("finished()"),self.setModels)
        QObject.connect(self.task, SIGNAL("finished()"),qApp.instance().view.to_determined_mode)
        self.view.close()
            

    
    
    @pyqtSlot()
    def setModels(self):
        """
        end processing 
        
        """
        qApp.instance().view.comparativeTableView.setModel(MSDialogController.actualizePeakModelComparative())
        qApp.instance().view.showInformationMessage("Integration Done", "Integration process finished...")
        qApp.instance().view.tabWidget.setCurrentIndex(1)
         
            

class MSIntegrationThread(MSThreadBasis):
    """integration thread progress in indeterminate mode"""
    
    status_message = pyqtSignal(str)
    
    def __init__(self, lspl, **kw):
        MSThreadBasis.__init__(self)#kw.get('parent',None))
        self.lspl =lspl
        self.kw = kw
    
    def run(self):
        integrator = MSIntegrationModel(self.lspl, parent=self)
        self.emit(SIGNAL("status_message"), "Getting peaks from xcms...")
        integrator.integrateWithR(**self.kw)
        
    #def __del__(self):
    #    self.terminate()
    #    QThread.wait()

                       



class SSHHandle(QDialog):
        
    queueItems=["workq", "longq", "bigmemq"]
    
    def __init__(self, controller, parent=None):
        
        QDialog.__init__(self, parent)
        self.setModal(False)
        self.controller = controller
        self.selectedFiles=[]
        self.directory =""
        self.setWindowTitle("Information Connexion ...")
        self.setupUi()
        self.connect(self.buttonBox, SIGNAL("accepted()"), self.startConnection)
        self.connect(self.buttonBox, SIGNAL("rejected()"), self.close)
        self.connect(self.checkDir, SIGNAL("clicked()"), self.openDirDialog)
        self.populateDialog()
        self.SHELL_SCRIPT= 'xcms.sh'
        self.XCMS_SCRIPT = 'script.R'
    
    def setupUi(self):
        f =QFormLayout(self)
        self.username =QLineEdit(self)
        self.password = QLineEdit(self)
        self.password.setEchoMode(QLineEdit.Password)
        self.host = QLineEdit(self)
        self.dirName = QLineEdit(self)
        self.checkDir = QPushButton("set directory to upload", self)
        self.mail = QLineEdit()
        self.mail.setToolTip("if you enter your email now, metms will be able to get the result on the cluster, if empty you will have to do by yourself")
        self.queue = QComboBox(self)
        self.queue.setToolTip("Each queues correspond to a series of nodes of the same power workq<longq<bigmemq")
        self.queue.addItems(self.queueItems)
        self.interactiveSession=QCheckBox("start an interactive session")
        f.addRow("username:", self.username)
        f.addRow("password:", self.password)  
        f.addRow("hostname:", self.host)
        f.addRow("email:", self.mail)
        f.addRow(self.checkDir, self.dirName)
        f.addRow("select a queue:", self.queue)
        f.addRow("", self.interactiveSession)
        
        self.buttonBox = QDialogButtonBox(self)
        self.buttonBox.setStandardButtons(QDialogButtonBox.Ok|QDialogButtonBox.Cancel)
        f.addRow("", self.buttonBox)
    
    
    def populateDialog(self):
        with open(os.path.normcase('config/config/login.txt')) as f:
            info=f.readline().split(';')
            self.username.setText(info[0])
            self.password.setText(info[1])
            self.host.setText(info[2])
            self.mail.setText(info[3])
    
    
    def openDirDialog(self, flags='*.CDF'):
        """
        setting the selected files 
        """
        directory  = QFileDialog.getExistingDirectory(self.parent(), "Select one master directory")
        if directory:
            try:
                self.view.lineEdit.setText(directory)
            except AttributeError:
                pass
            if not glob.glob(os.path.normcase(str(directory)+'/'+flags)):
                self.dir=True
                subdir =os.listdir(directory)
                for d in subdir:
                    self.selectedFiles+= glob.glob(os.path.normcase("".join([str(directory),'/', d,'/',flags])))
            else:
                self.selectedFiles+= ["".join([self.directory,'/',x]) for x in map(os.path.normcase, glob.glob(str(directory)+'/'+flags))]
                self.dir=False
            self.directory = str(directory)
            self.dirName.setText(directory)     
            
    
    
    def startConnection(self): 
        """
        connection to remote server
        can launch a thread checking every minute your mailbox...
        """
        #if not self.directory:return
        #self.parent().close()
        self.close()
        client = SSHClient()
        client.set_missing_host_key_policy(AutoAddPolicy())
        try:
            client.connect(str(self.host.text()), username=str(self.username.text()), password=str(self.password.text()))
        except SSHException: qApp.instance().showErrorMessage("Error", "The ssh session could not be established")
        except AuthenticationException: qApp.instance().showErrorMessage("Error","Authentication failed")
        except BadHostKeyException: qApp.instance().showErrorMessage("Error", "the server's host key could not be verified")
        
        sftpCp = self.cleaningRepository(client)
        if sftpCp:
            sftp = client.open_sftp()
            self.sftpCopying(sftp)
            sftp.close()
        else:
            self.retrieveDirTree(c, out)
        self.makeRScript(client)
        self.makeShellScript(client)
        if self.interactiveSession.isChecked():
            import interactive
            print ('invoking a shell')
            chan = client.invoke_shell()
            chan.send('bash\n')
            interactive.interactive_shell(chan)
            chan.close()
        else:
            self.launchCommand(client)
        client.close()
        #self.cleaningUp()
    
    def retrieveDirTree(self,c, out):
        """
        the command ls -d does not work it would have been very interesting to use it
        """
        self.directory = maindir=[x for x in out.read().split('\n') if x not in ['script.R', 'xcms.sh'] and not x.startswith('xcms')][0]        
        in_, out_, err_ = c.exec_command("".join(['cd work/', maindir, ' && ls']))
        string=out_.read()
        self.dir=False if all([x.endswith('cdf') for x in string.split('\n')[:-1] ]) else True        
        for f in string.split('\n')[:-1]:
            self.selectedFiles+= ["".join([maindir,'/',f])]

            
        
    def cleaningRepository(self, c):
        in_, out, err =c.exec_command('cd work/ && ls')
        res = qApp.instance().view.showWarningMessage("Non Empty remote repository", 
                                                   "the remote repository is not empty, do you want to remove all files?")
        if res!=4194304:
            #c.exec_command('cd work/ && rm -rf *')#to much agressive
            try:
                c.exec_command('cd work && rm %s && rm %s'%(self.XCMS_SCRIPT, self.SHELL_SCRIPT))
            except Exception:
                pass
            return True
        return False
                   
    
    def makeRScript(self, client):
        remotedir=self.controller.goodName(self.directory).split('/')[-1]
        self.controller.getParameters()
        model = MSIntegrationModel(self.controller.model, **self.controller.parameters)
        code=model.makeRscript((self.dir, remotedir), self.selectedFiles)
        with open(self.XCMS_SCRIPT, 'w') as f:
            f.write(code)
        print "putting new script"
        user = str(self.username.text())
        sftp=client.open_sftp()
        sftp.put(self.XCMS_SCRIPT, "".join(['/work/',user, '/', self.XCMS_SCRIPT]))
        sftp.close()
    
    
    def sftpCopying(self, sftp):
        if not hasattr(self, 'dir'):
            return
        user = str(self.username.text())
        print 'user', user
        remotedir=self.controller.goodName(self.directory).split('/')[-1]
        sftp.mkdir("".join(['/work/', user, '/', remotedir]))
        if self.dir:
            for subdir in os.listdir(self.directory):
                sftp.mkdir("".join(['/work/',user,'/', remotedir,'/',subdir]))
            for f in self.selectedFiles:
                gn =self.controller.goodName(f)
                subdir, name= gn.split('/')[-2], gn.split('/')[-1]
                print "copying: %s, to: /work/%s"%(name, name)
                sftp.put(f,"".join(['/work/',user,'/',subdir,'/', name]))
        else:
            for f in self.selectedFiles:
                name= self.controller.goodName(f).split('/')[-1]
                print "copying: %s, to: '/work'"%name
                sftp.put(f,"".join(['/work/',user,'/',remotedir,'/',name]))
    
    
    
    def makeShellScript(self, c):
        user = str(self.username.text())
        q=str(self.queue.currentText())
        if q == 'longq':
            cores = '24'
        elif q == 'workq':
            cores='8'
        elif q == 'bigmemq':
            cores='32'
        string="".join(['#!/bin/sh\n#$-q ',q,
                        '\n#$-M ',str(self.mail.text()),
                        '\n#$-m ea\n#$-pe parallel_smp ',
                        cores,'\nRscript script.R'])
        with open(self.SHELL_SCRIPT, 'w') as f:
            f.write(string)
        sftp =c.open_sftp()
        sftp.put(self.SHELL_SCRIPT, "".join(['/work/',user,'/', self.SHELL_SCRIPT]))
        sftp.close()
    
    
    def launchCommand(self, c):
        """
        does not work...
        launch command by the interactive way
        """
        user = str(self.username.text())
        print ("Launching the job...")
        #session = c.get_transport().open_session()
        #session.exec_command('qsub work/xcms.sh\n')
        c.exec_command('qsub work/%s'%self.SHELL_SCRIPT)
        #while session.recv_ready():
        #    print "hola"
        #    print session.recv(9999)
    
        #string=chan.recv(9999)
        #print string
        #c.exec_command("".join(['cd work && qsub',self.SHELL_SCRIPT]))
        #print "launch qstat"
        #in_, out, err=c.exec_command('qstat -u '+user)
        #import re
        #s = out.read()
        #print "output qsub", s
        #regexp = re.compile('.+(\d+).+')
        #m = regexp.match(s)
        #job_id = m.group(1)
        #print "job_id",job_id
        #c.exec_command("".join(['qalter -R y', job_id]))
       
        #the launch the email thread
#        if self.mail.text():
#            from utils.MetHelperFunctions import MSMailThread
#            thread = MSMailThread(user= self.mail.text(), passw='Cram@86', server='imap.gmail.com')
#            self.connect(thread, SIGNAL('finished()'), self.getSftp)
#            thread.start(); thread.exec_()    
    
    
    def getSftp(self):
        client = SSHClient()
        client.set_missing_host_key_policy(AutoAddPolicy())
        try:
            client.connect(str(self.host.text()), username=str(self.username.text()), password=str(self.password.text()))
        except SSHException: qApp.instance().showErrorMessage("Error", "The ssh session could not be established")
        except AuthenticationException: qApp.instance().showErrorMessage("Error","Authentication failed")
        except BadHostKeyException: qApp.instance().showErrorMessage("Error", "the server's host key could not be verified")
        sftp = client.open_sftp()
        sftp.get('/work/matrice', './matrice')
        sftp.close()
        client.close()
        
    
    
    def cleaningUp(self):
        try:
            os.remove(self.SHELL_SCRIPT)
            os.remove(self.XCMS_SCRIPT)
        except IOError:
            print ("unable to erase xcms and shell script")
    
    
  
