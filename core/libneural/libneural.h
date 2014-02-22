#ifndef _NNWORK_H
#define _NNWORK_H

#include <stdio.h>
#include <math.h>
#include <time.h>
#include <stdlib.h>
#include <limits.h>
#include <sstream>
#include <iostream>
#include <fstream>
#include <assert.h>
#include <string.h>


#define ALL 0
#define INPUT 1
#define HIDDEN 2
#define OUTPUT 3
#define NONINPUT 0

using namespace std;

struct neuron {
	float *weights;
	float output;
};

class nnlayer {
public:
	neuron *nodes;
	nnlayer (int, int);		// Number of nodes in the layer.
	~nnlayer ();
private:
	int size;
	int weights;
};


// Sigmoid function. Basically a differentiable threshold function.
float sigmoid (float);


// This class implements a simple three-layer backpropagation network.
class nnwork {
// Initialise with the dimensions of the network (input, hidden, output)
public:
	nnwork (int, int, int);
	nnwork ();
	nnwork (char*);
	~nnwork ();
	
	
// returns dims of network - argument is either ALL, INPUT, HIDDEN or OUTPUT
// (see above). ALL gives total nodes (useful to see if network is empty).

	int get_layersize (int);

// Training args are input, desired output, minimum error, learning rate

	void train (float [], float [], float, float);

// Run args are input data, output

	void run (float [], float []);
	
// Arg for load and save is just the filename.

	int load (char*);
	int save (char*);

private:
	nnlayer *output_nodes;
	nnlayer *hidden_nodes;
	int input_size;
	int output_size;
	int hidden_size;
};

#endif
