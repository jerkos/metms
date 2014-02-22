import numpy as np
cimport numpy as np
from time import clock
cimport cython


cdef extern from "stdlib.h":
    ctypedef unsigned long size_t
    void free(void *ptr)
    void *malloc(size_t size)
    void *realloc(void *ptr, size_t size)


cdef extern from "masses.h":
    cdef struct xyarray:
        double* x
        double* y
        int length


    cdef struct scan:
        double *mass
        int *intensity
        int length
        double rt


    cdef struct goodMasses:
        double  mz
        double  mzmin
        double  mzmax

    int bisect_left(double *a, double x, int lo, int hi)
    int int_cmp(void *a, void *b)
    int * bisection(double* a, int n, double x, double minm, double maxm, int *size)
    double getClosest(double* a, int length, double v)
    int is_included(goodMasses* outMasses, int length, goodMasses current)
    goodMasses* findInterestingMasses(scan* scans, int scanLength, int expectedSize, int minTimeSpan, double ppm)
    scan getEic(scan* scans, int length, double mz, double minmz, double maxmz)


@cython.boundscheck(False)
@cython.wraparound(False)
cpdef object massExtraction(object sample, float mz, float minmz, float maxmz):
    cdef int n = len(sample.spectra), i
    cdef scan xy
    cdef scan* scans = <scan*> malloc(n * sizeof(scan))
    cdef scan s
    cdef np.ndarray[np.float_t, ndim=1] xf
    cdef np.ndarray[int, ndim=1] yf
    t = clock()
    for i in xrange(len(sample.spectra)):
        scans[i] = s
        scans[i].mass = <double*> (<np.ndarray>sample.spectra[i].x_data).data
        scans[i].intensity = <int*> (<np.ndarray>sample.spectra[i].y_data).data
        scans[i].length = <int> sample.spectra[i].x_data.shape[0]
        scans[i].rt = sample.spectra[i].rtmin
    xy = getEic(scans, n, mz, minmz, maxmz)
    xf = np.zeros(xy.length)
    yf = np.zeros(xy.length, dtype=int)
    for i from 0 <= i < xy.length:
        xf[i] = xy.mass[i]
        yf[i] = xy.intensity[i]
    free(scans)
    #scans = None    
    print "Time elapsed:", clock() - t    
    return xf, yf


cpdef object pyGoodMasses(object sample, int expectedSize, int minTimeSpan, float ppm=10.):
    cdef int n = len(sample.spectra), i
    cdef goodMasses *xy
    cdef scan* scans = <scan*> malloc(n * sizeof(scan))
    cdef scan s
  
    t = clock()
    for i in xrange(len(sample.spectra)):
        scans[i] = s
        scans[i].mass = <double*> (<np.ndarray>sample.spectra[i].x_data).data
        scans[i].intensity = <int*> (<np.ndarray>sample.spectra[i].y_data).data
        scans[i].length = <int> sample.spectra[i].x_data.shape[0]
        scans[i].rt = sample.spectra[i].rtmin
    #findInterestingMasses(struct scan* scans, int scanLength, int expectedSize, int minTimeSpan, double ppm)
    xy = findInterestingMasses(scans, n, 1000, minTimeSpan, ppm)
    #print <int>xy.length
    free(scans)
    return False