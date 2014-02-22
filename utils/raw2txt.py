#!/home/inorton/bin/pywin
import comtypes, comtypes.client
from ctypes import *
from comtypes.automation import *
import sys
import numpy

# GetMassListFromScanNum(long FAR* pnScanNumber, LPCTSTR szFilter,  
# long nIntensityCutoffType, long nIntensityCutoffValue,  
# long nMaxNumberOfPeaks, BOOL bCentroidResult, 
# VARIANT FAR* pvarMassList, 
# VARIANT FAR* pvarPeakFlags,  
# long FAR* pnArraySize)

#Default values for MSFileReader.GetMassListFromScanNumber call:
scanNum = 1
scanFilter = u''
scanIntensityCutoffType = 0 # 0 = none, 1=Abs, 2=Rel. to basepk
scanIntensityCutoffValue = 0
scanMaxNumberOfPeaks = 0
scanCentroidResult = 0
pl = VARIANT() #Unused variable
# ml set up later
arsize = c_long()

minmz=600
maxmz=1000



if (len(sys.argv) < 2):
    print ("you loose... forgot to enter a filename ?")
    sys.exit(-1)
else:
    fInName = sys.argv[1]
    
#~ if (len(sys.argv) < 3):
    #~ fOutName = fInName + ".csv"
#~ else:
    #~ fOutName = sys.argv[2]

print "in File: "+fInName

# Set up the COM object interface
xr = comtypes.client.CreateObject('MSFileReader.XRawfile')
xr.open(fInName)
res = xr.SetCurrentController(0,1)
print "res: " + str(res)
ns = c_long()
xr.GetNumSpectra(ns)
print "Num spectra: "+str(ns.value)

data = numpy.array('f')
outStrings = []

for i in range(1,ns.value+1):
    ml = VARIANT()
    xr.GetMassListFromScanNum(
        c_long(i),scanFilter,
        c_long(scanIntensityCutoffType),
        c_long(scanIntensityCutoffValue),
        c_long(scanMaxNumberOfPeaks),
        c_long(scanCentroidResult),
        c_double(0),
        ml,pl,arsize
        )
    data = numpy.array(ml.value)
    rng = [(data[0]>=minmz)&(data[0]<=maxmz)]
    dataout = numpy.array((data[0][rng],data[1][rng])).transpose()
    of = file(fInName+'.'+str(i)+'.csv','w',arsize.value)
    of.write('M/Z,Intensity\n')
    for item in dataout: of.write("%.3f,%.3f\n" % (item[0],item[1]))
    of.flush()
    of.close()
    del(ml,of)