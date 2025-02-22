
#define _GNU_SOURCE

#include <stdlib.h>
#include <stdio.h>
#include <assert.h>
#include <unistd.h>
#include <sys/time.h>
#include <fcntl.h>
#include <sys/types.h>
#include <sys/stat.h>
#include <math.h>
#include <string.h>
#include <pthread.h>
#include <sys/mman.h>
#include <errno.h>
#include <stdint.h>
#include <stdbool.h>
#include <numaif.h>

#include "gups.h"

#define MAX_THREADS     64

#define GUPS_PAGE_SIZE      (4 * 1024)
#define PAGE_NUM            3
#define PAGES               2048
#define MPOL_F_NUMA_BALANCING 1 << 13

#ifdef HOTSPOT
extern uint64_t hotset_start;
extern double hotset_fraction;
#endif

int threads;

bool move_hotset[MAX_THREADS] = {0};

uint64_t hot_start = 0;
uint64_t hotsize = 0;

char *path;

struct gups_args {
  int tid;                      // thread id
  uint64_t *indices;       // array of indices to access
  void* field;                  // pointer to start of thread's region
  uint64_t iters;          // iterations to perform
  uint64_t size;           // size of region
  uint64_t elt_size;       // size of elements
  uint64_t hot_start;            // start of hot set
  uint64_t hotsize;        // size of hot set
};


static inline uint64_t rdtscp(void)
{
    uint32_t eax, edx;
    // why is "ecx" in clobber list here, anyway? -SG&MH,2017-10-05
    __asm volatile ("rdtscp" : "=a" (eax), "=d" (edx) :: "ecx", "memory");
    return ((uint64_t)edx << 32) | eax;
}

uint64_t thread_gups[MAX_THREADS];

static unsigned long updates, nelems;
static unsigned long phase_change_period = 100;
static unsigned long hot_prob = 100;
static unsigned long tot_time = 200;

bool stop = false;
uint64_t hot_region_random;
uint64_t lfsr;

static uint64_t lfsr_fast(uint64_t _lfsr)
{
  _lfsr ^= _lfsr >> 7;
  _lfsr ^= _lfsr << 9;
  _lfsr ^= _lfsr >> 13;
  return _lfsr;
}


static void *timing_thread()
{
  uint64_t tic = -1;
  for (;;) {
    tic++;
    if (tic % phase_change_period == 0) {
      hot_region_random = lfsr_fast(hot_region_random);
      for (int i = 0; i < MAX_THREADS; i++){
        move_hotset[i] = true;
      }
    }
    if (tic >= tot_time) {
      stop = true;
    }
    sleep(1);
  }
  return 0;
}

uint64_t tot_updates = 0;

static void *print_instantaneous_gups()
{
  FILE *tot;
  uint64_t tot_gups, tot_last_second_gups = 0;


  tot = fopen(path, "w");
  if (tot == NULL) {
    perror("fopen");
  }

  for (;;) {
    tot_gups = 0;
    for (int i = 0; i < threads; i++) {
      tot_gups += thread_gups[i];
    }
    fprintf(tot, "%.10f\n", (1.0 * (abs(tot_gups - tot_last_second_gups))) / (1.0e9));
    tot_updates += abs(tot_gups - tot_last_second_gups);
    tot_last_second_gups = tot_gups;
    sleep(1);
  }

  return NULL;
}


FILE *hotsetfile = NULL;

static void *do_gups(void *arguments)
{
  printf("do_gups entered\n");
  struct gups_args *args = (struct gups_args*)arguments;
  uint64_t *field = (uint64_t*)(args->field);
  uint64_t i;
  uint64_t index1, index2;
  uint64_t elt_size = args->elt_size;
  char data[elt_size];
  uint64_t hot_num;

  uint64_t lfsr_local;
  uint64_t hot_prob_local = hot_prob;


  srand(args->tid);
  lfsr_local = rand();
  
  // uint64_t hot_region_random;

  

  // hot_region_random = lfsr;
  // hot_region_random = lfsr_fast(hot_region_random);

  // for (int i = 0; i < 7; i++){
  //   hot_region_random = lfsr_fast(hot_region_random);
  // }

  index1 = 0;
  index2 = 0;

  fprintf(hotsetfile, "Thread %d region: %p - %p\thot set: %p - %p\n", args->tid, field, field + args->size, field + args->hot_start, field + args->hot_start + args->hotsize);   

  for (i = 0; i < args->iters; i++) {
    hot_num = lfsr_fast(lfsr_local) % 100;
    if (hot_num < hot_prob_local) {
      lfsr_local = lfsr_fast(lfsr_local);
      index1 = (args->hot_start + (lfsr_local % args->hotsize)) % (args->size);

      if (move_hotset[args->tid]) {
        args->hot_start = ((hot_region_random + args->tid * args->hotsize) % (args->size));
        move_hotset[args->tid] = false;
        if (args->hot_start + args->hotsize < args->size)
          printf("Thread %d region: %p - %p\thot set moved: %p - %p\n", args->tid, field, field + args->size, field + args->hot_start, field + args->hot_start + args->hotsize);  
        else
          printf("Thread %d region: %p - %p\thot set moved: %p - %p, %p - %p\n", args->tid, field, field + args->size, field + args->hot_start, field + args->size, field, field + args->hot_start + args->hotsize - args->size);
      }

      if (elt_size == 8) {
        volatile uint64_t tmp = *(volatile uint64_t*)(field + index1);
        tmp = tmp + i;
        field[index1] = tmp;
      }
      else {
        memcpy(data, &field[index1 * elt_size], elt_size);
        memset(data, data[0] + i, elt_size);
        memcpy(&field[index1 * elt_size], data, elt_size);
      }

    }
    else {
      lfsr_local = lfsr_fast(lfsr_local);
      index2 = lfsr_local % (args->size);

      if (elt_size == 8) {
        volatile uint64_t tmp = *(volatile uint64_t*)(field + index2);
        tmp = tmp + i;
        field[index2] = tmp;
      }
      else {
        memcpy(data, &field[index2 * elt_size], elt_size);
        memset(data, data[0] + i, elt_size);
        memcpy(&field[index2 * elt_size], data, elt_size);
      }
    }

    if (i % 10000 == 0) {
      thread_gups[args->tid] += 10000;
    }

    if (stop) {
      break;
    }
  }

  return 0;
}

double elapsed(struct timeval *starttime, struct timeval *stoptime){
  double elapsed_time = 0;
  elapsed_time = (double)(stoptime->tv_sec - starttime->tv_sec) + ((double)(stoptime->tv_usec - starttime->tv_usec))/1000000;
  return elapsed_time;
}

int main(int argc, char **argv)
{
  // unsigned long expt;
  unsigned long size, elt_size;
  unsigned long tot_hot_size;
  int log_hot_size;
  struct timeval starttime, stoptime;
  double secs, gups;
  int i;
  void *p;
  struct gups_args** ga;
  pthread_t t[MAX_THREADS];



  if (argc != 10) {
    fprintf(stderr, "Usage: %s [threads] [updates per thread] [exponent] [data size (bytes)] [noremap/remap]\n", argv[0]);
    fprintf(stderr, "  threads\t\t\tnumber of threads to launch\n");
    fprintf(stderr, "  updates per thread\t\tnumber of updates per thread\n");
    fprintf(stderr, "  exponent\t\t\tlog size of region\n");
    fprintf(stderr, "  data size\t\t\tsize of data in array (in bytes)\n");
    fprintf(stderr, "  hot size\t\t\tlog size of hot set\n");
    fprintf(stderr, "  hot_prob\t\t\tthe probability of accessing hot spot\n");
    fprintf(stderr, "  phase_change_period\t\t\tperiod of changing hot spot\n");
    fprintf(stderr, "  tot_time\t\t\ttime limit in seconds\n");
    fprintf(stderr, "  path to save log\n");
    return 0;
  }

  gettimeofday(&starttime, NULL);

  threads = atoi(argv[1]);
  assert(threads <= MAX_THREADS);
  ga = (struct gups_args**)malloc(threads * sizeof(struct gups_args*));

  updates = atol(argv[2]);
  updates -= updates % 256;
  assert(updates > 0 && (updates % 256 == 0));
  size = atol(argv[3]);
  size -= (size % 256);
  assert(size > 0 && (size % 256 == 0));
  elt_size = atoi(argv[4]);
  log_hot_size = atof(argv[5]);
  tot_hot_size = (unsigned long)(1) << log_hot_size;

  hot_prob = atol(argv[6]);
  phase_change_period = atol(argv[7]);
  tot_time = atol(argv[8]);

  path = argv[9];

  fprintf(stderr, "%lu updates per thread (%d threads)\n", updates, threads);
  fprintf(stderr, "field of %lu bytes\n", size);
  fprintf(stderr, "%ld byte element size (%ld elements total)\n", elt_size, size / elt_size);

  p = mmap((void *)(0x1e00000000), size, PROT_READ | PROT_WRITE, MAP_FIXED | MAP_SHARED | MAP_ANONYMOUS | MAP_POPULATE | MAP_HUGETLB, -1, 0);

  if (p == MAP_FAILED) {
    printf("mmap failed!\n");
    perror("mmap");
    assert(0);
  }

  int mode = MPOL_BIND | (MPOL_F_NUMA_BALANCING);
  unsigned long nodemask = -1;

//   if (mbind((void *)(0x1e00000000), size, mode, &nodemask, sizeof(nodemask) * 8, MPOL_MF_MOVE)) {
//     printf("mbind failed!\n");
//     perror("set_mempolicy");
//     return 1;
//   }


  gettimeofday(&stoptime, NULL);
  fprintf(stderr, "Init took %.4f seconds\n", elapsed(&starttime, &stoptime));
  fprintf(stderr, "Region address: %p - %p\t size: %ld\n", p, (p + size), size);
  
  // nelems = (size / threads) / elt_size; // number of elements per thread
  nelems = (size) / elt_size;
  fprintf(stderr, "Elements per thread: %lu\n", nelems);

  fprintf(stderr, "hot_prob: %lu\n", hot_prob);
  fprintf(stderr, "phase_change_period: %lu\n", phase_change_period);
  fprintf(stderr, "tot_time: %lu\n", tot_time);

  memset(thread_gups, 0, sizeof(thread_gups));

  hotsetfile = fopen("hotsets.txt", "w");
  if (hotsetfile == NULL) {
    perror("fopen");
    assert(0);
  }
  

  gettimeofday(&stoptime, NULL);
  secs = elapsed(&starttime, &stoptime);
  fprintf(stderr, "Initialization time: %.4f seconds.\n", secs);

  hot_start = 0;
  hotsize = (tot_hot_size / threads) / elt_size;
  printf("hot_start: %p\thot_end: %p\thot_size: %lu\n", p + hot_start, p + hot_start + (hotsize * elt_size), hotsize);

  pthread_t print_thread;
  int pt = pthread_create(&print_thread, NULL, print_instantaneous_gups, NULL);
  assert(pt == 0);

  srand(0);
  lfsr = rand();
  hot_region_random = lfsr;
  hot_region_random = lfsr_fast(hot_region_random);
  for (int i = 0; i < 7; i++){
    hot_region_random = lfsr_fast(hot_region_random);
  }

  pthread_t timer_thread;
  int tt = pthread_create(&timer_thread, NULL, timing_thread, NULL);
  assert (tt == 0);

  fprintf(stderr, "Timing.\n");
  gettimeofday(&starttime, NULL);

  // spawn gups worker threads
  for (i = 0; i < threads; i++) {
    printf("starting thread [%d]\n", i);
    ga[i] = (struct gups_args*)malloc(sizeof(struct gups_args));
    ga[i]->tid = i;
    // ga[i]->field = p + (i * nelems * elt_size);
    ga[i]->field = p;
    ga[i]->iters = updates;
    ga[i]->size = nelems;
    ga[i]->elt_size = elt_size;
    ga[i]->hot_start = i * hotsize;        // hot set at start of thread's region
    ga[i]->hotsize = hotsize;
    int r = pthread_create(&t[i], NULL, do_gups, (void*)ga[i]);
    assert(r == 0);
  }

  // wait for worker threads
  for (i = 0; i < threads; i++) {
    int r = pthread_join(t[i], NULL);
    assert(r == 0);
  }
  gettimeofday(&stoptime, NULL);

  secs = elapsed(&starttime, &stoptime);
  printf("Elapsed time: %.4f seconds.\n", secs);
  gups = ((double)tot_updates) / (secs * 1.0e9);
  printf("GUPS2 = %.10f\n", gups);

  memset(thread_gups, 0, sizeof(thread_gups));

  for (i = 0; i < threads; i++) {
    free(ga[i]);
  }
  free(ga);

  munmap(p, size);

  return 0;
}