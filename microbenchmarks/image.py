import matplotlib.pyplot as plt



# with open("./result_shared/100hot/gups_neomem_100_1_2.txt", "r") as f:
#     neomem_100 = list(map(float, f.readlines()[1:200]))

# with open("./result_shared/90hot/gups_neomem_100_1_3.txt", "r") as f:
#     neomem_90 = list(map(float, f.readlines()[1:200]))

# with open("./result_shared/100hot/gups_numabalancing_1000_1000_60000_1000_256.txt", "r") as f:
#     numatiered_100 = list(map(float, f.readlines()[1:200]))

# with open("./result_shared/90hot/gups_numabalancing_1000_1000_60000_1000_256.txt", "r") as f:
#     numatiered_90 = list(map(float, f.readlines()[1:200]))

# with open("./result_shared/100hot/gups_original.txt", "r") as f:
#     local_100 = list(map(float, f.readlines()[1:200]))
    
# with open("./result_shared/90hot/gups_original.txt", "r") as f:
#     local_90 = list(map(float, f.readlines()[1:200]))
    
# with open("./result_shared/100hot/gups_baseline.txt", "r") as f:
#     baseline_100 = list(map(float, f.readlines()[1:200]))

# with open("./result_shared/90hot/gups_baseline.txt", "r") as f:
#     baseline_90 = list(map(float, f.readlines()[1:200]))
    
# with open("./result_shared/100hot/gups_abit_2_2_1.txt", "r") as f:
#     abit_100 = list(map(float, f.readlines()[1:200]))

# with open("./result_shared/90hot/gups_abit_2_2_1.txt", "r") as f:
#     abit_90 = list(map(float, f.readlines()[1:200]))


with open("./result_gups/100hot/gups_neomem.txt", "r") as f:
    neomem_100 = list(map(float, f.readlines()[1:200]))

with open("./result_gups/100hot/gups_numabalancing.txt", "r") as f:
    numatiered_100 = list(map(float, f.readlines()[1:200]))

# with open("./result_shared/100hot/gups_original.txt", "r") as f:
#     local_100 = list(map(float, f.readlines()[1:200]))
    
with open("./result_gups/100hot/gups_baseline.txt", "r") as f:
    baseline_100 = list(map(float, f.readlines()[1:200]))
    
with open("./result_gups/100hot/gups_abit.txt", "r") as f:
    abit_100 = list(map(float, f.readlines()[1:200]))
    
with open("./result_gups/100hot/gups_pebs_user.txt", "r") as f:
    pebs_100 = list(map(float, f.readlines()[1:200]))

plt.plot(neomem_100, label="neomem_100hot")
plt.plot(numatiered_100, label="numatiered_100hot")
# plt.plot(local_100, label="local_100hot")
plt.plot(baseline_100, label="baseline_100hot")
plt.plot(abit_100, label="abit_100hot")
plt.plot(pebs_100, label="pebs_100hot")

# plt.plot(neomem_90, label="neomem_90hot")
# plt.plot(numatiered_90, label="numatiered_90hot")
# plt.plot(local_90, label="local_90hot")
# plt.plot(baseline_90, label="baseline_90hot")
# plt.plot(abit_90, label="abit_90hot")

plt.legend()
plt.xlabel('second')
plt.ylabel('gups')
plt.savefig("test.png")