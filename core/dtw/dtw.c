/*  
    This code is written by Davide Albanese <albanese@fbk.it>.
    (C) 2009 Fondazione Bruno Kessler - Via Santa Croce 77, 38100 Trento, ITALY.

    This program is free software: you can redistribute it and/or modify
    it underthe terms of the GNU General Public License as published by
    the Free Software Foundation, either version 3 of the License, or
    (at your option) any later version.

    This program is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU General Public License for more details.

    You should have received a copy of the GNU General Public License
    along with this program.  If not, see <http://www.gnu.org/licenses/>.
*/

#include <Python.h>
#include <numpy/arrayobject.h>
#include <stdlib.h>
#include <stdio.h>
#include <math.h>
#include <float.h>


#define SYMMETRIC0 0
#define ASYMMETRIC0 1
#define QUASISYMMETRIC0 2

#define NOWINDOW 0
#define SAKOECHIBA 1
 

double
min3(double a, double b, double c)
{
  double minvalue;
  
  minvalue = a;
  
  if (b < minvalue)
    minvalue = b;
  
  if (c < minvalue)
    minvalue = c;

  return minvalue;
}


double
min2(double a, double b)
{
  double minvalue;
  
  minvalue = a;
  
  if (b < minvalue)
    minvalue = b;
  
  return minvalue;
}


double
max2(double a, double b)
{
  double maxvalue;
  
  maxvalue = a;
  
  if (b > maxvalue)
    maxvalue = b;
  
  return maxvalue;
}


double
euclidean(double a, double b)
{
  return pow((a - b), 2);
}


int
der(double *x, int n, double *out)
{
  int i, j;
  
  for (i=1, j=0; i<n-1; i++, j++)
      out[i] = ((x[i] - x[j]) + ((x[i+1] - x[j]) / 2.0)) / 2.0;
  
  out[0] = out[1];
  out[n-1] = out[n-2];
  
  return 1;
}


/* No global constraints
 * 
 * constr[0] -> lower constraint (0)
 * constr[1] -> upper constraint (m - 1)
 *
 */

int **
no_window(int n, int m)
{
  int i;
  int **constr;

  constr = (int **) malloc (2 * sizeof(int*));
  constr[0] = (int *) malloc (n * sizeof(int));
  constr[1] = (int *) malloc (n * sizeof(int));
      
  for (i=0; i<n; i++)
    {
      constr[0][i] = 0;
      constr[1][i] = m - 1;
    }
  
  return constr;
}


/* Sakoe-Chiba global constraints
 * 
 * constr[0] -> lower constraint
 * constr[1] -> upper constraint
 *
 */

int **
sakoe_chiba(int n, int m, double r)
{
  int i;
  int **constr;
  double mnf;

  constr = (int **) malloc (2 * sizeof(int*));
  constr[0] = (int *) malloc (n * sizeof(int));
  constr[1] = (int *) malloc (n * sizeof(int));
  
  mnf = (double) m / (double) n;
    
  for (i=0; i<n; i++)
    {
      constr[0][i] = (int) max2( ceil(i * mnf - r), 0.0 );
      constr[1][i] = (int) min2( floor(i * mnf + r), m - 1 );
    }
  
  return constr;
}


double
symmetric0(double *x, double *y, int n, int m, double *dtwm, int **constr)
{
  int i, j;
  double d;
  double dtwm_i, dtwm_j, dtwm_ij;


  for (i=0; i<n; i++)
    for (j=0; j<m; j++)
      dtwm[i * m + j] = DBL_MAX;

  dtwm[0] = 2.0 * euclidean(x[0], y[0]); // DP-algorithm (i - 1), (j - 1) 
   
  for (j=constr[0][0] + 1; j<=constr[1][0]; j++)
    {
      d = euclidean(x[0], y[j]);
      dtwm_j  = dtwm[0 * m + (j - 1)] + d; // DP-algorithm (j - 1)
      dtwm[0 * m + j] = dtwm_j;
    }

  for (i=1; i<n; i++)             
    for (j=constr[0][i]; j<=constr[1][i]; j++)
      {
	d = euclidean(x[i], y[j]); 
	
	if (j == 0)
	  {
	    dtwm_i = dtwm[(i - 1) * m + j] + d; // DP-algorithm (i - 1)
	    dtwm[i * m + j] = dtwm_i;
	  }
	else
	  {
	    dtwm_i = dtwm[(i - 1) * m + j];
	    dtwm_ij = dtwm[(i - 1) * m + (j - 1)];
	    dtwm_j  = dtwm[i * m + (j - 1)];
	    
	    if (dtwm_i != DBL_MAX)
	      dtwm_i = dtwm_i + d; // DP-algorithm (i - 1)
	    
	    if (dtwm_ij != DBL_MAX)
	      dtwm_ij = dtwm_ij + (2 * d); // DP-algorithm (i - 1), (j - 1) 

	    if (dtwm_j != DBL_MAX)
	      dtwm_j = dtwm_j + d; // DP-algorithm (j - 1)
	       
	    dtwm[i * m + j] = min3(dtwm_i, dtwm_j, dtwm_ij);
	  }
      }
  
  return dtwm[(m * n) - 1] / (double) (n + m);
}


double
quasisymmetric0(double *x, double *y, int n, int m, double *dtwm, int **constr)
{
  int i, j;
  double d;
  double dtwm_i, dtwm_j, dtwm_ij;


  for (i=0; i<n; i++)
    for (j=0; j<m; j++)
      dtwm[i * m + j] = DBL_MAX;

  dtwm[0] = euclidean(x[0], y[0]); // DP-algorithm (i - 1), (j - 1) 
   
  for (j=constr[0][0] + 1; j<=constr[1][0]; j++)
    {
      d = euclidean(x[0], y[j]);
      dtwm_j  = dtwm[0 * m + (j - 1)] + d; // DP-algorithm (j - 1)
      dtwm[0 * m + j] = dtwm_j;
    }

  for (i=1; i<n; i++)             
    for (j=constr[0][i]; j<=constr[1][i]; j++)
      {
	d = euclidean(x[i], y[j]); 
	
	if (j == 0)
	  {
	    dtwm_i = dtwm[(i - 1) * m + j] + d; // DP-algorithm (i - 1)
	    dtwm[i * m + j] = dtwm_i;
	  }
	else
	  {
	    dtwm_i = dtwm[(i - 1) * m + j];
	    dtwm_ij = dtwm[(i - 1) * m + (j - 1)];
	    dtwm_j  = dtwm[i * m + (j - 1)];
	    
	    if (dtwm_i != DBL_MAX)
	      dtwm_i = dtwm_i + d; // DP-algorithm (i - 1)
	    
	    if (dtwm_ij != DBL_MAX)
	      dtwm_ij = dtwm_ij + d; // DP-algorithm (i - 1), (j - 1) 

	    if (dtwm_j != DBL_MAX)
	      dtwm_j = dtwm_j + d; // DP-algorithm (j - 1)
	       
	    dtwm[i * m + j] = min3(dtwm_i, dtwm_j, dtwm_ij);
	  }
      }
  
  return dtwm[(m * n) - 1] / (double) (n + m);
}


double
asymmetric0(double *x, double *y, int n, int m, double *dtwm, int **constr)
{
  int i, j;
  double d;
  double dtwm_i, dtwm_j, dtwm_ij;


  for (i=0; i<n; i++)
    for (j=0; j<m; j++)
      dtwm[i * m + j] = DBL_MAX;

  dtwm[0] = euclidean(x[0], y[0]); // DP-algorithm (i - 1), (j - 1) 
   
  for (j=constr[0][0] + 1; j<=constr[1][0]; j++)
    {
      d = euclidean(x[0], y[j]);
      dtwm_j  = dtwm[0 * m + (j - 1)]; // DP-algorithm (j - 1)
      dtwm[0 * m + j] = dtwm_j;
    }

  for (i=1; i<n; i++)             
    for (j=constr[0][i]; j<=constr[1][i]; j++)
      {
	d = euclidean(x[i], y[j]); 
	
	if (j == 0)
	  {
	    dtwm_i = dtwm[(i - 1) * m + j] + d; // DP-algorithm (i - 1)
	    dtwm[i * m + j] = dtwm_i;
	  }
	else
	  {
	    dtwm_i = dtwm[(i - 1) * m + j];
	    dtwm_ij = dtwm[(i - 1) * m + (j - 1)];
	    dtwm_j  = dtwm[i * m + (j - 1)];
	    
	    if (dtwm_i != DBL_MAX)
	      dtwm_i = dtwm_i + d; // DP-algorithm (i - 1)
	    
	    if (dtwm_ij != DBL_MAX)
	      dtwm_ij = dtwm_ij + d; // DP-algorithm (i - 1), (j - 1) 

	    // DP-algorithm (j - 1) (no sum)
	       
	    dtwm[i * m + j] = min3(dtwm_i, dtwm_j, dtwm_ij);
	  }
      }
  
  return dtwm[(m * n) - 1] / (double) n;
}


double
symmetric0_od(double *x, double *y, int n, int m, int **constr)
{
  int i, j;
  double d, dist = 0.0;
  double dtwm_i, dtwm_j, dtwm_ij;
  
  double *prev_col = (double *) malloc (m * sizeof(double));
  double *next_col = (double *) malloc (m * sizeof(double));
  double *tmp;


  for (j=0; j<m; j++)
    {
      prev_col[j] = DBL_MAX;
      next_col[j] = DBL_MAX;      
    }

  prev_col[0] = 2.0 * euclidean(x[0], y[0]); // DP-algorithm (i - 1), (j - 1) 
   
  for (j=constr[0][0] + 1; j<=constr[1][0]; j++)
    {
      d = euclidean(x[0], y[j]);
      dtwm_j  = prev_col[j - 1] + d; // DP-algorithm (j - 1)
      prev_col[j] = dtwm_j;
    }

  for (i=1; i<n; i++)
    {
      for (j=constr[0][i]; j<=constr[1][i]; j++)
	{
	  d = euclidean(x[i], y[j]); 
	  
	  if (j == 0)
	    {
	      dtwm_i = prev_col[j] + d; // DP-algorithm (i - 1)
	      next_col[j] = dtwm_i;
	    }
	  else
	    {
	      dtwm_i  = prev_col[j];
	      dtwm_ij = prev_col[j - 1];
	      dtwm_j  = next_col[j - 1];
	      
	      if (dtwm_i != DBL_MAX)
		dtwm_i = dtwm_i + d; // DP-algorithm (i - 1)
	      
	      if (dtwm_ij != DBL_MAX)
		dtwm_ij = dtwm_ij + (2 * d); // DP-algorithm (i - 1), (j - 1) 
	      
	      if (dtwm_j != DBL_MAX)
		dtwm_j = dtwm_j + d; // DP-algorithm (j - 1)
	      
	      next_col[j] = min3(dtwm_i, dtwm_j, dtwm_ij);
	    }
	}
      
      dist = next_col[m - 1];
      
      tmp = prev_col;
      prev_col = next_col;
      next_col = tmp;
      
      for (j=0; j<m; j++)
	next_col[j] = DBL_MAX;      
            
    }
  
  free(prev_col);
  free(next_col);

  return dist / (double) (n + m);
}


double
quasisymmetric0_od(double *x, double *y, int n, int m, int **constr)
{
  int i, j;
  double d, dist = 0.0;
  double dtwm_i, dtwm_j, dtwm_ij;
  
  double *prev_col = (double *) malloc (m * sizeof(double));
  double *next_col = (double *) malloc (m * sizeof(double));
  double *tmp;


  for (j=0; j<m; j++)
    {
      prev_col[j] = DBL_MAX;
      next_col[j] = DBL_MAX;      
    }

  prev_col[0] = euclidean(x[0], y[0]); // DP-algorithm (i - 1), (j - 1) 
   
  for (j=constr[0][0] + 1; j<=constr[1][0]; j++)
    {
      d = euclidean(x[0], y[j]);
      dtwm_j  = prev_col[j - 1] + d; // DP-algorithm (j - 1)
      prev_col[j] = dtwm_j;
    }
  
  for (i=1; i<n; i++)
    {
      for (j=constr[0][i]; j<=constr[1][i]; j++)
	{
	  d = euclidean(x[i], y[j]); 
	  
	  if (j == 0)
	    {
	      dtwm_i = prev_col[j] + d; // DP-algorithm (i - 1)
	      next_col[j] = dtwm_i;
	    }
	  else
	    {
	      dtwm_i  = prev_col[j];
	      dtwm_ij = prev_col[j - 1];
	      dtwm_j  = next_col[j - 1];
	      
	      if (dtwm_i != DBL_MAX)
		dtwm_i = dtwm_i + d; // DP-algorithm (i - 1)
	      
	      if (dtwm_ij != DBL_MAX)
		dtwm_ij = dtwm_ij + d; // DP-algorithm (i - 1), (j - 1) 
	      
	      if (dtwm_j != DBL_MAX)
		dtwm_j = dtwm_j + d; // DP-algorithm (j - 1)
	      
	      next_col[j] = min3(dtwm_i, dtwm_j, dtwm_ij);
	    }
	}
      
      dist = next_col[m - 1];
      
      tmp = prev_col;
      prev_col = next_col;
      next_col = tmp;
      
      for (j=0; j<m; j++)
	next_col[j] = DBL_MAX;      
            
    }
  
  free(prev_col);
  free(next_col);

  return dist / (double) (n + m);
}


double
asymmetric0_od(double *x, double *y, int n, int m, int **constr)
{
  int i, j;
  double d, dist = 0.0;
  double dtwm_i, dtwm_j, dtwm_ij;
  
  double *prev_col = (double *) malloc (m * sizeof(double));
  double *next_col = (double *) malloc (m * sizeof(double));
  double *tmp;


  for (j=0; j<m; j++)
    {
      prev_col[j] = DBL_MAX;
      next_col[j] = DBL_MAX;      
    }

  prev_col[0] = euclidean(x[0], y[0]); // DP-algorithm (i - 1), (j - 1) 
   
  for (j=constr[0][0] + 1; j<=constr[1][0]; j++)
    {
      d = euclidean(x[0], y[j]);
      dtwm_j  = prev_col[j - 1]; // DP-algorithm (j - 1)
      prev_col[j] = dtwm_j;
    }

  for (i=1; i<n; i++)
    {
      for (j=constr[0][i]; j<=constr[1][i]; j++)
	{
	  d = euclidean(x[i], y[j]); 
	  
	  if (j == 0)
	    {
	      dtwm_i = prev_col[j] + d; // DP-algorithm (i - 1)
	      next_col[j] = dtwm_i;
	    }
	  else
	    {
	      dtwm_i  = prev_col[j];
	      dtwm_ij = prev_col[j - 1];
	      dtwm_j  = next_col[j - 1];
	      
	      if (dtwm_i != DBL_MAX)
		dtwm_i = dtwm_i + d; // DP-algorithm (i - 1)
	      
	      if (dtwm_ij != DBL_MAX)
		dtwm_ij = dtwm_ij + d; // DP-algorithm (i - 1), (j - 1) 
	      
	      // DP-algorithm (j - 1) (no sum)
	      
	      next_col[j] = min3(dtwm_i, dtwm_j, dtwm_ij);
	    }
	}
      
      dist = next_col[m - 1];
      
      tmp = prev_col;
      prev_col = next_col;
      next_col = tmp;
      
      for (j=0; j<m; j++)
	next_col[j] = DBL_MAX;      
            
    }
  
  free(prev_col);
  free(next_col);

  return dist / (double) n;
}


/* double */
/* symmetric0(double *x, double *y, int n, int m, double *dtwm) */
/* { */
/*   int i, j; */
/*   double d; */

/*   dtwm[0] = 2.0 * euclidean(x[0], y[0]); */
  
/*   for (i=1; i<n; i++) */
/*     dtwm[i * m + 0] = dtwm[(i - 1) * m + 0] + euclidean(x[i], y[0]); */
  
/*   for (j=1; j<m; j++) */
/*     dtwm[0 * m + j] = dtwm[0 * m + (j - 1)] + euclidean(x[0], y[j]); */
  
/*   for (i=1; i<n; i++) */
/*     for (j=1; j<m; j++) */
/*       { */
/* 	d = euclidean(x[i], y[j]); */
/* 	dtwm[i * m + j] = min3(dtwm[(i - 1) * m + j] + d, */
/* 			       dtwm[i * m + (j - 1)] + d, */
/* 			       dtwm[(i - 1) * m + (j - 1)] + (2 * d)); */
/*       } */

/*   return dtwm[(m * n) - 1] / (float) (n + m); */
/* } */


/* double */
/* asymmetric0(double *x, double *y, int n, int m, double *dtwm) */
/* { */
/*   int i, j; */
/*   double d; */
  
/*   dtwm[0] = euclidean(x[0], y[0]); */
  
/*   for (i=1; i<n; i++) */
/*     dtwm[i * m + 0] = dtwm[(i - 1) * m + 0] + euclidean(x[i], y[0]); */
  
/*   for (j=1; j<m; j++) */
/*     dtwm[0 * m + j] = dtwm[0 * m + (j - 1)]; */
  
/*   for (i=1; i<n; i++) */
/*     for (j=1; j<m; j++) */
/*       { */
/* 	d = euclidean(x[i], y[j]); */
/* 	dtwm[i * m + j] = min3(dtwm[(i - 1) * m + j] + d, */
/* 			       dtwm[i * m + (j - 1)], */
/* 			       dtwm[(i - 1) * m + (j - 1)] + d); */
/*       } */

/*   return dtwm[(m * n) - 1] / (float) n; */
/* } */


/* double */
/* quasisymmetric0(double *x, double *y, int n, int m, double *dtwm) */
/* { */
/*   int i, j; */
/*   double d; */
  
/*   dtwm[0] = euclidean(x[0], y[0]); */
  
/*   for (i=1; i<n; i++) */
/*     dtwm[i * m + 0] = dtwm[(i - 1) * m + 0] + euclidean(x[i], y[0]); */
  
/*   for (j=1; j<m; j++) */
/*     dtwm[0 * m + j] = dtwm[0 * m + (j - 1)] + euclidean(x[0], y[j]); */
  
/*   for (i=1; i<n; i++) */
/*     for (j=1; j<m; j++) */
/*       { */
/* 	d = euclidean(x[i], y[j]); */
/* 	dtwm[i * m + j] = min3(dtwm[(i - 1) * m + j] + d, */
/* 			       dtwm[i * m + (j - 1)] + d, */
/* 			       dtwm[(i - 1) * m + (j - 1)] + d); */
/*       } */

/*   return dtwm[(m * n) - 1] / (float) (n + m); */
/* } */


int
optimal_warping_path(double *dtwm, int n, int m, int *pathx, int *pathy, int startbc)
{
  int i = n - 1;
  int j = m - 1;
  int k = 0;
  double min_ij, dtwm_i, dtwm_j, dtwm_ij;

  pathx[k] = i;
  pathy[k] = j;
  k++;

  while ((i > 0) || (j > 0))
    {
      if ((i == 0) && (j > 0))
	{
	  if (startbc == 1)
	    j -= 1;
	  else
	    break;
	}
      
      if ((j == 0) && (i > 0))
	{
	  if (startbc == 1)
	    i -= 1;
	  else
	    break;
	}
      
      if ((i > 0) && (j > 0))
	{
	  dtwm_i  = dtwm[(i - 1) * m + j];
	  dtwm_j  = dtwm[i * m + (j - 1)];
	  dtwm_ij = dtwm[(i - 1) * m + (j - 1)];
	  min_ij  = min3(dtwm_i, dtwm_j, dtwm_ij);
	  
	  if (dtwm_ij == min_ij)
	    {
	      i -= 1;
	      j -= 1;
	    }
	  else if (dtwm_i == min_ij)
	    i -= 1;
	  else if (dtwm_j == min_ij)
	    j -= 1;
	}
      
      pathx[k] = i;
      pathy[k] = j;
      k++;
    }
  
  return k;
}


/********************/
/***** not used *****/
/********************/

int
sakoe_warping_path(double *dtwm, int n, int m,
		   int *pathx, int *pathy, int startbc, double wl)
{
  int i = n - 1;
  int j = m - 1;
  int k = 0;
  
  double min_ij, dtwm_i, dtwm_j, dtwm_ij;
  double mnf = (double) m / (double) n;

  pathx[k] = i;
  pathy[k] = j;
  k++;

  while ((i > 0) || (j > 0))
    {
      if ((i == 0) && (j > 0))
	{
	  if (startbc == 1)
	    j -= 1;
	  else
	    break;
	}
      
      else if ((j == 0) && (i > 0))
	{
	  if (startbc == 1)
	    i -= 1;
	  else
	    break;
	}
      
      else
	{
	  dtwm_i  = dtwm[(i - 1) * m + j];
	  dtwm_ij = dtwm[(i - 1) * m + (j - 1)];
	  dtwm_j  = dtwm[i * m + (j - 1)];
	  
	  if ( j <= ((i - 1) * mnf + wl) )
	    {
	      if ( (j - 1) >= (i * mnf - wl) )
		{
		  min_ij  = min3(dtwm_i, dtwm_j, dtwm_ij);
		  
		  if (dtwm_ij == min_ij)
		    {
		      i -= 1;
		      j -= 1;
		    }
		  else if (dtwm_i == min_ij)
		    i -= 1;
		  else if (dtwm_j == min_ij)
		    j -= 1;
		}
	      
	      else if ( (j - 1) >= ((i - 1) * mnf - wl) )
		{
		  min_ij  = min2(dtwm_i, dtwm_ij);
		  
		  if (dtwm_ij == min_ij)
		    {
		      i -= 1;
		      j -= 1;
		    }
		  else if (dtwm_i == min_ij)
		    i -= 1;
		}
	      
	      else
		i -= 1;
	    }
	  
	  else if ( (j - 1) >= (i * mnf - wl) )
	    {
	      if ( (j - 1) <= ((i - 1) * mnf +wl) )
		{
		  min_ij  = min2(dtwm_j, dtwm_ij);
		  
		  if (dtwm_ij == min_ij)
		    {
		      i -= 1;
		      j -= 1;
		    }
		  else if (dtwm_j == min_ij)
		    j -= 1;
		}
	      
	      else
		j -= 1;
	    }
	}
      
      pathx[k] = i;
      pathy[k] = j;
      k++;
    }
  
  return k;
}


static PyObject *dtw_dtw(PyObject *self, PyObject *args, PyObject *keywds)
{
  PyObject *x  = NULL; PyObject *x_a  = NULL;
  PyObject *y  = NULL; PyObject *y_a  = NULL; 
  PyObject *startbc = Py_True;
  PyObject *onlydist = Py_False;
  int steppattern = 0;
  double r = 0.0;
  int wincond = 0;
 
  int *pathx, *pathy;
  int k;
  int sbc;
  double distance;
  int ** constr;

  npy_intp n, m;
  double *x_v, *y_v;
  
  PyObject *px_a    = NULL;
  PyObject *py_a    = NULL; 
  PyObject *dtwm_a  = NULL; 
  
  npy_intp p_dims[1];
  npy_intp dtwm_dims[2];

  int *px_v, *py_v;
  double *dtwm_v;

  int i;
 

  /* Parse Tuple*/
  static char *kwlist[] = {"x", "y", "startbc", "steppattern", "onlydist", "wincond", "r", NULL};
  if (!PyArg_ParseTupleAndKeywords(args, keywds, "OO|OiOid", kwlist,
				   &x, &y, &startbc, &steppattern, &onlydist, &wincond, &r))
    return NULL;

  x_a = PyArray_FROM_OTF(x, NPY_DOUBLE, NPY_IN_ARRAY);
  if (x_a == NULL) return NULL;
 
  y_a = PyArray_FROM_OTF(y, NPY_DOUBLE, NPY_IN_ARRAY);
  if (y_a == NULL) return NULL;

  if (PyArray_NDIM(x_a) != 1){
    PyErr_SetString(PyExc_ValueError, "x should be 1D numpy array or list");
    return NULL;
  }
  
  if (PyArray_NDIM(y_a) != 1){
    PyErr_SetString(PyExc_ValueError, "y should be 1D numpy array or list");
    return NULL;
  }

  x_v = (double *) PyArray_DATA(x_a);
  y_v = (double *) PyArray_DATA(y_a);
  n = (int) PyArray_DIM(x_a, 0);
  m = (int) PyArray_DIM(y_a, 0);

  
  switch (wincond)
    {
    case NOWINDOW:
      constr = no_window(n, m);
      break;
      
    case SAKOECHIBA:
      constr = sakoe_chiba(n, m, r);
      break;
      
    default:
      PyErr_SetString(PyExc_ValueError, "wincond is not valid");
      return NULL;
    }
  

  if (onlydist == Py_True)
    {
      switch (steppattern)
	{
	case SYMMETRIC0:
	  distance = symmetric0_od(x_v, y_v, n, m, constr);
	  break;
	  
	case QUASISYMMETRIC0:
	  distance = quasisymmetric0_od(x_v, y_v, n, m, constr);
	  break;
	  
	case ASYMMETRIC0:
	  distance = asymmetric0_od(x_v, y_v, n, m, constr);
	  break;
	  
	default:
	  PyErr_SetString(PyExc_ValueError, "steppattern is not valid");
	  return NULL;
	}

      free(constr[0]);
      free(constr[1]);
      free(constr);          
    
      Py_DECREF(x_a);
      Py_DECREF(y_a);
     
      return Py_BuildValue("d", distance);
    }
  else
    {
      dtwm_dims[0] = (npy_intp) n;
      dtwm_dims[1] = (npy_intp) m;
      dtwm_a = PyArray_SimpleNew(2, dtwm_dims, NPY_DOUBLE);
      dtwm_v = (double *) PyArray_DATA(dtwm_a);

      switch (steppattern)
	{
	case SYMMETRIC0:
	  distance = symmetric0(x_v, y_v, n, m, dtwm_v, constr);
	  break;
	  
	case QUASISYMMETRIC0:
	  distance = quasisymmetric0(x_v, y_v, n, m, dtwm_v, constr);
	  break;
	  
	case ASYMMETRIC0:
	  distance = asymmetric0(x_v, y_v, n, m, dtwm_v, constr);
	  break;
	  
	default:
	  PyErr_SetString(PyExc_ValueError, "steppattern is not valid");
	  return NULL;
	}

      free(constr[0]);
      free(constr[1]);
      free(constr);          

      pathx = (int *) malloc((n + m - 1) * sizeof(int));
      pathy = (int *) malloc((n + m - 1) * sizeof(int));
      
      if (startbc == Py_True)
	sbc = 1;
      else
	sbc = 0;  
      
      k = optimal_warping_path(dtwm_v, n, m, pathx, pathy, sbc);
      
      p_dims[0] = (npy_intp) k;
      px_a = PyArray_SimpleNew(1, p_dims, NPY_INT);
      py_a = PyArray_SimpleNew(1, p_dims, NPY_INT);
      px_v = (int *) PyArray_DATA(px_a);
      py_v = (int *) PyArray_DATA(py_a);
      
      for (i=0; i<k; i++)
	{
	  px_v[i] = pathx[k-1-i];
	  py_v[i] = pathy[k-1-i];
	}
      
      free(pathx);
      free(pathy);
      
      Py_DECREF(x_a);
      Py_DECREF(y_a);
      
      return Py_BuildValue("d, N, N, N", distance, px_a, py_a, dtwm_a);
    }
}


static PyObject *dtw_der(PyObject *self, PyObject *args, PyObject *keywds)
{
  PyObject *x  = NULL; PyObject *x_a  = NULL;
  PyObject *out_a = NULL;
  
  npy_intp out_dims[1];
  npy_intp n;
  
  double *out_v, *x_v;
  

  /* Parse Tuple*/
  static char *kwlist[] = {"x", NULL};
  if (!PyArg_ParseTupleAndKeywords(args, keywds, "O", kwlist, &x))
    return NULL;

  x_a = PyArray_FROM_OTF(x, NPY_DOUBLE, NPY_IN_ARRAY);
  if (x_a == NULL) return NULL;
 
  if (PyArray_NDIM(x_a) != 1){
    PyErr_SetString(PyExc_ValueError, "x should be 1D numpy array or list");
    return NULL;
  }

  x_v = (double *) PyArray_DATA(x_a);
  n = (int) PyArray_DIM(x_a, 0);

  out_dims[0] = (npy_intp) n;
  out_a = PyArray_SimpleNew(1, out_dims, NPY_DOUBLE);
  out_v = (double *) PyArray_DATA(out_a);

  der(x_v, n, out_v);

  Py_DECREF(x_a);
  
  return Py_BuildValue("N", out_a);
}




/* Doc strings: */
static char module_doc[] = "";

static char dtw_der_doc[] = "" ;
static char dtw_dtw_doc[] = "" ;


/* Method table */
static PyMethodDef dtw_methods[] = {
  {"dtw",
   (PyCFunction)dtw_dtw,
   METH_VARARGS | METH_KEYWORDS,
   dtw_dtw_doc},
  {"der",
   (PyCFunction)dtw_der,
   METH_VARARGS | METH_KEYWORDS,
   dtw_der_doc},
  {NULL, NULL, 0, NULL}
};


/* Init */
void initdtw()
{
  Py_InitModule3("dtw", dtw_methods, module_doc);
  import_array();
}
