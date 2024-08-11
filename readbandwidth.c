#include <stdlib.h>
#include <stdio.h>
#include <string.h>
#include <pthread.h>
#include <stdint.h>
#include <inttypes.h>
#include <stdbool.h>
#include <pthread.h>
#include <assert.h>
#include <sys/time.h>
#include <unistd.h>
#include <asm/unistd.h>
#include <linux/perf_event.h>
#include <linux/hw_breakpoint.h>
#include <sys/mman.h>
#include <sched.h>
#include <sys/ioctl.h>
#include <numaif.h>
#include <unistd.h>
#include <signal.h>
#include <fcntl.h>
#include <errno.h>

uint64_t total_access = 0;
FILE *fp;

void sigterm_handler(int signum) {
    printf("get SIGTERM, exiting...\n");

    printf("total_access: %lld\n", total_access);

    fclose(fp);

    exit(0); 
}

int main(){

    signal(SIGTERM, sigterm_handler);

    

    fp = fopen("example.txt", "w");
    if (fp == NULL) {
        perror("Error opening file");
        return -1;
    }

    while(1){
        usleep(1000000);
        FILE *file;
        char buffer[256]; 
        int totalCycles = 0, writeCounts = 0, readCounts = 0;

        file = fopen("/sys/kernel/mm/neomem/neomem_states_show", "r");
        if (file == NULL) {
            perror("Error opening file");
            return -1;
        }

        while (fgets(buffer, sizeof(buffer), file)) {
            
            if (sscanf(buffer, "total cycles: %d", &totalCycles) == 1) {
                // printf("Total cycles: %d\n", totalCycles);
            }
            
            else if (sscanf(buffer, "write counts: %d", &writeCounts) == 1) {
                // printf("Write counts: %d\n", writeCounts);
            }
            
            else if (sscanf(buffer, "read counts: %d", &readCounts) == 1) {
                // printf("Read counts: %d\n", readCounts);
            }
        }

        fclose(file);
        total_access += writeCounts + readCounts;

        fprintf(fp, "writeCounts: %d, readCounts: %d\n", writeCounts, readCounts);

    }

    fclose(fp);

    return 0;
}