import os
import time

if __name__ == '__main__':
    benchmarks = ['pageranking', 'XSBench', 'silo', '603.bwaves', '654.roms', 'btree', 'gups']
    methods = ['abit', 'numabalancing', 'pebs', 'reset', 'neomem']

    # because the performance of deathstarbench is not stable, we run it for multiple times and store the results previously 
    # benchmarks = ['deathstarbench']

    # TPP use another kernel, we store the results previously as well
    # methods = ['TPP']

    for bench in benchmarks:
        for method in methods:
            
            if bench in ['deathstarbench']:
                for i in range(5):
                    print(f"Running {bench} with {method}, trial {i+1} of 5")
                    os.system(f"python3 run_benchmark.py --config ./method_config/{method}.json --benchmark {bench} --calculate_bandwidth --neomem_threshold_path ./output/neomem_threshold/{method}_{bench}_trial{i+1} > ./output/experiment_output/{method}_{bench}_trial{i+1}.txt")
                    print(f"Finished {bench} with {method}, trial {i+1} of 5")
                    time.sleep(3)
            if bench in ['pageranking']:
                for i in range(3):
                    print(f"Running {bench} with {method}, trial {i+1} of 3")
                    os.system(f"python3 run_benchmark.py --config ./method_config/{method}.json --benchmark {bench} --calculate_bandwidth --neomem_threshold_path ./output/neomem_threshold/{method}_{bench}_trial{i+1} > ./output/experiment_output/{method}_{bench}_trial{i+1}.txt")
                    print(f"Finished {bench} with {method}, trial {i+1} of 3")
                    time.sleep(3)
            else:
                for i in range(1):
                    print(f"Running {bench} with {method}, trial {i+1} of 1")
                    os.system(f"python3 run_benchmark.py --config ./method_config/{method}.json --benchmark {bench} --calculate_bandwidth --neomem_threshold_path ./output/neomem_threshold/{method}_{bench}_trial{i+1} > ./output/experiment_output/{method}_{bench}_trial{i+1}.txt")
                    print(f"Finished {bench} with {method}, trial {i+1} of 1")
                    time.sleep(3)

            
