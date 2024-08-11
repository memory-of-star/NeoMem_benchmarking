import numpy as np
import os
import copy
import pandas as pd
import matplotlib.pyplot as plt

benchmarks = ['pageranking', 'XSBench', 'silo', '603.bwaves', '654.roms', 'btree', 'gups', 'deathstarbench']
methods = ['neomem', 'pebs', 'abit', 'numabalancing','TPP', 'reset']

performance_array = np.zeros((len(methods), len(benchmarks)))
slow_tier_access_array = np.zeros((len(methods), len(benchmarks)))
promote_pages_array = np.zeros((len(methods), len(benchmarks)))
demote_pages_array = np.zeros((len(methods), len(benchmarks)))
trial_num = np.zeros((len(methods), len(benchmarks)))

print(trial_num)

for method in methods:
    for bench in benchmarks:
        for i in range(1, 6):
            if os.path.exists(f"./output/experiment_output/{method}_{bench}_trial{i}.txt"):
                with open(f"./output/experiment_output/{method}_{bench}_trial{i}.txt", "r") as f:
                    lines = f.readlines()
                    performance = 0
                    slow_tier_access = 0
                    promote = 0
                    demote = 0
                    trial_valid = 0

                    if bench == 'pageranking':
                        for line in lines:
                            if "Average Time" in line:
                                performance = float(line.split(" ")[-1])
                                trial_num[methods.index(method), benchmarks.index(bench)] += 1
                                trial_valid = 1
                    elif bench == 'XSBench':
                        for line in lines:
                            if "Runtime:" in line:
                                performance = float(line.split(" ")[-2])
                                trial_num[methods.index(method), benchmarks.index(bench)] += 1
                                trial_valid = 1
                    elif bench == 'silo':
                        for line in lines:
                            if "e+" in line:
                                performance = float(line.split(" ")[0])
                                trial_num[methods.index(method), benchmarks.index(bench)] += 1
                                trial_valid = 1
                    elif bench == 'btree':
                        for line in lines:
                            if "Took:" in line:
                                performance = float(line.split()[-1])
                                trial_num[methods.index(method), benchmarks.index(bench)] += 1
                                trial_valid = 1
                                break
                    elif bench == '603.bwaves':
                        for line in lines:
                            if "total seconds elapsed" in line:
                                performance = float(line.split()[-4])
                                trial_num[methods.index(method), benchmarks.index(bench)] += 1
                                trial_valid = 1
                    elif bench == '654.roms':
                        for line in lines:
                            if "total seconds elapsed" in line:
                                performance = float(line.split()[-4])
                                trial_num[methods.index(method), benchmarks.index(bench)] += 1
                                trial_valid = 1
                    elif bench == 'gups':
                        for line in lines:
                            if "GUPS2" in line:
                                performance = float(line.split()[-1])
                                trial_num[methods.index(method), benchmarks.index(bench)] += 1
                                trial_valid = 1
                    elif bench == 'deathstarbench':
                        for line in lines:
                            if "99.000%" in line:
                                # print(line.split()[-1][0:-1])
                                performance = float(line.split()[-1][0:-1])
                                trial_num[methods.index(method), benchmarks.index(bench)] += 1
                                trial_valid = 1

                    performance_array[methods.index(method), benchmarks.index(bench)] += performance

                    if trial_valid == 1:

                        for line in lines:
                            if "demoted diff:" in line:
                                demote = int(line.split()[-1])
                                
                            if "total_access:" in line:
                                slow_tier_access = int(line.split()[-1])
                                
                        demote_pages_array[methods.index(method), benchmarks.index(bench)] += demote
                        slow_tier_access_array[methods.index(method), benchmarks.index(bench)] += slow_tier_access

                        if method == 'neomem':
                            for line in lines:
                                if "neomem_migrate_pages diff:" in line:
                                    promote = int(line.split()[-1])
                        elif method == 'pebs':
                            for line in lines:
                                if "final pebs_pgpromoted_cnt:" in line:
                                    promote = int(line.split()[-1])
                        elif method == 'abit':
                            for line in lines:
                                if "abit_pgpromoted diff:" in line:
                                    promote = int(line.split()[-1])
                        elif method == 'numabalancing':
                            for line in lines:
                                if "numa_pages_migrated diff:" in line:
                                    promote = int(line.split()[-1])
                        elif method == 'reset':
                            promote = 0
                        elif method == 'TPP':
                            for line in lines:
                                if "numa_pages_migrated diff:" in line:
                                    promote = int(line.split()[-1])

                            
                        promote_pages_array[methods.index(method), benchmarks.index(bench)] += promote



for method in methods:
    for bench in benchmarks:
        performance_array[methods.index(method), benchmarks.index(bench)] = performance_array[methods.index(method), benchmarks.index(bench)] / trial_num[methods.index(method), benchmarks.index(bench)]

        slow_tier_access_array[methods.index(method), benchmarks.index(bench)] = slow_tier_access_array[methods.index(method), benchmarks.index(bench)] / trial_num[methods.index(method), benchmarks.index(bench)]
        promote_pages_array[methods.index(method), benchmarks.index(bench)] = promote_pages_array[methods.index(method), benchmarks.index(bench)] / trial_num[methods.index(method), benchmarks.index(bench)]
        demote_pages_array[methods.index(method), benchmarks.index(bench)] = demote_pages_array[methods.index(method), benchmarks.index(bench)] / trial_num[methods.index(method), benchmarks.index(bench)]

print(trial_num)
print(performance_array)

performance_array_normalized = copy.deepcopy(performance_array)

for method in methods:
    for bench in benchmarks:
        if bench not in ['gups', 'silo']:
            performance_array_normalized[methods.index(method), benchmarks.index(bench)] = performance_array[methods.index('pebs'), benchmarks.index(bench)] / performance_array[methods.index(method), benchmarks.index(bench)]
        else:
            performance_array_normalized[methods.index(method), benchmarks.index(bench)] = performance_array[methods.index(method), benchmarks.index(bench)] / performance_array[methods.index('pebs'), benchmarks.index(bench)]

print(performance_array_normalized)


methods_name = ['NeoMem', 'PEBS', 'PTE-Scan', 'AutoNUMA', 'TPP', 'First-touch NUMA']

data = pd.DataFrame(performance_array_normalized, index=methods_name, columns=benchmarks)
print(data)
fig, ax = plt.subplots(figsize=(10, 6))
bar_width = 0.15
index = np.arange(len(benchmarks))
for i, method in enumerate(methods_name):
    ax.bar(index + i * bar_width, data.loc[method], bar_width, label=method)
ax.set_xlabel('Benchmarks')
ax.set_ylabel('Normalized Performance')
ax.set_title('Fig.12 End-to-end Performance Comparison')
ax.set_xticks(index + bar_width * (len(methods_name) - 1) / 2)
ax.set_xticklabels(benchmarks)
ax.legend()
plt.savefig('./output/fig_output/performance.png')


data = pd.DataFrame(slow_tier_access_array, index=methods_name, columns=benchmarks)
fig, ax = plt.subplots(figsize=(10, 6))
bar_width = 0.15
index = np.arange(len(benchmarks))
for i, method in enumerate(methods_name):
    ax.bar(index + i * bar_width, data.loc[method], bar_width, label=method)
ax.set_xlabel('Benchmarks')
ax.set_ylabel('Sampled Slow-tier Access')
ax.set_yscale('log')
ax.set_title('Fig.13 Slow-Tier (CXL Memory) Traffic')
ax.set_xticks(index + bar_width * (len(methods_name) - 1) / 2)
ax.set_xticklabels(benchmarks)
ax.legend()
plt.savefig('./output/fig_output/slow_tier_access.png')


data = pd.DataFrame(promote_pages_array, index=methods_name, columns=benchmarks)
fig, ax = plt.subplots(figsize=(10, 6))
bar_width = 0.15
index = np.arange(len(benchmarks))
for i, method in enumerate(methods_name):
    ax.bar(index + i * bar_width, data.loc[method], bar_width, label=method)
ax.set_xlabel('Benchmarks')
ax.set_ylabel('Promoted Pages')
ax.set_yscale('log')
ax.set_title('Fig.13 Promotion Traffic')
ax.set_xticks(index + bar_width * (len(methods_name) - 1) / 2)
ax.set_xticklabels(benchmarks)
ax.legend()
plt.savefig('./output/fig_output/promote.png')


data = pd.DataFrame(demote_pages_array, index=methods_name, columns=benchmarks)
fig, ax = plt.subplots(figsize=(10, 6))
bar_width = 0.15
index = np.arange(len(benchmarks))
for i, method in enumerate(methods_name):
    ax.bar(index + i * bar_width, data.loc[method], bar_width, label=method)
ax.set_xlabel('Benchmarks')
ax.set_ylabel('Demoted Pages')
ax.set_yscale('log')
ax.set_title('Fig.13 Demotion Traffic')
ax.set_xticks(index + bar_width * (len(methods_name) - 1) / 2)
ax.set_xticklabels(benchmarks)
ax.legend()
plt.savefig('./output/fig_output/demote.png')


# to get the gups curve
 
methods = ['neoprof', 'pebs', 'abit', 'numabalancing', 'reset']
methods_name = ['NeoProf', 'PEBS', 'PTE-Scan', 'Hint-fault', 'Baseline']

# gups = np.zeros((len(methods), 200))
time = list(range(1,201))

plt.clf()

for method in methods:
    with open(f"./output/gups_convergence_analysis/{method}", "r") as f:
        lines = f.readlines()
        gups = list(map(float, lines))

    plt.plot(time, gups[550:750], label=methods_name[methods.index(method)])

plt.xlabel('Time (s)')
plt.ylabel('GUPS')
plt.legend()

plt.savefig('./output/fig_output/convergence_analysis.png')

