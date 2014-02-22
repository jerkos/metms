
#include <stdlib.h>
#include <stdio.h>
#include <math.h>
#include <float.h>

int max(int a, int b);
int min(int a, int b);
double mean(double* a, int n);
double mean_2(double* a, double* b, int n);
int binary_search(double *sorted_list, int low, int high, double element);
int binary_search_d(int *sorted_list, int low, int high, int element);
int  bisect_left(double *a, double x, int lo, int hi);
int is_in_d(int *a, int n, int b);
int int_cmp(const void *a, const void *b);
int* bisection(double* a, int n, double x, double minm, double maxm, int size);
void resolution_adjustment(double* isomasses, // mass
                      double* isoprob, // prob
                      int n, //length
                      double errormass, //ppm *1e-6 
                      double limitp, //limitprob
                      double *out_isomasses, //array for results
                      double *out_isoprob);