import os

def set_state_monitor():
    print("set neomem parameters")
    print("migration_interval: ", 100000, "us")
    print("clear_interval: ", 1, "iteration")
    print("threshold: ", 1000000, "accesses")
    # os.system(f"echo 100000 > /sys/kernel/mm/neomem/migration_interval")
    # os.system(f"echo 1 > /sys/kernel/mm/neomem/clear_interval")
    # os.system(f"echo 1000000 > /sys/kernel/mm/neomem/hot_threshold")
    # os.system("echo 1 > /sys/kernel/mm/neomem/neomem_enabled")
    # os.system("echo Y > /sys/kernel/mm/neomem/debug")