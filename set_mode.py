import os
import argparse
import json
import sys
import subprocess


def reset_vals():
    print("reset all environment")
    # os.system("echo off > /sys/devices/system/cpu/smt/control")
    # for i in range(32):
    #     os.system(f"echo 1 > /sys/devices/system/cpu/cpu{i}/online")
    #     os.system(f"echo performance > /sys/devices/system/cpu/cpu{i}/cpufreq/scaling_governor")
    # os.system("echo 0 > /sys/devices/system/cpu/intel_pstate/no_turbo")
    # os.system("echo 1 > /sys/kernel/mm/numa/demotion_enabled")
    # os.system("echo 0 > /proc/sys/kernel/numa_balancing")
    # os.system("echo Y > /sys/module/damon_migrate/parameters/node1_is_toptier")
    # os.system("echo 0 > /sys/kernel/mm/neomem/neomem_scanning_enabled")
    # os.system("echo N > /sys/module/damon_migrate/parameters/enabled")
    # os.system("echo 0 > /sys/kernel/mm/neopebs/neopebs_enabled")
    # os.system("echo 0 > /proc/sys/kernel/perf_cpu_time_max_percent")
    # os.system("sync")
    # os.system("echo 3 > /proc/sys/vm/drop_caches")
    # os.system("echo 15 > /proc/sys/vm/zone_reclaim_mode")
    # os.system("echo 10 > /proc/sys/vm/watermark_scale_factor")
    # os.system("echo never > /sys/kernel/mm/transparent_hugepage/enabled")
    # os.system("echo never > /sys/kernel/mm/transparent_hugepage/defrag")
    # os.system("swapoff -a")

    os.system("./write_to_file off /sys/devices/system/cpu/smt/control")
    for i in range(32):
        os.system(f"./write_to_file 1 /sys/devices/system/cpu/cpu{i}/online")
        os.system(f"./write_to_file performance /sys/devices/system/cpu/cpu{i}/cpufreq/scaling_governor")
    os.system("./write_to_file 0 /sys/devices/system/cpu/intel_pstate/no_turbo")
    os.system("./write_to_file 1 /sys/kernel/mm/numa/demotion_enabled")
    os.system("./write_to_file 0 /proc/sys/kernel/numa_balancing")
    os.system("./write_to_file Y /sys/module/damon_migrate/parameters/node1_is_toptier")
    os.system("./write_to_file 0 /sys/kernel/mm/neomem/neomem_scanning_enabled")
    os.system("./write_to_file N /sys/module/damon_migrate/parameters/enabled")
    os.system("./write_to_file 0 /sys/kernel/mm/neopebs/neopebs_enabled")
    os.system("./write_to_file 0 /proc/sys/kernel/perf_cpu_time_max_percent")
    os.system("sync")
    os.system("./write_to_file 3 /proc/sys/vm/drop_caches")
    os.system("./write_to_file 15 /proc/sys/vm/zone_reclaim_mode")
    os.system("./write_to_file 10 /proc/sys/vm/watermark_scale_factor")
    os.system("./write_to_file never /sys/kernel/mm/transparent_hugepage/enabled")
    os.system("./write_to_file never /sys/kernel/mm/transparent_hugepage/defrag")
    # os.system("./swapoff")
    
    


def set_neomem(config_data):
    print("set neomem parameters")
    print("migration_interval: ", config_data['migration_interval'], "us")
    print("clear_interval: ", config_data['clear_interval'], "iteration")
    print("threshold: ", config_data['threshold'], "accesses")

    os.system(f"./write_to_file {config_data['migration_interval']} /sys/kernel/mm/neomem/neomem_scanning_interval_us")
    os.system(f"./write_to_file {config_data['clear_interval']} /sys/kernel/mm/neomem/neomem_scanning_reset_period")
    os.system(f"./write_to_file {config_data['hist_period']} /sys/kernel/mm/neomem/neomem_hist_scan_period")
    os.system(f"./write_to_file {config_data['threshold']} /sys/kernel/mm/neomem/neomem_scanning_hotness_threshold")
    os.system("./write_to_file 1 /sys/kernel/mm/neomem/neomem_scanning_enabled")
    
def set_numatiered(config_data):
    print("set numatiered parameters")
    print("hot_threshold_ms: ", config_data['hot_threshold_ms'])
    print("scan_delay_ms: ", config_data['scan_delay_ms'])
    print("scan_period_max_ms: ", config_data['scan_period_max_ms'])
    print("scan_period_min_ms: ", config_data['scan_period_min_ms'])
    print("scan_size_mb: ", config_data['scan_size_mb'])
    os.system(f"./write_to_file {config_data['hot_threshold_ms']} /sys/kernel/debug/sched/numa_balancing/hot_threshold_ms")
    os.system(f"./write_to_file {config_data['scan_delay_ms']} /sys/kernel/debug/sched/numa_balancing/scan_delay_ms")
    os.system(f"./write_to_file {config_data['scan_period_max_ms']} /sys/kernel/debug/sched/numa_balancing/scan_period_max_ms")
    os.system(f"./write_to_file {config_data['scan_period_min_ms']} /sys/kernel/debug/sched/numa_balancing/scan_period_min_ms")
    os.system(f"./write_to_file {config_data['scan_size_mb']} /sys/kernel/debug/sched/numa_balancing/scan_size_mb")
    os.system("./write_to_file 2 /proc/sys/kernel/numa_balancing")
    os.system("./write_to_file N /sys/module/damon_migrate/parameters/node1_is_toptier")
    
def set_abit(config_data):
    print("set abit parameters")
    print("aggr_interval: ", config_data['aggr_interval'], "us")
    print("sample_interval: ", config_data['sample_interval'], "us")
    print("min_accesses: ", config_data['min_accesses'])
    print("quota_ms: ", config_data['quota_ms'])
    os.system(f"./write_to_file {config_data['aggr_interval']} /sys/module/damon_migrate/parameters/aggr_interval")
    os.system(f"./write_to_file {config_data['sample_interval']} /sys/module/damon_migrate/parameters/sample_interval")
    os.system(f"./write_to_file {config_data['min_accesses']} /sys/module/damon_migrate/parameters/min_access")
    os.system(f"./write_to_file {config_data['quota_ms']} /sys/module/damon_migrate/parameters/quota_ms")
    os.system(f"./write_to_file {config_data['quota_sz']} /sys/module/damon_migrate/parameters/quota_sz")
    os.system("./write_to_file Y /sys/module/damon_migrate/parameters/enabled")
    os.system("./write_to_file Y /sys/module/damon_migrate/parameters/commit_inputs")
    os.system("./write_to_file 200 /proc/sys/vm/watermark_scale_factor")
    

def set_pebs(config_data):
    print("pebs experiment")
    print(f"granularity: {config_data['granularity']}")
    print(f"cpu: {config_data['cpu']}")
    event_num = len(config_data['event'])
    print(f"event_num: {event_num}")
    tail = ""
    for i in range(event_num):
        print("event ", i, ": ", "config", config_data['event'][i]['config'], ", ", "sample_period: ", config_data['event'][i]['sample_period'])
        tail += "_" + config_data['event'][i]['config'] + "_" + config_data['event'][i]['sample_period']
    
    pebs_cmd = ['./pebs_test', config_data['granularity'], config_data['cpu'], str(config_data['time']), str(event_num)]
    for i in range(event_num):
        pebs_cmd += [config_data['event'][i]['config'], config_data['event'][i]['sample_period']]
    print("pebs_cmd: ", " ".join(pebs_cmd))
    pebs_process = subprocess.Popen(pebs_cmd, stdout=sys.stdout, stderr=subprocess.PIPE)

    return pebs_process

    

def set_mode(config_path):
    with open(config_path, 'r') as config:
        config_data = json.load(config)
    if config_data["method"] == "reset":
        reset_vals()
    elif config_data["method"] == "neomem":
        reset_vals()
        set_neomem(config_data)
    elif config_data["method"] == "numabalancing":
        reset_vals()
        set_numatiered(config_data)
    elif config_data["method"] == "abit":
        reset_vals()
        set_abit(config_data)
    elif config_data["method"] == "pebs":
        reset_vals()
        return set_pebs(config_data)
    elif config_data["method"] == "tpp":
        reset_vals()
        set_numatiered(config_data)
    elif config_data["method"] == "neoprof":
        reset_vals()
        set_neomem(config_data)
        
        
if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="input the json file")
    parser.add_argument('--config', type=str, default='./method_config/reset.json', help='the path to migration mode config file')

    args = parser.parse_args()
    set_mode(args.config)
