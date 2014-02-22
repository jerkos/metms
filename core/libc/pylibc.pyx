import numpy as np
cimport numpy as np

cdef extern from "stdlib.h":
    ctypedef unsigned long size_t
    void free(void *ptr)
    void *malloc(size_t size)
    void *realloc(void *ptr, size_t size)
   

cdef extern from "libc.h":
    #int binary_search(double *sorted_list, int low, int high, double element)
    #int binary_search_d(int *sorted_list, int low, int high, int element)
    #int  bisect_left(double *a, double x, int lo, int hi)
    #int is_in_d(int *a, int n, int b)
    #int int_cmp(void* a, void* b)
    int * bisection(double* a, int n, double x, double minm, double maxm, int* size)
#    void resolution_adjustment(double* isomasses,
#                          double* isoprob,
#                          int n,
#                          double errormass,
#                          double limitp,
#                          double *out_isomasses,
#                          double *out_isoprob)
   



cpdef np.ndarray[int, ndim=1] bisect (np.ndarray[double, ndim=1] inp, double m, double min_, double max_):
    """
    python definition of bisection
    """    
    cdef:
        int *res
        int i, size = 0
        list r = []
    res = bisection(<double*>inp.data, <int>inp.shape[0], m, min_, max_, &size)
    append = r.append
    for i from 0 <= i < size:
        append(res[i])
    free(res)
    return np.array(sorted(list(set(r))), dtype=int)


cpdef object massExtract(object spl, double mass, double ppm):
    cdef:
        int i, j, N=len(spl.spectra), size=0
        list intensity=[], rts=[]
        double diff = ppm * mass / 1e6
        double mi = mass - diff
        double mx = mass + diff
        np.ndarray[int, ndim=1] idx        
        
    spectra = spl.spectra
    for i in xrange(N):
        idx = bisect(spectra[i].x_data, mass, mi, mx)
        rts += [spectra[i].rtmin for x in xrange(<int>idx.shape[0])]          
        intensity += spectra[i].y_data[idx].tolist()
    return np.array(rts), np.array(intensity)