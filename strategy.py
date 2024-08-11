import os
import numpy as np
import time
import copy
import sys

def get_neomem_migrate_info():

    neomem_migrate_info = {}
    
    with open("/proc/vmstat", "r") as f:
        lines = f.readlines()

    for line in lines:
        name, number = line.split()
        if "neomem" in name:
            neomem_migrate_info[name] = int(number)
    
    return neomem_migrate_info


def get_neomem_hist_info():

    neomem_hist_info = {}

    with open("/sys/kernel/mm/neomem/neomem_hist", "r") as f:
        lines = f.readlines()

    for line in lines:
        _, hist_bin, number = line.split()
        neomem_hist_info[int(hist_bin[:-1])] = int(number)

    return neomem_hist_info


def get_neomem_bandwidth_info():

    neomem_bandwidth_info = {}

    with open("/sys/kernel/mm/neomem/neomem_states_show") as f:
        lines = f.readlines()
    
    for line in lines:
        line_lst = line.split()
        neomem_bandwidth_info[line_lst[0]] = int(line_lst[-1])

    return neomem_bandwidth_info


def get_neomem_hist_percentile(percentile):

    neomem_hist_info = get_neomem_hist_info()

    hist_sum = np.sum(list(neomem_hist_info.values()))

    percentile_sum = 0

    percentile_value = 0

    for i in sorted(neomem_hist_info.keys()):
        
        percentile_sum += neomem_hist_info[i]
        
        if percentile_sum >= percentile * hist_sum:
            percentile_value = i
            break

    return percentile_value


def get_neomem_hist_percentile_reversed(percentile):

    neomem_hist_info = get_neomem_hist_info()

    hist_sum = np.sum(list(neomem_hist_info.values()))

    percentile_sum = 0

    percentile_value = 0

    for i in list(sorted(neomem_hist_info.keys()))[::-1]:
        
        percentile_sum += neomem_hist_info[i]
        
        if percentile_sum >= percentile * hist_sum:
            percentile_value = i
            break

    if percentile_value <= 0:
        percentile_value = 1

    return percentile_value


def get_neomem_error_bound():
    mid_value = get_neomem_hist_percentile(0.5)
    return mid_value


def adjust_percentile(neomem_migrate_info_prev, neomem_hist_info_prev, neomem_bandwidth_info_prev, neomem_migrate_info, neomem_hist_info, neomem_bandwidth_info, \
                      lower_bound_percentile, higher_bound_percentile, current_percentile, quota):
    
    ret_percentile = current_percentile
    
    neomem_migrate_pages = neomem_migrate_info["neomem_migrate_pages"] - neomem_migrate_info_prev["neomem_migrate_pages"]
    neomem_add_hot_page = neomem_migrate_info["neomem_add_hot_page"] - neomem_migrate_info_prev["neomem_add_hot_page"]
    neomem_migrate_pages_remained = neomem_migrate_info["neomem_migrate_pages_remained"] - neomem_migrate_info_prev["neomem_migrate_pages_remained"]
    neomem_hot_after_demoted = neomem_migrate_info["neomem_hot_after_demoted"] - neomem_migrate_info_prev["neomem_hot_after_demoted"]
    neomem_hot_page_candidate = neomem_migrate_info["neomem_hot_page_candidate"] - neomem_migrate_info_prev["neomem_hot_page_candidate"]

    bandwidth_prev = (neomem_bandwidth_info_prev["write"] + neomem_bandwidth_info_prev["read"]) / neomem_bandwidth_info_prev["total"]
    bandwidth = (neomem_bandwidth_info["write"] + neomem_bandwidth_info["read"]) / neomem_bandwidth_info["total"]

    if neomem_migrate_pages < quota:
        ret_percentile = ((1 + bandwidth)/((1+(neomem_hot_after_demoted / (neomem_migrate_pages + 1)))**2)) * ret_percentile
    else:
        ret_percentile = ret_percentile // 2

    # print("bandwidth: ", bandwidth)
    # print("neomem_migrate_pages: ", neomem_migrate_pages)
    

    ret_percentile = max(ret_percentile, lower_bound_percentile)
    ret_percentile = min(ret_percentile, higher_bound_percentile)
    
    # with open("./strategy_percentile", "a+") as f:
    #     f.write(f"current percentile: {ret_percentile}")
    # os.system(f"echo \"current percentile: {ret_percentile}\" >> ./strategy_percentile")
    #print(f"current percentile: {ret_percentile}")
    # print("demote: ", neomem_hot_after_demoted / (neomem_migrate_pages + 1))

    return ret_percentile

def neomem_strategy(path=None):

    neomem_migrate_info_prev = get_neomem_migrate_info()
    neomem_hist_info_prev = get_neomem_hist_info()
    neomem_bandwidth_info_prev = get_neomem_bandwidth_info()
    neomem_error_bound_prev = get_neomem_error_bound()

    lower_bound_percentile = 1
    higher_bound_percentile = 156
    current_percentile = 10

    scale_factor = 10000

    quota = 8192 * 256


    if path is not None:
        with open(path, "w") as f:
            f.write("")


    while True:
        neomem_migrate_info = get_neomem_migrate_info()
        neomem_hist_info = get_neomem_hist_info()
        neomem_bandwidth_info = get_neomem_bandwidth_info()
        neomem_error_bound = get_neomem_error_bound()

        # hist_sum = np.sum(list(neomem_hist_info.values()))
        # hist_sum_prev = np.sum(list(neomem_hist_info_prev.values()))

        # neomem_hist_info_current = copy.deepcopy(neomem_hist_info)
        # if hist_sum > 1.1 * hist_sum_prev:
        #     neomem_hist_info_current = {key: neomem_hist_info_current[key] - neomem_hist_info_prev.get(key, 0) for key in neomem_hist_info_current if key in neomem_hist_info_prev}
        
        # print(neomem_hist_info_current)

        current_percentile = adjust_percentile(neomem_migrate_info_prev, neomem_hist_info_prev, neomem_bandwidth_info_prev, neomem_migrate_info, neomem_hist_info, neomem_bandwidth_info, lower_bound_percentile, higher_bound_percentile, current_percentile, quota)

        neomem_percentile_value = get_neomem_hist_percentile_reversed(current_percentile / scale_factor)
        
        neomem_migrate_info_prev = neomem_migrate_info
        neomem_hist_info_prev = neomem_hist_info
        neomem_bandwidth_info_prev = neomem_bandwidth_info
        neomem_error_bound_prev = neomem_error_bound
        
        if path is not None:
            with open(path, "a+") as f:
                f.write(f"neomem_percentile_value: {neomem_percentile_value}\n")

        os.system(f"./write_to_file {neomem_percentile_value} /sys/kernel/mm/neomem/neomem_scanning_hotness_threshold > tmp")

        time.sleep(1)


if __name__ == "__main__":
    neomem_strategy()
