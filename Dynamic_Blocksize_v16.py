import bisect

# Initialization
T_R = 3000 # reference transaction weight for fee
Z_M = 300000 # Guaranteed penalty free zone
M_B = 100000 # Block weight in bytes
M_L = 300000 # Effective Long term median, 100k blocks
M_L_weight = 0 # M_L_weight to enter in M_L_list
M_L_prev = 300000 # Previously effective long term median for last block
M_S = 100000 # Effective short term median, 100 blocks
M_N = 300000 # Median for Penalty calculation
R_Base = 0.6 # Block Reward
M_B_max = 600000 # Maximum permitted size for next block
M_L_list = [300000]*100000 #list of 100000 previous M_L values
M_S_list = [100000]*100 #list of 100 previous M_S values
mempool = 0 # Size of unconfirmed transactions, bytes

#Data for plotting
M_L_archive = [] # Long term median archive
M_L_weight_archive = [] # Long term weight archive
M_S_archive = [] # Short term median archive
M_B_archive = [] # Block weight archive
M_N_archive = [] # Penalty median archive
mempool_archive = [] # mempool archive
P_archive = [] # Penalty archive
F_T_archive = [] # Additional fee to overcome penalty increase archive
f_I_archive = [] # Minimum fee per byte archive

#Median calculation speedup
sorted_M_L_list = sorted(M_L_list)
M_L_mid = len(M_L_list) // 2
sorted_M_S_list = sorted(M_S_list)
M_S_mid = len(M_S_list) // 2


# Process n blocks
n= 500000
for i in range(n):
    
    # Median calculations
    M_L_from_list = (sorted_M_L_list[M_L_mid] + sorted_M_L_list[~M_L_mid]) / 2 # Median of list of long term weights
    M_L = max(300000, M_L_from_list) # Force M_L into valid range
    M_L_weight = max(min(M_B, 1.7 * M_L_prev), 300000, M_L_prev / 1.7) # Long term block weight
    M_L_prev = M_L # Store M_L for next M_L_weight calculation
    M_S = (sorted_M_S_list[M_S_mid] + sorted_M_S_list[~M_S_mid]) / 2 # Median of list of short term weights
    M_N = max(300000,min(max(300000, M_S), 50 * M_L)) # Median for Penalty calculation
    
    # Penalty calculation
    B = (M_B / M_N) - 1
    P_B = R_Base * B**2
    if B <= 0:
        P_B = 0
    
    # Fee Calculations
    B_T = T_R / M_N # Increase from adding additional transaction to block, using T_R as placeholder
    F_T = R_Base * (2 * B * B_T + B_T**2) # Additional fee required to overcome the increase in penalty, F_T = P_T
    if B + B_T <= 0:
        F_T = 0
    f_I = 0.95 * R_Base * T_R / (M_L**2) # Minimum fee per byte, M_F = M_L
    
    # Prepare values for next block
    M_B_max = 2 * M_N # Maximum weight of next block
    
    #Simulate tx ramp
    mempool += 1000 * i # Add newly broadcast tx bytes to mempool
    if i > 350000:
        mempool = 100000
    
    M_B = min(M_B_max, mempool) # Calculate size of next block
    # Calculate size of mempool
    if M_B == mempool: # If M_B includes entire mempool
        mempool = 0 # mempool is now empty
    else:
        mempool -= M_B # remove M_B from mempool
    
    # Update Long Term Median Lists
    sorted_M_L_list.pop(bisect.bisect_left(sorted_M_L_list, M_L_list[0])) # Remove oldest M_L value from sorted_M_L_list
    M_L_list.pop(0) # Remove oldest M_L value from M_L_list
    M_L_list.append(M_L_weight) # Append newest M_L value to M_L_list
    bisect.insort(sorted_M_L_list, M_L_weight) # Insert newest M_L value into correct index of sorted_M_L_list
    
    # Update Short Term Median Lists
    sorted_M_S_list.pop(bisect.bisect_left(sorted_M_S_list, M_S_list[0])) # Remove oldest M_B value from sorted_M_S_list
    M_S_list.pop(0) # Remove oldest M_B value from M_S_list
    M_S_list.append(M_B) # Append newest M_B value to M_S_list
    bisect.insort(sorted_M_S_list, M_B) # Insert newest M_B value into correct index of sorted_M_S_list
    
    # Store data for plotting
    M_L_archive.append(M_L) # Long term median archive
    M_L_weight_archive.append(M_L_weight) # Long term weight archive
    M_S_archive.append(M_S) # Short term median archive
    M_B_archive.append(M_B) # Block weight archive
    M_N_archive.append(M_N) # Penalty median archive
    mempool_archive.append(mempool)
    P_archive.append(P_B) # Penalty archive
    F_T_archive.append(F_T) # Additional fee to overcome penalty increase archive
    f_I_archive.append(f_I) # Minimum fee per byte archive
    
    if i % 10000 == 0: print('Running iteration ', i)
