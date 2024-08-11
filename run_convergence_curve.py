import os
import time

if __name__ == '__main__':
    benchmarks = ['gups_convergence_analysis']
    methods = ['abit', 'numabalancing', 'pebs', 'reset', 'neoprof']

    for bench in benchmarks:
        for method in methods:
            for i in range(1):
                print(f"Running {bench} with {method}, trial {i+1} of 1")
                os.system(f"python3 run_benchmark.py --config ./method_config/{method}.json --benchmark {bench}  > ./output/experiment_output/{method}_{bench}_trial{i+1}.txt")
                print(f"Finished {bench} with {method}, trial {i+1} of 1")
                time.sleep(3)