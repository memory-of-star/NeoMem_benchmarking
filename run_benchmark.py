import json
import os
import subprocess
import argparse
import sys
import set_mode
import set_state_monitor
import time
import multiprocessing
import strategy
import psutil

def find_pids_by_cmdline(search_string):
    pids = []
    for proc in psutil.process_iter(attrs=['pid', 'cmdline']):
        try:
            print(proc.info['cmdline'])
            if proc.info['cmdline'] and search_string in ' '.join(proc.info['cmdline']):
                pids.append(proc.info['pid'])
        except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
            pass
    return pids


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="input the json file")
    parser.add_argument('--config', type=str, default='./method_config/reset.json', help='the json file specify the method')
    parser.add_argument('--benchmark', type=str, default='XSBench', help='the benchmark to test')
    parser.add_argument('--calculate_bandwidth', action='store_true')
    parser.add_argument('--neomem_threshold_path', type=str, default='./output/neomem_threshold/tmp', help='the path to store the neomem threshold trace')

    args = parser.parse_args()
    
    ret = set_mode.set_mode(args.config)

    with open(args.config, 'r') as config:
        config_data = json.load(config)
    
    # method = args.config.split('/')[-1][:args.config.split('/')[-1].find('.')]
    method = config_data["method"]

    if os.path.exists("/sys/kernel/mm/neomem/neomem_states_accumulated"):
        with open("/sys/kernel/mm/neomem/neomem_states_accumulated", 'r') as f:
            lines = f.readlines()
            for line in lines:
                lst = line.split()

                if lst[0] == 'write':
                    neomem_write_accumulated_cnt_begin = int(lst[-1])
                elif lst[0] == 'read':
                    neomem_read_accumulated_cnt_begin = int(lst[-1])



    with open("/proc/vmstat", 'r') as f:
        lines = f.readlines()
        for line in lines:
            lst = line.split()

            if lst[0] == 'neomem_migrate_pages':
                neomem_migrate_pages_begin = int(lst[1])
            elif lst[0] == 'pgpromote_success':
                pgpromote_success_begin = int(lst[1])
            elif lst[0] == 'abit_pgpromoted':
                abit_pgpromoted_begin = int(lst[1])
            elif lst[0] == 'pgdemote_kswapd':
                pgdemote_kswapd_begin = int(lst[1])
            elif lst[0] == 'pgdemote_direct':
                pgdemote_direct_begin = int(lst[1])
            elif lst[0] == 'numa_pages_migrated':
                numa_pages_migrated_begin = int(lst[1])



    if args.calculate_bandwidth:
        readbandwidth_cmd = ["./readbandwidth"]
        readbandwidth_process = subprocess.Popen(readbandwidth_cmd, stdout=sys.stdout, stderr=subprocess.PIPE)

        os.system(f"./write_to_file 10000 /sys/kernel/mm/neomem/neomem_scanning_interval_us > tmp")
        os.system(f"./write_to_file 500 /sys/kernel/mm/neomem/neomem_scanning_reset_period > tmp")
        os.system(f"./write_to_file 500 /sys/kernel/mm/neomem/neomem_hist_scan_period > tmp")
        os.system(f"./write_to_file 1000000000 /sys/kernel/mm/neomem/neomem_scanning_hotness_threshold > tmp")
        os.system("./write_to_file 1 /sys/kernel/mm/neomem/neomem_scanning_enabled > tmp")

    if method == "neomem":
        # print("neomem!")
        # sys.stdout = open('strategy_output.txt', 'w')
        p_neomem_strategy = multiprocessing.Process(target=strategy.neomem_strategy, args=(args.neomem_threshold_path,))
        p_neomem_strategy.start()

    if args.benchmark == 'XSBench':
        os.system("./XSBench/openmp-threading/XSBench -t 32 -g 35000 -p 30000000")
    elif args.benchmark == 'pageranking': 
        os.system("./gapbs/pr -g 26 -n 16")
    elif args.benchmark == 'silo':
        os.system("./silo/out-perf.masstree/benchmarks/dbtest --verbose --bench ycsb --num-threads 32 --scale-factor 80000 --ops-per-worker=100000000 --slow-exit")
    elif args.benchmark == '603.bwaves':
        os.system("cd ./spec2017/ && source ./shrc && runcpu --config=cyq-try1 603.bwaves")
    elif args.benchmark == '654.roms':
        os.system("cd ./spec2017/ && source ./shrc && runcpu --config=cyq-try1 654.roms")
    elif args.benchmark == 'btree':
        os.system("./vmitosis-workloads/bin/bench_btree_mt")
    elif args.benchmark == 'gups':
        gups_cmd = ["./microbenchmarks/gups-hotset-changed", "32", "90000000000", "19000000000", "8", "31", "90", "600", "600", f"./output/gups_curve/{method}"]
        gups_process = subprocess.Popen(gups_cmd, stdout=sys.stdout, stderr=subprocess.PIPE)
        gups_process.wait()
    elif args.benchmark == 'deathstarbench':
        # os.system(f"cd ./DeathStarBench/socialNetwork && docker-compose up -d && python3 scripts/init_social_graph.py --graph=socfb-Reed98 && ../wrk2/wrk -D exp -t 32 -c 32 -d 100s -L -s ./wrk2/scripts/social-network/compose-post.lua http://localhost:8080/wrk2-api/post/compose -R 4k")
        os.system(f"cd ./DeathStarBench/socialNetwork && docker-compose up -d && python3 scripts/init_social_graph.py --graph=socfb-Reed98 && ../wrk2/wrk -D exp -t 32 -c 32 -d 100s -L -s ./wrk2/scripts/social-network/compose-post.lua http://localhost:8080/wrk2-api/post/compose -R 4k")
        os.system(f"docker stop $(docker ps -aq) && docker rm $(docker ps -aq)")
    elif args.benchmark == 'gups_convergence_analysis':
        gups_cmd = ["./microbenchmarks/gups-hotset-changed", "32", "90000000000", "19000000000", "8", "31", "90", "600", "900", f"./output/gups_convergence_analysis/{method}"]
        gups_process = subprocess.Popen(gups_cmd, stdout=sys.stdout, stderr=subprocess.PIPE)
        gups_process.wait()
    
    if method == "neomem":
        p_neomem_strategy.terminate()
        p_neomem_strategy.join()
    elif method == "pebs" or method == "pebs_huge":
        # pass
        ret.terminate()
        ret.wait()


    if args.calculate_bandwidth:
        readbandwidth_process.terminate()
        readbandwidth_process.wait()


    if os.path.exists("/sys/kernel/mm/neomem/neomem_states_accumulated"):
        with open("/sys/kernel/mm/neomem/neomem_states_accumulated", 'r') as f:
            lines = f.readlines()
            for line in lines:
                lst = line.split()

                if lst[0] == 'write':
                    neomem_write_accumulated_cnt_end = int(lst[-1])
                elif lst[0] == 'read':
                    neomem_read_accumulated_cnt_end = int(lst[-1])



    with open("/proc/vmstat", 'r') as f:
        lines = f.readlines()
        for line in lines:
            lst = line.split()

            if lst[0] == 'neomem_migrate_pages':
                neomem_migrate_pages_end = int(lst[1])
            elif lst[0] == 'pgpromote_success':
                pgpromote_success_end = int(lst[1])
            elif lst[0] == 'abit_pgpromoted':
                abit_pgpromoted_end = int(lst[1])
            elif lst[0] == 'pgdemote_kswapd':
                pgdemote_kswapd_end = int(lst[1])
            elif lst[0] == 'pgdemote_direct':
                pgdemote_direct_end = int(lst[1])
            elif lst[0] == 'numa_pages_migrated':
                numa_pages_migrated_end = int(lst[1])
    try:
        print("neomem_migrate_pages diff: ", neomem_migrate_pages_end-neomem_migrate_pages_begin)
    except:
        pass
    try:
        print("pgpromote_success diff: ", pgpromote_success_end-pgpromote_success_begin)
    except:
        pass
    try:
        print("abit_pgpromoted diff: ", abit_pgpromoted_end-abit_pgpromoted_begin)
    except:
        pass
    try:
        print("demoted diff: ", pgdemote_kswapd_end-pgdemote_kswapd_begin+pgdemote_direct_end-pgdemote_direct_begin)
    except:
        pass
    try:
        print("numa_pages_migrated diff: ", numa_pages_migrated_end-numa_pages_migrated_begin)
    except:
        pass

    try:
        print("neomem_write_accumulated_cnt: ", neomem_write_accumulated_cnt_end-neomem_write_accumulated_cnt_begin)
    except:
        pass

    try:
        print("neomem_read_accumulated_cnt: ", neomem_read_accumulated_cnt_end-neomem_read_accumulated_cnt_begin)
    except:
        pass
