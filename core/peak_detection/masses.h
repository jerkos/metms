#include <Python.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <math.h>
#include <float.h>


#undef TRUE
#define TRUE 1
#undef FALSE
#define FALSE 0


struct xyarray {
    double* x;
    double* y;
    int length;
};


struct scan {
    double *mass;
    int *intensity;
    int length;
    double rt;
};

struct goodMasses {
    double  mz;
    double  mzmin;
    double  mzmax;
};


struct feature {
    double mz;
    double mzmin;
    double mzmax;
    double rt;
    double rtmin;
    double rtmax;
    double sn;
    double area;
};

int bisect_left(double *a, double x, int lo, int hi);
int int_cmp(const void *a, const void *b);
int * bisection(double* a, int n, double x, double minm, double maxm, int *size);
double getClosest(double* a, int length, double v);
int is_included(struct goodMasses* outMasses, int length, struct goodMasses current);
struct goodMasses* findInterestingMasses(struct scan* scans, int scanLength, int expectedSize, int minTimeSpan, double ppm);
struct scan getEic(struct scan* scans, int length, double mz, double minmz, double maxmz);
