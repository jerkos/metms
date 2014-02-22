#include "generator.h"


Element::Element(const char* s, double m, float v, const char* k, int mi, int ma, int c, int sa){
    sym=s;
    mass=m;
    val=v;
    key=k;
    min=mi;
    max=ma;
    cnt=c;
    save=sa;
}

Element::~Element(){}


MSFormulaGenerator::MSFormulaGenerator(double mz, double tol, char* cmd){

    Element c("C",  12.000000000,   +2.0, "C", 0, 41, 0,0 );el.push_back(c);
    Element c13("13C", 13.0033548378, +2.0, "1", 0, 0, 0 ,0 );el.push_back(c13);
    Element h("H",   1.0078250321,  -1.0, "H", 0, 72, 0 ,0);el.push_back(h);
    Element d("D",   2.0141017780,  -1.0, "D", 0, 0, 0 ,0);el.push_back(d);
    Element n("N",  14.0030740052,  +1.0, "N", 0, 34, 0,0);el.push_back(n);	
    Element n15("15N", 15.0001088984,   +1.0, "M", 0, 0, 0,0);el.push_back(n15);
    Element o("O",  15.9949146221,   0.0, "O", 0, 30, 0 ,0);el.push_back(o);
    Element f("F",  18.99840320,    -1.0, "F", 0, 0, 0 ,0);el.push_back(f);
    Element na("Na", 22.98976967,    -1.0, "A", 0, 0, 0 ,0);el.push_back(na);
    Element si("Si", 27.9769265327,  +2.0, "I", 0, 0, 0 ,0);el.push_back(si);
    Element p("P",  30.97376151,    +3.0, "P", 0, 0, 0 ,0);el.push_back(p);	
    Element s("S",  31.97207069,    +4.0, "S", 0, 0, 0 ,0);el.push_back(s);	
    Element cl("Cl", 34.96885271,    -1.0, "L", 0, 0, 0 ,0);el.push_back(cl);
    Element br("Br", 78.9183376,     -1.0, "B", 0, 0, 0 ,0);el.push_back(br);
    
    
    electron=0.000549;	
    nr_el = el.size();
    charge =0.;
    //analyse de la ligne de commande
    vector<string> splitted;
    int tmp;
    string cmdline=cmd;
    split(string(cmdline), ' ', splitted);
    if (splitted.size()% 2 != 0) 
        printf("error, missing one argument\n");
    for (unsigned int i=0; i < splitted.size(); i+=2){
        char *atom= (char*)splitted[i].c_str();
        char *numbers= (char*)splitted[i+1].c_str();
        for (int j=0; j<nr_el; j++){
            //printf("%s,%s\n", el[j].key, atom);
            if (strcmp(el[j].key, atom)==0){
                sscanf(numbers, "%d-%d", &el[j].min, &el[j].max);
                if (el[j].min > el[j].max){
                    tmp = el[j].min;
                    el[j].min = el[j].max;
                    el[j].max = tmp;
                }
                break;
            }
        }
    }
    this->mz=mz;
    this->tol=tol;
}

MSFormulaGenerator::~MSFormulaGenerator(){}

void MSFormulaGenerator::split(const string& s, char c, vector<string>& v) {
    string::size_type i = 0;
    string::size_type j = s.find(c);
    while (j != string::npos) {
        v.push_back(s.substr(i, j-i));
        i = ++j;
        j = s.find(c, j);
        if (j == string::npos) v.push_back(s.substr(i, s.length( )));
    }
}


double MSFormulaGenerator::calc_mass(void)
{
int i;
double sum = 0.0;

for (i=0; i < nr_el; i++)
	sum += el[i].mass * el[i].cnt;

return (sum - (charge * electron));
}


float MSFormulaGenerator::calc_rdb(void)
{
int i;
float sum = 2.0;

for (i=0; i < nr_el; i++)
	sum += el[i].val * el[i].cnt;

return (sum/2.0);
}

bool MSFormulaGenerator::calc_element_ratios(bool element_probability)
{
bool CHNOPS_ok;	
float HC_ratio;
float NC_ratio;
float OC_ratio;
float PC_ratio;
float SC_ratio;

float C_count = (float)el[0].cnt;
float H_count = (float)el[2].cnt;
float N_count = (float)el[4].cnt;
float O_count = (float)el[6].cnt;
float P_count = (float)el[10].cnt;
float S_count = (float)el[11].cnt;


		

	// set CHNOPS_ok = true and assume all ratios are ok
	CHNOPS_ok = true;	
	
	
	if (C_count && H_count >0)					
	{	
		HC_ratio = H_count/C_count;
		if (element_probability)
		{
			if ((HC_ratio <  0.2) || (HC_ratio >  3.0)) // this is the H/C probability check ;
			CHNOPS_ok = false;
		}
		else if (HC_ratio >  6.0) // this is the normal H/C ratio check - type cast from int to float is important
			CHNOPS_ok = false;
	}

	if (N_count >0)	// if positive number of nitrogens then thes N/C ratio else just calc normal
	{
		NC_ratio = N_count/C_count;
		if (element_probability)
		{
			if (NC_ratio >  2.0) // this is the N/C probability check 
			CHNOPS_ok = false;
		}
		else if (NC_ratio >  4.0)
			CHNOPS_ok = false;
	}	
	
	if (O_count >0)	// if positive number of O then thes O/C ratio else just calc normal
	{	
		OC_ratio = O_count/C_count;
		if (element_probability)
		{
			if (OC_ratio >  2.1) // this is the O/C  probability check ;
			CHNOPS_ok = false;		
		}
		else if (OC_ratio >  3.0)
				CHNOPS_ok = false;
	}	


	if (P_count >0)	// if positive number of P then thes P/C ratio else just calc normal
	{	
		PC_ratio = 	P_count/C_count;
		if (element_probability)
		{
			if (PC_ratio >  0.34) // this is the P/C  probability check 
			CHNOPS_ok = false;	
		
		}
		else if (PC_ratio >  6.0)
			CHNOPS_ok = false;
	}	

	if (S_count >0)	// if positive number of S then thes S/C ratio else just calc normal
	{	
		SC_ratio = 	S_count/C_count;
		if (element_probability)
		{
			if (SC_ratio >  0.65) // this is the S/C  probability check 
			CHNOPS_ok = false;	
		}
		else if (SC_ratio >  2.0)
			CHNOPS_ok = false;
	}	

		
	// check for multiple element ratios together with probability check 
	//if N<10, O<20, P<4, S<3 then true
	if (element_probability && (N_count > 10) && (O_count > 20) && (P_count > 4) && (S_count > 1))
		CHNOPS_ok = false;	
	
	// NOP check for multiple element ratios together with probability check
	// NOP all > 3 and (N<11, O <22, P<6 then true)
	if (element_probability && (N_count > 3) && (O_count > 3) && (P_count > 3))
		{
		if (element_probability && (N_count > 11) && (O_count > 22) && (P_count > 6))
			CHNOPS_ok = false;	
		}
	
	// OPS check for multiple element ratios together with probability check
	// O<14, P<3, S<3 then true
	if (element_probability && (O_count > 14) && (P_count > 3) && (S_count > 3))
		CHNOPS_ok = false;	

	// PSN check for multiple element ratios together with probability check
	// P<3, S<3, N<4 then true
	if (element_probability && (P_count > 3) && (S_count > 3) && (N_count >4))
		CHNOPS_ok = false;	

	
	// NOS check for multiple element ratios together with probability check
	// NOS all > 6 and (N<19 O<14 S<8 then true)
	if (element_probability && (N_count >6) && (O_count >6) && (S_count >6))
	{
		if (element_probability && (N_count >19) && (O_count >14) && (S_count >8))
			CHNOPS_ok = false;	
	}	


	// function return value; return CHNOPS_ok!
	if (CHNOPS_ok == true)
		return true;
	else 
		return false;
}


vector<string> MSFormulaGenerator::do_calculations(void)
{

double mass=0.0;			
double limit_lo, limit_hi;	
float rdb, lewis;
long i;			
long long hit;
long long counter;
bool elementcheck;
bool set_break; 


printf("\n");	

/* calculate limits */

//limit_lo = measured_mass - (tolerance / 1000.0);
//limit_hi = measured_mass + (tolerance / 1000.0);
limit_lo = mz - ((mz*tol) / 1e6);//change to put it in ppm
limit_hi = mz + ((mz*tol) / 1e6);


/*
printf ("Composition\t");
for (i=0; i < nr_el; i++)
	if (el[i].max > 0)
		printf("%s:%d-%d ", el[i].sym, el[i].min, el[i].max);
printf ("\n");

printf ("Tol (ppm)\t%.1f\n",tol);
printf ("Measured\t%.4lf\n", mz);
printf ("Charge  \t%+.1lf\n", charge);
*/
hit = 0;			
counter = 0;
set_break = false;	


el[13].cnt = el[13].min - 1;  el[13].save = el[13].cnt; 
while (el[13].cnt++ < el[13].max) /* "Br"*/ { 

el[12].cnt = el[12].min - 1;  el[12].save = el[12].cnt; 
while (el[12].cnt++ < el[12].max) /*"Cl"*/ { 
	 
el[11].cnt = el[11].min - 1;  el[11].save = el[11].cnt; 
while (el[11].cnt++ < el[11].max) /*"S"*/ { 
	 
el[10].cnt = el[10].min - 1;  el[10].save = el[10].cnt; 
while (el[10].cnt++ < el[10].max) /*"P"*/ { 
	 
el[9].cnt = el[9].min - 1;  el[9].save = el[9].cnt; 
while (el[9].cnt++ < el[9].max) /*"Si"*/ { 

el[8].cnt = el[8].min - 1;  el[8].save = el[8].cnt; 
while (el[8].cnt++ < el[8].max) /*"Na"*/{ 

el[7].cnt = el[7].min - 1;  el[7].save = el[7].cnt; 
while (el[7].cnt++ < el[7].max) /*"F"*/ { 
 
el[6].cnt = el[6].min - 1;  el[6].save = el[6].cnt; 
while (el[6].cnt++ < el[6].max) /*"O"*/ { 
	 
el[5].cnt = el[5].min - 1;  el[5].save = el[5].cnt; 
while (el[5].cnt++ < el[5].max) /*"15N"*/{ 

el[4].cnt = el[4].min - 1; el[4].save = el[4].cnt; 
while (el[4].cnt++ < el[4].max) /*"N"*/{ 
	 
el[1].cnt = el[1].min - 1; el[1].save = el[1].cnt; 
while (el[1].cnt++ < el[1].max) /*"13C"*/ { 

el[0].cnt = el[0].min - 1; el[0].save = el[0].cnt; 
while (el[0].cnt++ < el[0].max) /* "C"*/ { 

el[3].cnt = el[3].min - 1; 	el[3].save = el[3].cnt; 
while (el[3].cnt++ < el[3].max) /*"D"*/{ 

el[2].cnt = el[2].min - 1; el[2].save = el[2].cnt; 
while (el[2].cnt++ < el[2].max) /*"H"*/{ 

	mass = calc_mass();
	counter++;

	

	// break H loop 
	if (mass > limit_hi)  break;

  
	
	if ((mass >= limit_lo) && (mass <= limit_hi)) 
	
	{	
		
		 elementcheck = calc_element_ratios(true);
		 if (elementcheck)
		{
			rdb = calc_rdb();	
			lewis = (float)(fmod(rdb, 1)); 
			if ((rdb >= 0) && (lewis != 0.5) && (lewis !=-0.5))
			{												
                hit ++;
                string s;
				for (i = 0; i < nr_el; i++)
                {
					if (el[i].cnt > 0)
                    {
					  //printf("%s%d.", el[i].sym, el[i].cnt);	// print formula
                      s+=string(el[i].sym);
                      s+=toString(el[i].cnt);
                      s+=string(".");
                      //formulas.push_back("%s%d.", el[i].sym, el[i].cnt)
                    }
                }
                //printf("\t\t%.1f\t%.4lf\t%+.1lf  \n", rdb, mass, (mz - mass)*1000);
                //printf("\n");
                massDifference.push_back(mz-mass);
                formulas.push_back(s);
			}	
		}	// end of elementcheck loop
	
	}	
	
		} /*"H"*/
		
		} /*"D"*/
		
		if ((mass >= limit_lo) && (el[2].save == el[2].cnt-1)) break;
		} /* "C"*/
		
		} /*"13C"*/

		if ((mass >= limit_lo) && (el[0].save == el[0].cnt-1)) break;
		} /*"N"*/
		
		} /*"15N"*/

        if ((mass >= limit_lo) && (el[4].save == el[4].cnt-1)) break;
		} /*"O"*/
		
	    if ((mass >= limit_lo) && (el[6].save == el[6].cnt-1)) break;
		} /*"F"*/
		
		} /*"Na"*/
		
	    if ((mass >= limit_lo) && (el[7].save == el[7].cnt-1)) break;
		}  /*"Si"*/
		
		if ((mass >= limit_lo) && (el[9].save == el[9].cnt-1)) break;
		} /*"P"*/
		
		if ((mass >= limit_lo) && (el[10].save == el[10].cnt-1)) break;
		} /*"S"*/
		
		if ((mass >= limit_lo) && (el[11].save == el[11].cnt-1)) break;
		} /*"Cl"*/
		
		if ((mass >= limit_lo) && (el[12].save == el[12].cnt-1)) break;
		} /*"Br" ends*/

return formulas;
}

string MSFormulaGenerator::toString(int n){
    ostringstream oss;
    oss << n;
    return oss.str();
}
vector<string> MSFormulaGenerator::getFormulas(void){
    return formulas;
}
vector<double> MSFormulaGenerator::getMassDifference(void){
    return massDifference;
}
