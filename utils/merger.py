import sys, os
from io import open
from core.MetObjects import MSSample, MSSampleList

class MSXmlCreationModel(object):
    def __init__(self, spl, filename):
        self.model = spl
        self.filename=filename
               
    def writing_xml(self):
        #f=open(self.filename,'w')
        with open(self.filename, 'w') as f:      
            f.write(self.model.header)

            for i, spectra in enumerate(self.model.spectra):
                f.write("<scan num=\""+str(i+1)+"\"\n")
                f.write("msLevel=\"1\"\n")
                f.write("peaksCount=\""+str(len(spectra.x_data))+"\"\n")
                #f.write('scanType="MRM"\n')
                f.write("retentionTime=\"PT"+str(spectra.rt)+"S\">\n")
                f.write("<peaks precision=\"32\"\n")
                f.write("byteOrder=\"network\"\n")
                f.write("pairOrder=\"m/z-int\">"+str(spectra.encode64())+"</peaks>\n")
                f.write("</scan>\n")
            f.write("</msRun>\n")
            f.write("</mzXML>")   
    
    def get_new_file(self):
        return "".join([self.model.xmlfile,".txt"])

import numpy as np
def spectraMerger(spl, errorRt=1.):
    longestOne = spl[0]#sorted(spl, key=lambda x:len(x.spectra))[-1]
    others = spl[1:]#[s for s in spl if s!=longestOne]
    treated =set()
    for spectrum in longestOne.spectra:
        for sample in others:
            spectrum_ = sorted(sample.spectra, key=lambda x:abs(x.rt - spectrum.rt))[0]
            if spectrum_ in treated:
                continue
            #print "same rt ?", spectrum.rt, spectrum_.rt            
            spectrum.x_data = np.hstack((spectrum.x_data, spectrum_.x_data))
            spectrum.y_data = np.hstack((spectrum.y_data, spectrum_.y_data))
            treated.add(spectrum_)
    return longestOne

def createMergedXml(filename, spl):
    s = spectraMerger(spl)
    xmlcreator = MSXmlCreationModel(s, filename)
    xmlcreator.writing_xml()
                
        
def merge(filenames):
    sampleList = MSSampleList(kind='MRM')
    n = [s.split('-')[-1].split('.')[0][1:] for s in filenames]
    print n
    for f in filenames:
        s = MSSample(os.path.normcase(f), kind='MRM')
        s.loadMZXMLData()
        sampleList.append(s)
   
    mergedSampleName = "-".join(n)+".mzXML"
    createMergedXml(mergedSampleName, sampleList)

if __name__ =='__main__':
    base = sys.argv[1]
    startPoint = int(sys.argv[2])
    max_ = int(sys.argv[3])
    allfiles = ["".join([base, str(i), '.mzXML']) for i in xrange(startPoint, max_+1)]
    realfiles =[]
    for f in allfiles:
        if os.path.exists(f):
            realfiles.append(f)
    
    for i in xrange(0, len(realfiles), 3):
        print realfiles[i:i+3]
        merge(realfiles[i:i+3])