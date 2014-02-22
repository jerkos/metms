#! usr/bin/python
# -*- coding: utf-8 -*-


import os, subprocess, sys, time
from multiprocessing import cpu_count
from numpy import array, round

from controller.MetBaseControl import MSModel
from core import MetObjects as obj
from core.MetClustering import inSpectraFinder


class MSIntegrationModel(MSModel):
    """
    Allows integration of peak calling xcms
    
    """    
    def __init__(self, lspl, parent=None):
        """
        @xml_creation:wether to use only xcms (error) for  handling MRM data or no
        """
        MSModel.__init__(self, lspl, parent=parent)#have to put parent to None
        
        self.mode=self.model[0].kind
        
        if not all(spl.kind==self.mode for spl in self.model[:]):
            raise TypeError("all sample must have the same mode: HighRes or MRM")
            return
        
        self.filesToXCMS=self.model.getFiles() if self.mode=='HighRes' else []
        self.RCOMMAND = "Rscript"
        self.RFILE = "script.R"
        self.cmdline =" ".join([self.RCOMMAND, self.RFILE])
        self.XCMS_OUTPUT="peaks.pkl"
    
    
    def toGoodMzXML(self):
        """Transformation into a new xml"""
        for spl in self.model:
            xmlCreator = MSXmlCreationModel(spl)
            xmlCreator.writing_xml()
            filename=xmlCreator.get_new_file()
            self.filesToXCMS.append(filename)        
    
    
    def _erasingTraces (self): 
        """
        erase new transition file
        """
        print "removing temporary file ..."   
        if self.mode!='HighRes':
            for xml in self.filesToXCMS:
                try:
                    os.remove(xml)
                    print " ".join([xml, "removed..."])
                except IOError:
                    pass
        for f in (self.RFILE, self.XCMS_OUTPUT):
            try:
                os.remove(f)
                print " ".join([f, "removed..."])
            except OSError:
                pass

    
    def filesAsString(self, l):
        s=""
        for i, f in enumerate(l):
            s+="".join(['"',f,'"',","]) if i < len(l)-1 else "".join(['"',f,'"'])
        return s
    
    
    @staticmethod
    def sampleString(c, active):
        s=""
        for i in range (1, c+1):
            s+="class"+str(i)+"=levels(sampclass("+active+"))["+str(i)+"]"+"," if i < c\
             else "class"+str(i)+"=levels(sampclass("+active+"))["+str(i)+"]"
        return s
    
    
    def makeRscript(self, dir, selectedFiles, **kw):
        """
        dir is tuple 
        dir[1]:boolean if we work on directories or on files
        dir[2]; directory name
        selectedfiles:list containing names of files
        """
        t="library(xcms)\n"
        if dir[0]:
            t+= "".join(['cdffiles=list.files(path=',dir[1],', pattern=".cdf", all.files=FALSE, recursive=TRUE, full.names=TRUE, ignore.case=FALSE)\n'])
        else:
            t+= "".join(["cdffiles=c(",self.filesAsString(selectedFiles),")\n"])
        if kw["algorithm"]==0:
            fwhm=kw["fwhm"]
            step=kw["step"]
            steps=kw["steps"]
            mzdiff=kw["mzdiff"]
            snthresh=kw["snthresh"]
            max_=kw["max"]
            t+="".join(['xset<-xcmsSet(cdffiles, fwhm=',fwhm,', step=',step,', steps=',steps,
                        ', mzdiff=',mzdiff,', snthresh=', snthresh,', max=',str(max_),', nSlaves=',str(cpu_count()),')\n'])
        elif kw["algorithm"]==1:
            ppm = str(kw["ppm"])
            scanrange =kw["scanrange"]
            snthresh = str(kw["snthresh"])
            peakwidth=kw["peakwidth"]
            noise = str(kw["noise"])
            fitgauss = 'TRUE' if kw["fitgauss"] else 'FALSE'
            integrate = str(kw["integrate"])
            mzdiff = str(kw["mzdiff"])        
            t+="".join(['xset<-xcmsSet(cdffiles, method="centWave", ppm=',str(ppm),
                        ', scanrange=c(',str(scanrange[0]),','+str(scanrange[1]),'), snthresh=',str\
            (snthresh),', peakwidth=c(',str(peakwidth[0]),',',str(peakwidth[1]),
            '), noise=',str(noise),', fitgauss=',fitgauss,', integrate=', integrate\
            ,', mzdiff=', str(mzdiff),')\n'])
        active="xset"
        if kw["doGrouping"]:
            minfrac = str(kw["minfrac"])
            bw= str(kw["bw"])
            max = str(kw["max"])
            mzwid = str(kw["mzwid"])
            t+="".join(["xsetgp1<-group(xset, minfrac=",minfrac,", sleep=0, bw=",
                        bw,", max=",max,", mzwid=",mzwid,")\n"])
            active = "xsetgp1"
        if kw["doAlignment"]:
            if len(selectedFiles)>1:
                t+='xsetrt<-retcor(xsetgp1, method="obiwarp")\n'
                active = "xsetrt"
                t+="".join(["xsetgp2<-group(",active,",  minfrac=",minfrac,
                            ", sleep=0, bw=",bw,", max=",max,", mzwid=",mzwid,")\n"])
                active = "xsetgp2"
                t+="".join(["xset3 <-fillPeaks(",active,")\n"])
                active = "xset3"
            else:
                print ("Error, can no make retention alignment correction, only one sample analysed")
        if dir[0]:
            t+="".join(["reportab<-diffreport(",active,", ",self.sampleString(2, active),")\n"])
            t+="".join(['write.table(reportab, paste("matrice.csv"), sep=";")\n'])
        else:
            t+="".join(['write.table(peaks(',active,'), paste("',self.XCMS_OUTPUT,'"), sep=";")\n'])
        t+='q()'
        #print t
        return t
        
            
    
    
    def integrateWithR(self, **kw):
        if self.mode=='MRM':
            if self.model[0].msLevel == 2:
                self.toGoodMzXML()
            elif self.model[0].msLevel == 1:
                self.filesToXCMS += self.model.getFiles()
        code = self.makeRscript((False, None), self.filesToXCMS, **kw)
        with open(self.RFILE, 'w') as f:
            f.write(code)
        boolean=False
        if sys.platform.startswith("linux"):
            boolean=True
        process= subprocess.Popen(self.cmdline, shell=boolean)
        process.wait()
        self.getPeaks(**kw)
        #self._erasingTraces()
        
      
    def getPeaks(self, **kw):
        with open(self.XCMS_OUTPUT) as f:
            for i in range (2):#skip the header
                l=f.readline()
            while l != "":
                peak=l.split(';')
                massrange=round(array(map(float, [peak[1], peak[2], peak[3]])), decimals=4).tolist()
                rt, rtmin, rtmax = float(peak[4]), float(peak[5]), float(peak[6])
                try:
                    into, intf = float(peak[7]), float(peak[8])
                except ValueError:
                    into, intf = 0., 0.
                height=float(peak[9])
                nfile = peak[-1].rstrip()
                if kw['algorithm']==0:
                    sn=float(peak[12])
                else:
                    sn=float(peak[10])
                #chromatogram=None
                spl = self.model[int(nfile)-1]
                spl.rawPeaks.append(obj.MSChromatographicPeak((rt, rtmin, rtmax), 
                                                       massrange=massrange,
                                                       intinfo=(into, intf, sn, height),
                                                       spectra=spl.spectraInRTRange(rt, rtmin, rtmax),
                                                       sample=spl))
                l=f.readline()
        ###end with, Warning add some stuffs here
        isomasses=[]
        mode=spl.kind
        clusterLength=5
        if mode=='HighRes': #tuple(mass, prob, nmol) nmol for calculating 2M+Na+ for example
            m=[(1.0033548378, 0.0107), (2.003241988,0.), #C Element
               (1.006276746, 0.000115), (2.008224235,0.), #H Element
               (0.997034893, 0.00368), #N Element
               (1.004216878,0.00038), (2.004245778,0.00205), #O Element, P got no isotopes
               (0.99938781,0.0076), (1.99579614,0.0429), (3.99501019,0.0002)] #S Element
            for i in range(1, clusterLength+1):#setting isotopic stuffs 
                isomasses+=([(x[0]*i, x[1]**i) for x in m if x[0]*i < clusterLength])
        else:
            isomasses = [(float(i), 0.) for i in xrange(1, clusterLength)]#map(float, range(1, clusterLength+1))            
        t=time.clock()
        for spl in self.model.isamples():
            spl.rawPeaks= inSpectraFinder(spl.rawPeaks, isomasses)#, ppm=spl.ppm)
            spl.rawPeaks.sort(key = lambda x:x.mass())
            if spl.restriction is not None:
                l = self.goodPeaksRegardsToRestriction(spl.rawPeaks, spl.restriction[0], spl.restriction[1])
                spl.rawPeaks = l
        print "Elapsed time inspectraFinder:%s"%str(time.clock()-t)
        
        
    def goodPeaksRegardsToRestriction(self, peaks, min_, max_):
        #not classed by rt
        l = obj.MSPeakList(sample=peaks.sample)
        for p in peaks.ipeaks():
            if p.rt >min_ and p.rt <max_:
                l.append(p)
        return l
            


class MSXmlCreationModel(MSModel):
    def __init__(self, spl):
        MSModel.__init__(self, spl)
               
    def writing_xml(self):
        #f=open(self.filename,'w')
        with open(self.model.xmlfile+'.txt', 'w') as f:      
            f.write(self.model.header)
            for i, spectra in enumerate(self.model.spectra):
                f.write("<scan num=\""+str(i+1)+"\"\n")
                f.write("msLevel=\"1\"\n")
                f.write("peaksCount=\""+str(len(spectra.x_data))+"\"\n")
                #f.write('scanType="MRM"\n')
                f.write("retentionTime=\"PT"+str(spectra.rtmin)+"S\">\n")
                f.write("<peaks precision=\"32\"\n")
                f.write("byteOrder=\"network\"\n")
                f.write("pairOrder=\"m/z-int\">"+str(spectra.encode64())+"</peaks>\n")
                f.write("</scan>\n")
            f.write("</msRun>\n")
            f.write("</mzXML>")   
    
    def get_new_file(self):
        return "".join([self.model.xmlfile,".txt"])
           
                 