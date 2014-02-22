#ifndef MSGENERATOR
#define MSGENERATOR

#include <string.h>
#include <stdio.h>
#include <iostream>
#include <sstream>
#include <vector>
#include <math.h>
#include <fstream>
#include <cstring>


using namespace std;

class Element {
        public:
            Element(const char*, double, float, const char*, int, int, int, int);
            ~Element();
            const char* sym;	
            double mass;	
            float val;	
            const char* key;	
            int min;
            int max;
            int cnt;
            int save;
};

class MSFormulaGenerator {
    public:
        MSFormulaGenerator(double, double, char*);
        ~MSFormulaGenerator();
        vector<Element> el;
        double electron;
        int nr_el;
        double charge;
        double mz;
        double tol;
        
        vector<string> formulas;
        vector<double> massDifference;
        
        void split(const string&, char, vector<string>&);
        double  calc_mass(void);
        float calc_rdb(void);
        vector<string> do_calculations(void);
        bool calc_element_ratios(bool);
        string toString(int);
        
        vector<string> getFormulas(void);
        vector<double> getMassDifference(void);
};
#endif
