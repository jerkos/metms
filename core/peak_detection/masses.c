#include "masses.h"

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
int_cmp(const void *a, const void *b) 
{ 
    const int *ia = (const int *)a; // casting pointer types 
    const int *ib = (const int *)b;
    return *ia  - *ib;
}



int *
bisection(double* a, int n, double x, double minm, double maxm, int *size)
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
                //indexes.insert(0, i)
                results[count] = i;count++ ;               
                i-=1;
            }
        }        
        if (a[i] < minm)
        {
            while (a[i]< minm)
                i+=1;
            while (a[i] <maxm)
            {
                results[count] = i;count++;                
                //indexes.append(i)                
                i+=1;
            }
        }        
        if (a[i] < maxm && a[i] > minm)
        {
            results[count] = i;count++;
            j=i+1;
            while (j < n && a[j] < maxm)
            {
                results[count]=j;count++;
                j+=1;
            }
            j=i-1;
            while (j > 0 && a[j] > minm)
            {
                results[count] = j;count++;
                j-=1;
            }
        }
    }    
    else
        results[count] = n-1;
    *size = count;
    results = realloc(results, sizeof(int) * count);
    qsort(results, count, sizeof(int), int_cmp);
    return results;    
}

double
getClosest(double* a, int length, double v)
{
    int i, closest=1e6, value=0;
    for (i=0; i < length; i++)
    {
        if (abs(a[i] - v) < closest)
        {
            closest = abs(a[i] - v);
            value = a[i];
        }
    }
    return value;
}
        

int
is_included(struct goodMasses* outMasses, int length, struct goodMasses current)
{
    int i;
    for(i=0; i<length; i++)
    {
        if (current.mzmin > outMasses[i].mzmin)
            return 1;
    }
    return 0;
}
        
        

struct goodMasses* 
findInterestingMasses(struct scan* scans, int scanLength, int expectedSize, int minTimeSpan, double ppm)
{
    printf("Detecting mass span at %f ppm on minimum %d scans...\n", ppm, minTimeSpan);
    int i, j, k, count_final = 0;
    double minm, maxm, m;
    struct goodMasses* outMasses = NULL;//malloc(1 * sizeof(struct goodMasses));
    
    for(i=0; i < scanLength; i++)
    {
        //int *indexToSkipNextLoop = calloc(scans[i+1].length * sizeof(int));

        for (j=0; j< scans[i].length; j++)
        {

          struct goodMasses currentMasses;// = malloc(sizeof(struct goodMasses));           
          m = scans[i].mass[j];
          minm = m - m*ppm/1e6;
          maxm = m + m*ppm/1e6;
          currentMasses.mz = m;
          currentMasses.mzmin = minm;
          currentMasses.mzmax = maxm;
          //outMasses[count_final] = currentMasses;
          count_final++;
          //outMasses = realloc(outMasses, count_final * sizeof(struct goodMasses));
          printf("count:%d\n", count_final);
//          
//          int idx=i+1, count = 0;
//          
//          while (idx < scanLength)
//          {   
//            int size = 0;
//            int* indexes = bisection(scans[idx].mass, scans[idx].length, m, minm, maxm, &size);//first initialization
//            if (size==0)
//                break;
//
//            double* tmp = calloc(size, sizeof(double)); //if (tmp==NULL) exit(0);
//            for (k=0; k < size; k++)
//                tmp[k] = scans[idx].mass[indexes[k]];
//            double closestMass = getClosest(tmp, size, m);
//            //memory cleaning            
//            free(tmp);
//            free(indexes);
//
//            if (closestMass > currentMasses.mzmax)
//                currentMasses.mzmax = closestMass;
//            
//            if (closestMass < currentMasses.mzmin)
//                currentMasses.mzmin = closestMass;
//            currentMasses.mz = (currentMasses.mz + closestMass)/2;
//            count++;
//            idx ++;
//          }
//          //printf("finished while loop\n");
//          //printf("span:%d\n", count);
//          if (count > minTimeSpan && is_included(outMasses, count_final, currentMasses)==FALSE)
//          {
//            //if (count_final > expectedSize)
//            outMasses[count_final] = currentMasses;
//            count_final++;
//            if (count_final >= expectedSize)
//                outMasses = realloc(outMasses, count_final * sizeof(struct goodMasses));
//          }
        }
    printf("finished One spectra...nb loop:%d\n", i);

    }
    //if (count_final < expectedSize)
    //    outMasses = realloc(outMasses, count_final * sizeof(struct goodMasses));
    //printf("length outMasses:%d\n", count_final);
    return outMasses;
}


struct scan
getEic(struct scan* scans, int length, double mz, double minmz, double maxmz)
{
    int i, j, nbPoints=0;
    struct scan* res = malloc(length * sizeof(struct scan));
    struct scan results, final;
    
    for (i=0; i < length; i++) 
    {
        int size= 0;
        int* indexes = bisection(scans[i].mass, scans[i].length, mz, minmz, maxmz, &size);
        results.mass = calloc(size, sizeof(double));
        results.intensity = calloc(size, sizeof(int));
        results.length = size; results.rt =0.;
        nbPoints+=size;
        for (j=0; j<size; j++)
        {
            results.mass[j] = scans[i].rt;
            results.intensity[j] = scans[i].intensity[indexes[j]];        
        }
        res[i] = results;
        free(indexes); 
    }
    //calc size of good ones
    final.mass = calloc(nbPoints, sizeof(double));
    final.intensity = calloc(nbPoints, sizeof(int));
    final.length = nbPoints; final.rt =0.;
    int count = 0;
    for (i=0; i<length; i++)
    {
        if (res[i].length != 0)
        {
            for (j=0; j<res[i].length; j++)
            {
                final.mass[count] = res[i].mass[j];
                final.intensity[count] = res[i].intensity[j];
                count++;
            }
        }
    }
    free(res);
    return final;
}



