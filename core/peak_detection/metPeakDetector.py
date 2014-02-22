from core.MetObjects import MSPeakList
from controller.MetBaseControl import MSModel


from numpy.fft import rfft, irfft
from numpy import fliplr

xcorr = lambda x,y : irfft(rfft(x)*rfft(fliplr(y)))

class MSPeakDetector(MSModel):
    
    def __init__(self, spectra, **k):
        MSModel.__init__(self, spectra)
        #parameters
        self.minSpanScan=k.get('minSpanScan', 5)
        self.applySmoothing=k.get('applySmoothing', False)
        self.ppm=k.get('ppm', self.model[0].ppm)/1e6
    
    
    def __call__(self):
        pkl=MSPeakList(sample=spectra[0].sample)
        for i in xrange (len(self.model)-1):
            matches=[]
            for j in xrange(len(self.model[i].x_data)):
                if abs(self.model[i].x_data[j] - matches[0] :
                    continue
                rtmin=s.rt
                matches=[]
                rtmax=None
                i+=1
                c=0
                while i < len(self.model):

                    matching=self.model[i].massPeakInRange(self.model[i].x_data[j])
                    if not matching:
                        break
                    matches.append((self.model[i].x_data[j], 
                                    self.model[i].y_data[j], 
                                    self.model[i].rt))
                    c+=1
                if c < self.minSpanScan:
                    break
                maxHeight=max([m[1] for m in matches])
                pkl.append(MSChromatographicPeak(rtinfo=([m[2] for m in matches][[m[1] for m in matches].index(maxHeight)],
                                                          rtmin, 
                                                          rtmax))
    
