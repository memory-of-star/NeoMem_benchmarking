#include <stdio.h>

#define DEBUG_COUNTER(name, times) \
	name += 1; \
	if (name % times == 0){ \
		printf(#name ": %lld\n", name); \
	}

int a = 1;

int main(){
    DEBUG_COUNTER(a, 2)
    return 0;
}