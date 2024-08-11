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

// static struct fifo_list dram_hot_list;
// static struct fifo_list dram_cold_list;
// static struct fifo_list nvm_hot_list;
// static struct fifo_list nvm_cold_list;
// static struct fifo_list dram_free_list;
// static struct fifo_list nvm_free_list;
// static ring_handle_t hot_ring;
// static ring_handle_t cold_ring;
// static ring_handle_t free_page_ring;
// static pthread_mutex_t free_page_ring_lock = PTHREAD_MUTEX_INITIALIZER;
// uint64_t global_clock = 0;

// uint64_t hemem_pages_cnt = 0;
// uint64_t other_pages_cnt = 0;
// uint64_t total_pages_cnt = 0;
// uint64_t zero_pages_cnt = 0;
uint64_t throttle_cnt = 0;
uint64_t unthrottle_cnt = 0;
// uint64_t cools = 0;

#define BASEPAGE_SIZE	  (4UL * 1024UL)
#define HUGEPAGE_SIZE 	(2UL * 1024UL * 1024UL)
#define GIGAPAGE_SIZE   (1024UL * 1024UL * 1024UL)
#define PAGE_SIZE 	    HUGEPAGE_SIZE

#define BASEPAGE_MASK	(BASEPAGE_SIZE - 1)
#define HUGEPAGE_MASK	(HUGEPAGE_SIZE - 1)
#define GIGAPAGE_MASK   (GIGAPAGE_SIZE - 1)

#define BASE_PFN_MASK	(BASEPAGE_MASK ^ UINT64_MAX)
#define HUGE_PFN_MASK	(HUGEPAGE_MASK ^ UINT64_MAX)
#define GIGA_PFN_MASK   (GIGAPAGE_MASK ^ UINT64_MAX)

// #define MIGRATE_PAGES_GRANULARITY (1)
// #define MIGRATE_MASK (BASE_PFN_MASK)

#define PERF_PAGES	(1 + (1 << 14))
#define SCANNING_THREAD_CPU (1)

// #define SAMPLE_PERIOD 1000
#define MAX_CPU_NUM 32
#define MAX_NPBUFTYPES 10

// static int sample_period[MAX_NPBUFTYPES] = {10000};

static uint64_t migrate_pages_granularity = 512;
static uint64_t migrate_mask = HUGE_PFN_MASK;
static uint64_t npbuftypes = 1;
static uint64_t cpu_num = 1;
static uint64_t monitor_time = 200;

static uint64_t pebs_pgpromoted_cnt = 0;

struct pebs_event {
  int sample_period;
  __u64	config;
} pebs_events[MAX_NPBUFTYPES];


// enum {
//   ALL_STORES = 1,
//   L3_MISS_LOAD = 0,
// };

uint64_t nsamples = 0;

// static struct perf_event_mmap_page *perf_page[PEBS_NPROCS][NPBUFTYPES];
static struct perf_event_mmap_page *perf_page[MAX_CPU_NUM][MAX_NPBUFTYPES];
int pfd[MAX_CPU_NUM][MAX_NPBUFTYPES];
// int pfd;

static bool should_stop = false;


struct perf_sample {
  struct perf_event_header header;
  __u64	ip;
  __u32 pid, tid;    /* if PERF_SAMPLE_TID */
  __u64 addr;        /* if PERF_SAMPLE_ADDR */
  // __u64 weight;      /* if PERF_SAMPLE_WEIGHT */
  __u64 phy_addr;
  /* __u64 data_src;    /\* if PERF_SAMPLE_DATA_SRC *\/ */
};


static long perf_event_open(struct perf_event_attr *hw_event, pid_t pid, 
    int cpu, int group_fd, unsigned long flags)
{
  int ret;

  ret = syscall(__NR_perf_event_open, hw_event, pid, cpu,
		group_fd, flags);
  return ret;
}

static struct perf_event_mmap_page* perf_setup(__u64 config, __u64 config1, __u64 cpu, __u64 type)
{
  struct perf_event_attr attr;

  memset(&attr, 0, sizeof(struct perf_event_attr));

  attr.type = PERF_TYPE_RAW;
  attr.size = sizeof(struct perf_event_attr);

  attr.config = config;
  attr.config1 = config1;
  attr.sample_period = pebs_events[type].sample_period;

  attr.sample_type = PERF_SAMPLE_IP | PERF_SAMPLE_TID | PERF_SAMPLE_ADDR | PERF_SAMPLE_PHYS_ADDR;
  attr.disabled = 0;
  //attr.inherit = 1;
  attr.exclude_kernel = 1;
  attr.exclude_hv = 1;
  attr.exclude_callchain_kernel = 1;
  attr.exclude_callchain_user = 1;
  attr.precise_ip = 1;

  pfd[cpu][type] = perf_event_open(&attr, -1, cpu, -1, 0);
  if(pfd[cpu][type] == -1) {
    perror("perf_event_open");
  }
  assert(pfd[cpu][type] != -1);

  size_t mmap_size = sysconf(_SC_PAGESIZE) * PERF_PAGES;
  /* printf("mmap_size = %zu\n", mmap_size); */
  struct perf_event_mmap_page *p = mmap(NULL, mmap_size, PROT_READ | PROT_WRITE, MAP_SHARED, pfd[cpu][type], 0);
  if(p == MAP_FAILED) {
    perror("mmap");
  }
  assert(p != MAP_FAILED);

  return p;
}


void *pebs_scan_thread()
{
  // cpu_set_t cpuset;
  // pthread_t thread;

  // thread = pthread_self();
  // CPU_ZERO(&cpuset);
  // CPU_SET(SCANNING_THREAD_CPU, &cpuset);
  // int s = pthread_setaffinity_np(thread, sizeof(cpu_set_t), &cpuset);
  // if (s != 0) {
  //   perror("pthread_setaffinity_np");
  //   assert(0);
  // }

  unsigned long count = migrate_pages_granularity;  // Number of pages to move.
  void *pages[migrate_pages_granularity];        // Array to store address of pages.
  int nodes[migrate_pages_granularity];          // Target node for each page.
  int status[migrate_pages_granularity];         // Return status for each page.
  int flags = MPOL_MF_MOVE_ALL;  // Move pages without invalidation.

  int debug = 0;

  for (int i = 0; i < migrate_pages_granularity; i++){
    nodes[i] = 0;
  }

  for(uint64_t z = 0;;++z) {
    for (int i = 0; i < cpu_num; i++){
      for (int j = 0; j < npbuftypes; j++){
        struct perf_event_mmap_page *p = perf_page[i][j];
        char *pbuf = (char *)p + p->data_offset;

        __sync_synchronize();

        if(p->data_head == p->data_tail) {
            continue;
        }

        struct perf_event_header *ph = (void *)(pbuf + (p->data_tail % p->data_size));
        struct perf_sample *ps;

        switch(ph->type) {
        case PERF_RECORD_SAMPLE:
            uint64_t huge_pfn;
            
            ps = (struct perf_sample*)ph;
            assert(ps != NULL);
            if(ps->addr != 0) {
              nsamples++;
              if (nsamples % 40000 == 0){
                // printf("addr: %llx, phy_addr: %llx\n", ps->addr, ps->phy_addr);
                ;
              }
              huge_pfn = ps->addr & migrate_mask;
              if (nsamples % 40000 == 0)
                // printf("huge_pfn: %llx\n", huge_pfn);
                ;

              for (int k = 0; k < migrate_pages_granularity; k++){
                pages[k] = (void *)(huge_pfn + k * BASEPAGE_SIZE);
              }
              memset(status, -1, migrate_pages_granularity * sizeof(int));

              int ret = 0;
              if (ps->phy_addr > 0x2080000000){
                ret = move_pages(ps->pid, migrate_pages_granularity, pages, nodes, status, flags);
                for (int k = 0; k < migrate_pages_granularity; k++){
                  if(status[k] == 0){
                    pebs_pgpromoted_cnt++;
                    // if (pebs_pgpromoted_cnt % 10000 == 0)
                    //   printf("pebs_pgpromoted_cnt: %lld\n", pebs_pgpromoted_cnt);
                  }
                }
              }
              else{
                break;
              }

              if (nsamples % 40000 == 0){
                for (int j = 0; j < migrate_pages_granularity; j++){
                  // printf("%d", status[j]);
                  ;
                }
                // printf("\n");
                ;
              }
              if (ret){
                debug++;
                if (debug % 20000 == 0)
                  // printf("move_pages return value: %d\n", ret);
                  ;
              }
            }
            break;
        case PERF_RECORD_THROTTLE:
        case PERF_RECORD_UNTHROTTLE:
            if (ph->type == PERF_RECORD_THROTTLE) {
                throttle_cnt++;
                if (throttle_cnt % 1000 == 0)
                  printf("throttle for 1000 times\n");
            }
            else {
                unthrottle_cnt++;
                if (unthrottle_cnt % 1000 == 0)
                  printf("unthrottle for 1000 times\n");
            }
            break;
        default:
            printf("Unknown type %u\n", ph->type);
            //assert(!"NYI");
            break;
        }

        p->data_tail += ph->size;

      }
    }
    usleep(1000);
    if (should_stop){
      return NULL;
    }
  }
  return NULL;
}


void pebs_shutdown()
{
  for (int i = 0; i < cpu_num; i++) {
    for (int j = 0; j < npbuftypes; j++) {
      ioctl(pfd[i][j], PERF_EVENT_IOC_DISABLE, 0);
      munmap(perf_page[i][j], sysconf(_SC_PAGESIZE) * PERF_PAGES);
    }
  }
}


void sigterm_handler(int signum) {
    printf("get SIGTERM, pebs_pgpromoted_cnt: %lld\n", pebs_pgpromoted_cnt);

    printf("final pebs_pgpromoted_cnt: %lld\n", pebs_pgpromoted_cnt);

    fflush(stdout);

    pebs_shutdown();
    // exitg
    exit(0); 
}


int main(int argc, char *argv[])
{
  pthread_t scan_thread;

  signal(SIGTERM, sigterm_handler);

  if (argc > 1){
    // usage: ./pebs_test <granularity> <cpu_number> <monitor_time> <event_number> <event 1 config> <event 1 sample_period> <event 2 config> <event 2 sample_period> ...
    if (argc < 7){
      printf("usage: %s <granularity> <cpu_number> <monitor_time> <event_number> <event 1 config> <event 1 sample_period> <event 2 config> <event 2 sample_period> ...\n", argv[0]);
      return 0;
    }
    migrate_pages_granularity = atoi(argv[1]);
    if (migrate_pages_granularity == 1){
      migrate_mask = BASE_PFN_MASK;
    }
    else if (migrate_pages_granularity == 512){
      migrate_mask = HUGE_PFN_MASK;
    }
    else{
      printf("error input: granularity only support 1 for base page or 512 for huge page\n");
      return 0;
    }

    cpu_num = atoi(argv[2]);
    if (cpu_num <= 0){
      printf("error: cpu_num should > 0\n");
      return 0;
    }

    monitor_time = atoi(argv[3]);
    if (monitor_time <= 0){
      printf("error: monitor_time should > 0\n");
      return 0;
    }

    npbuftypes = atoi(argv[4]);
    if (npbuftypes <= 0){
      printf("error: event_number should > 0\n");
      return 0;
    }

    for (int i = 0; i < npbuftypes; i++){
      char *endptr = NULL;
      pebs_events[i].config = strtol(argv[5 + 2 * i], &endptr, 16);
      if (*endptr != '\0' && *endptr != '\n'){
        printf("event %d config failed\n", i);
        return 0;
      }
      pebs_events[i].sample_period = atoi(argv[6 + 2 * i]);
    }
  }
  else{
    pebs_events[0].config = 0x82d0;
    pebs_events[0].sample_period = 5000;
  }

  printf("migrate_pages_granularity: %d, migrate_mask: %llx, cpu_num: %d, npbuftypes: %d\n", \
          migrate_pages_granularity, migrate_mask, cpu_num, npbuftypes);

  for (int i = 0; i < npbuftypes; i++){
    printf("event %d: config %llx,  sample_period %d\n", i, pebs_events[i].config, pebs_events[i].sample_period);
  }

  printf("monitor_time: %lld\n", monitor_time);

  // for(int z = 0; z < monitor_time; z++){
  //   should_stop = false;
  //   printf("moniter iteration: %d\n", z);
  //   for (int i = 0; i < cpu_num; i++){
  //     // perf_page[i][ALL_STORES] = perf_setup(0x82d0, 0, i, ALL_STORES);    // MEM_INST_RETIRED.ALL_STORES
  //     // perf_page[i][L3_MISS_LOAD] = perf_setup(0x01d3, 0, i, L3_MISS_LOAD);
  //     // perf_page[i][0] = perf_setup(0x82d0, 0, i, 0);
  //     for (int j = 0; j < npbuftypes; j++){
  //       perf_page[i][j] = perf_setup(pebs_events[j].config, 0, i, j);
  //     }
  //   }

  //   int r = pthread_create(&scan_thread, NULL, pebs_scan_thread, NULL);
  //   assert(r == 0);

  //   sleep(1);
  //   should_stop = true;

  //   if (pthread_join(scan_thread, NULL) != 0) {
  //       printf("pthread_join");
  //       exit(EXIT_FAILURE);
  //   }

  //   pebs_shutdown();
  // }

  for (int i = 0; i < cpu_num; i++){
    // perf_page[i][ALL_STORES] = perf_setup(0x82d0, 0, i, ALL_STORES);    // MEM_INST_RETIRED.ALL_STORES
    // perf_page[i][L3_MISS_LOAD] = perf_setup(0x01d3, 0, i, L3_MISS_LOAD);
    // perf_page[i][0] = perf_setup(0x82d0, 0, i, 0);
    for (int j = 0; j < npbuftypes; j++){
      perf_page[i][j] = perf_setup(pebs_events[j].config, 0, i, j);
    }
  }

  int r = pthread_create(&scan_thread, NULL, pebs_scan_thread, NULL);
  assert(r == 0);

  for(int z = 0; z < monitor_time; z++){
    
    sleep(1);

    for (int i = 0; i < cpu_num; i++) {
      for (int j = 0; j < npbuftypes; j++) {
        ioctl(pfd[i][j], PERF_EVENT_IOC_DISABLE, 0);
      }
    }

    for (int i = 0; i < cpu_num; i++) {
      for (int j = 0; j < npbuftypes; j++) {
        ioctl(pfd[i][j], PERF_EVENT_IOC_ENABLE, 0);
      }
    }
  }

  pebs_shutdown();

  printf("pebs finished!\n");
  
  return 0;
}

