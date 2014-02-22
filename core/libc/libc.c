/*
written by Marco
*/

#include <stdlib.h>
#include <stdio.h>
#include <float.h>


inline int 
max(int i, int j)
{
    if (i > j)
        return i;
    return j;
}
    

inline int 
min(int i, int j)
{
    if (i < j)
        return i;
    return j;
}


inline double
mean(double* a, int n)
{
    int i;
    double res = 0.0;
    for (i=0; i<n; i++) 
        res+=a[i];
    return res/n;
}


inline double 
mean_2(double* a, double* b, int n)
{
    int i;
    double res = 0.0;
    for (i=0; i<n; i++) 
        res+= a[i] * b[i];
    return res/n;
}


int 
binary_search(double *sorted_list, int low, int high, double element) 
{
    while (low < high) {
        int middle = low + (high - low)/2;
        if (element > sorted_list[middle])
            low = middle + 1;
        else if (element < sorted_list[middle])
            high = middle - 1;
        else
            return middle;
    }
    return -1;
}




int 
binary_search_d(int *sorted_list, int low, int high, int element) 
{
    while (low < high) {
        int middle = low + (high - low)/2;
        if (element > sorted_list[middle])
            low = middle + 1;
        else if (element < sorted_list[middle])
            high = middle - 1;
        else
            return middle;
    }
    return -1;
}


int 
bisect_left(double *a, double x, int lo, int hi)
{
    int mid;
    if (lo < 0)
       return -1;
    while (lo < hi)
    {
     mid = (lo+hi)/2;
     if (a[mid] < x)
         lo = mid+1;
     else 
        hi = mid;
    }
    return lo;
}


int
is_in(double *a, int n, double b)
{  
    int idx = binary_search(a, 0, n, b);
    if (idx != -1) 
        return 1;
    return 0;
}

int
is_in_d(int *a, int n, int b)
{
    int idx = binary_search_d(a, 0, n, b);
    if (idx != -1)
        return -1;
    return 0;
}



int 
int_cmp(const void *a, const void *b) 
{ 
    const int *ia = (const int *)a; // casting pointer types 
    const int *ib = (const int *)b;
    return *ia  - *ib;
}



int *
bisection(double* a, int n, double x, double minm, double maxm, int* out)
{
    int i, j, count = 0;
    i = bisect_left(a, x, 0, n);
    int *results = calloc(n, sizeof(int));

    if (i != n)
    {
        if (a[i] > maxm)
        {
            while (a[i] > maxm && i > 0)
                i-=1;
            while (a[i] >minm && i > 0)
            {
                results[count] = i;++count ;               
                i-=1;
            }
        }        
     
        if (a[i] < maxm && a[i] > minm)
        {
            results[count] = i; ++count;
            j=i;
            while (a[j] < maxm && j < n)
            {
                results[count]=j;++count;
                j+=1;
            }
            j=i;
            while (a[j] > minm && j > 0)
            {
                results[count] = j;++count;
                j-=1;
            }
        }
    }    
    else
        results[count] = n-1;

    results = realloc(results, sizeof(int) * count);
    *(out) = count;
    qsort(results, count, sizeof(int), int_cmp);
    return results;    
}



void 
resolution_adjustment(double* isomasses, // mass
                      double* isoprob, // prob
                      int n, //length
                      double errormass, //ppm *1e-6 
                      double limitp, //limitprob
                      double *out_isomasses, //array for results
                      double *out_isoprob) 
                      //int* size) //array for results
{
    /*
    merge peaks when the distance between them is inferior to the deltam parameter
    to test, but seems to be good...
    l : np.array of tuple (mass, prob) sorted !!!!!
    ppm: incertitude on the mass high res: generally (10/1e6)*peak.mass()
    fwhm:  for the convolution...to have a nice isotopic cluster
    */

    int count, count_final=0, i=0;
    double * tmp_masses = calloc(n, sizeof(double));
    double * tmp_prob = calloc(n, sizeof(double));
    //double * out_isomasses = calloc(n, sizeof(double)), *out_isoprob = calloc(n, sizeof(double));
    double mass, prob;
    
    while (i < n-1)
      {
        count = 0;
        while (isomasses[i+1]-isomasses[i] < errormass && i < n-2)
        {
            tmp_masses[count] = isomasses[i];
            tmp_prob[count] = isoprob[i]; 
            count++;
            
            tmp_masses[count] = isomasses[i+1];
            tmp_prob[count] = isoprob[i+1];
            count++;
            
            i++;
        }
        if (count != 0)
        {
            mass = mean_2(tmp_masses, tmp_prob, count);
            prob = mean(tmp_prob, count);
            free(tmp_masses); 
            free(tmp_prob);
            if (prob > limitp)
            {
              out_isomasses[count_final] = mass;
              out_isoprob[count_final] = prob;
              count_final++;
            }
        }   
        else
        {
            out_isomasses[count_final] = isomasses[i];
            out_isoprob[count_final] = isoprob[i];
            count_final++;            
            if (i == n-2) 
              {
                out_isomasses[count_final] = isomasses[n-1];
                out_isoprob[count_final] = isoprob[n-1];
              }
        }
        i++;
      }
      //realloc
      out_isomasses = realloc(out_isomasses, count_final * sizeof(double));
      out_isoprob = realloc(out_isoprob, count_final * sizeof(double));
}





// double **
// findIsotopicPeak(double *masses, 
                 // int n, 
                 // double *isomasses,
                 // double *isoprob, 
                 // int o, 
                 // double ppm,  
                 // double limitp)//, int decreaseOrder)
// {
   // /*main function
   // masses array ndim=1
   // rts array ndim=1
   // isos array of tuple
   // decrease not search
   // */
  // int i, j, idx, l, count=0;
  // double *isotopes = calloc(n, sizeof(double)); //if (!isotopes) return NULL;
  // double **results = calloc(n, sizeof(double*)); //if (!results) return NULL;
  // for (l=0; l<n; l++) 
    // results[l] = calloc(o, sizeof(double));
  
  // double **iso = NULL;
  
  // for (i=0; i<n; i++)
  // {
   
     // if (is_in(isotopes, n, masses[i])) 
        // continue;
     // iso = resolution_adjustment(isomasses, isoprob, o, masses[i]*ppm/1e6,  limitp);//may use ***
     // for (j=0; j < o; j++)
     // {
        // idx = binary_search(masses, 0, n, iso[j][0]);//use other function like bisection
        // if (idx == -1) 
          // continue;
        // isotopes[count] = masses[idx]; count++;
        // results[i][j] = masses[idx];
     // }
     // /*free iso memory*/
     // for (l=0;l<o;l++) 
        // free(iso[l]);
     // free(iso);
     // iso=NULL;
  // }

  // /*free isotopes */
  // free(isotopes); isotopes = NULL;
  // return results;
// }
