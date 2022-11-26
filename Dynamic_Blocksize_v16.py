import bisect

# Initialization
n = 500000 # Number of blocks to simulate
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

# Function for controlling tx input to model
def tx_input(): 
    global selection
    if i == 0:
        print("Welcome! This is a Monero dynamic block size simulator. You have some options...")
        print("1. Linear Transaction Ramp")
        print("2. Parabolic Transaction Ramp")
        print("3. Exponential Transaction Ramp")
        print("4. Maximum flood")
        selection = input("Type the number for your selection and press enter: ")
    if selection == '1': controlled_input = 100000 + 1000 * i # Linear Ramp
    if selection == '2': controlled_input = (1000+(i/15))**2 # Parabolic Ramp
    if selection == '3': controlled_input = 300000*(1.6**(9.7 + (i / 50000))) # Exponential Ramp
    if selection == '4': controlled_input = M_B_max # Maximum tx flood
    return controlled_input

for i in range(n): # Process n blocks
    
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
    if B <= 0: P_B = 0 # P_B calculation only nonzero for B > 0
    
    # Fee Calculations
    T_T = T_R # tx size for F_T calculation, using reference tx size for demonstration
    B_F_T = B # B value used to calculate F_T
    if M_N - T_T < M_B < M_N: # If only a part of T_T is in penalty zone
        T_T = T_T - (M_N - M_B) # consider only portion of tx in penalty zone
        B_F_T = 0 # set (B value used to calculate F_T) = 0
    B_T = T_T / M_N # Increase from adding additional transaction to block
    F_T = R_Base * (2 * B_F_T * B_T + B_T**2) # Additional fee required to overcome the increase in penalty, F_T = P_T
    if B_F_T + B_T <= 0: F_T = 0 # calculated F_T only valid for B + B_T > 0
    f_I = 0.95 * R_Base * T_R / (M_L**2) # Minimum fee per byte, M_F = M_L
    
    # Prepare values for next block
    M_B_max = 2 * M_N # Maximum weight of next block
    mempool += tx_input() # Add newly broadcast tx bytes to mempool
    M_B = min(M_B_max, mempool) # Calculate size of next block
    
    # Calculate size of mempool
    if M_B == mempool: mempool = 0 # if mempool fully emptied into block it is zero
    else: mempool -= M_B # else subtract block bytes from mempool
    
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
    
    if i % 10000 == 0: print('Running iteration ', i) # Print running status
