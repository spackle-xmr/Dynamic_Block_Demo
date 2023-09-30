# This is a work in progress. Use at your own peril.

import math
import bisect
import matplotlib.pyplot as plt
import matplotlib.animation as animation
import numpy as np

# CONFIGURATION
RUN_TYPE = 6 # 1 = Linear Transaction Ramp, 2 = Fast Linear Transaction Ramp, 3 = Fast Parabolic Transaction Ramp, 
# 4 = Fast Exponential Transaction Ramp, 5 = Maximum flood, 6 = Configurable Transaction Ramp To Sine
ADD_NOISE = 0 # Select whether to add noise to tx broadcast
USERS_PAY_MORE = 0 # Select whether users respond to congestion by paying higher fees
WALLET_CALC = 0 # Select whether to perform Wallet calculations. MUCH SLOWER
PLOT_RESULT = 0 # Select whether to create plots/animations

# Initialization
n = 30000 # Number of blocks to simulate
T_sim = 800 # tx size discretization step. 800 means tx can be 800, 1600, 2400... bytes. (must be <=900 to display min fee block expansion)
B = 0 
F_T = 0 # Additional fee to overcome penalty increase
T_R = 3000 # Reference tx weight for fee
Z_M = 300000 # Guaranteed penalty free zone
M_B = 100000 # Block weight in bytes
M_L = 300000 # Effective Long term median, 100k blocks
M_L_weight = 0 # M_L_weight to enter in M_L_list
M_L_prev = 300000 # Previously effective long term median for last block
M_S = 300000 # Effective short term median, 100 blocks
M_S_weight = 0 # M_S_weight to enter in M_S_list
M_N = 300000 # Median for Penalty calculation
R_Base = 0.6 # Block Reward
M_B_max = 600000 # Maximum permitted size for next block
M_L_list = [300000]*100000 # List of 100000 previous M_L values
sorted_M_L_list = sorted(M_L_list) # Sorted list of M_L values, used for median calc
M_S_list = [300000]*100 # List of 100 previous M_S values
sorted_M_S_list = sorted(M_S_list) # Sorted list of M_S values, used for median calc
mid_100k = 50000 # Middle index for size 100k lists, used for median calc
mid_100 = 50 # Middle index for size 100 lists, used for median calc

# Assume all tx are size T_sim. Each list index is a certain fee level, the value of each index is the number of tx
# Highest fees are lowest index, lowest fees are highest index
broadcast = [0]*2 # Newly broadcast tx data
mempool = [0]*2 # List of unconfirmed tx
fees = [0]*2 # fees paid at each level of mempool
block_fee_total = 0 # total fee paid to create block
blockfilled = [0]*2 # tx in mempool that failed to pay enough fees
fee_set = [] # Calculated fee amount that must be paid to add each tx to a block.
percent_response = 0

# Initialize Wallet Fee Lists
M_LW_prev = 300000 # Previously effective long term wallet fee median
M_BW_list =[100000]*99990 # List of 99990 previous M_BW values
M_BW_list.extend([0] * 10) # Add 10x 0 entries
sorted_M_BW_list = sorted(M_BW_list) # Sorted list of 100k M_BW values
M_LW_list = M_L_list[10:] # Remove 10 oldest entries from M_L_list
M_LW_list.extend([0] * 10) # Add 10x 0 entries
sorted_M_LW_list = sorted(M_LW_list) # Sorted list of M_LW values
M_SW_list = M_S_list[10:] # List of 90 previous M_SW values
M_SW_list.extend([0] * 10) # Add 10x 0 entries
sorted_M_SW_list = sorted(M_SW_list) # Sorted list of 100 M_SW values

#Data for plotting
M_L_archive = [] # Long term median archive
M_L_weight_archive = [] # Long term weight archive
M_S_archive = [] # Short term median archive
M_S_weight_archive = [] # Short term weight archive
M_B_archive = [] # Block weight archive
M_N_archive = [] # Penalty median archive
broadcast_archive = [[0,0] for i in range(n)] # broadcast archive
mempool_archive = [[0,0] for i in range(n)] # Mempool archive
blockfilled_archive = [[0,0] for i in range(n)] # blockfilled archive
fee_sum_archive = []
P_archive = [] # Penalty archive
Block_fee_archive = [] # Fees paid by tx included in block archive
F_T_archive = [] # Fee needed to add another tx to block archive
f_I_archive = [] # Minimum fee per byte archive
input_volume_archive = [] # Broadcast tx volume archive (not split into fee levels)


for i in range(n): # Process n blocks
    
    # Median calculations
    M_L = (sorted_M_L_list[mid_100k] + sorted_M_L_list[~mid_100k]) / 2 # Median of list of long term weights
    M_L_weight = max(min(M_B, 1.7 * M_L_prev), Z_M, M_L_prev / 1.7) # Long term block weight
    M_S = (sorted_M_S_list[mid_100] + sorted_M_S_list[~mid_100]) / 2 # Median of list of short term weights
    M_S_weight = max(M_B, M_L) # Short term block weight
    M_N = min(M_S, 50 * M_L) # Median for penalty calculation
    
    M_B_max = 2 * M_N # Maximum weight of next block
    f_I = 0.95 * R_Base * T_R / (M_L**2) # Minimum fee per byte, M_F = M_L
    
    # Define fees paid for each tx fee level
    fees[1] = f_I * T_sim # lowest fee
    fees[0] = 16 * fees[1] # medium fee
    
    # Broadcast new tx
    blockfilled[0] = 0  # Clear the record of tx which filled the last block
    blockfilled[1] = 0
    broadcast[0] = 0 # Clear the record of previously broadcast tx
    broadcast[1] = 0
    
    if RUN_TYPE == 1: broadcast[1] = (300000 + 100 * i) // T_sim  #Linear Ramp
    if RUN_TYPE == 2: broadcast[1] = (300000 + 10 * i) // T_sim  # Fast Linear Ramp starting at 100k
    if RUN_TYPE == 3: broadcast[1] = ((316 + (i / 15))**2) // T_sim # Fast Parabolic Ramp starting at 100k
    if RUN_TYPE == 4: broadcast[1] = (300000 * (1.6**(9.8 + (i / 50000)) - 99.75)) // T_sim  # Fast Exponential Ramp starting at 100k
    if RUN_TYPE == 5: broadcast[1] = M_B_max // T_sim  # Maximum tx flood
    if RUN_TYPE == 6: 
        start_val = 300000 # Starting tx volume
        ramp_multiplier = 3 # Ending tv volume / starting tx volume
        ramp_delay = 10 # Wait to start ramping
        ramp_days = 14
        ramp_time = ramp_days*720 # Time for ramp to occur
        if i <= ramp_delay: broadcast[1] = start_val // T_sim #start with 100kB blocks for the first 100 blocks 
        if ramp_delay < i <= ramp_delay + ramp_time: #Ramp from 100kB to 1MB blocks over 720 blocks
            broadcast[1] = (start_val + math.floor((ramp_multiplier - 1)*start_val/ramp_time) * (i - ramp_delay)) // T_sim # Define total broadcast data volume during ramp
        if i > ramp_delay + ramp_time: 
            broadcast[1] = ramp_multiplier * start_val // T_sim  + 220 * np.sin(i/802) # Ramp finished, broadcast variable blocks around new size
    input_volume_archive.append(broadcast[1])
    
    if ADD_NOISE == 1:
        noise = 0.2 * np.random.normal(0,broadcast[1],1)
        broadcast[1] += int(noise)
        if broadcast[1] <= 0: broadcast[1] = 1
    
    if USERS_PAY_MORE == 1:
        # Check broadcast volume against mempool size. If mempool is already large, have broadcast tx pay higher fees
        #Control the fee level response
        previous_percent_response = percent_response
        percent_response_calc = math.floor((mempool[1] / (3 * broadcast[1])) * 100)
        percent_response = math.floor(previous_percent_response + 0.1 * (percent_response_calc-previous_percent_response))
        
        # if percent_response == 0: # Do nothing
        if percent_response > 100: percent_response = 100 # high fees only
        if 0 < percent_response <= 100: # Mark some tx with higher fee
            broadcast[0] = ((broadcast[1] * percent_response) // 100)
            broadcast[1] = (broadcast[1] * (100 - percent_response)) // 100
    
    # Update mempool with broadcast
    for j in range(len(mempool)):
        mempool[j] += broadcast[j]
        
    # Build next block
    M_B = 0 # Begin building from empty block
    block_fee_total = 0 
    fee_set.clear()
    break_flag = 0
    
    for k in range(len(mempool)): # for all fee levels
        if break_flag == 1: break # Nested break condition triggered
        for l in range(int(mempool[k])): # for all tx at a given fee level, check if fees justify adding tx to block and respond accordingly
            
            # Check if we are allowed to grow the block. If not, stop adding tx to block
            if M_B >= M_B_max:
                blockfilled[0] = k # save fee failure
                blockfilled[1] = l # save tx number failure
                break_flag = 1
                break
        
            M_B += T_sim # Add tx size to block
            
            # Check necessary fees to expand block to new size
            B = (M_B / M_N) - 1 # B can be thought of as % increase in block weight
            T_T = T_sim # Tx size for F_T calculation
            B_F_T = B # B value used to calculate F_T
            if M_N - T_T < M_B < M_N: # If only a part of T_T is in penalty zone
                T_T = T_T - (M_N - M_B) # Consider only portion of tx in penalty zone
                B_F_T = 0 # Set (B value used to calculate F_T) = 0
            B_T = T_T / M_N # Increase from adding additional tx to block
            F_T = R_Base * (2 * B_F_T * B_T + B_T**2) # Additional fee required to overcome the increase in penalty, F_T = P_T
            if B_F_T + B_T <= 0: 
                F_T = 0 # Calculated F_T only valid for B + B_T > 0
            
            # Load cheapest fee set with the cheapest fees possible for each tx
            fee_set.append(F_T)
            
            if fees[k] < F_T: # If not enough fees paid
                M_B -= T_T # Remove proposed tx from block
                blockfilled[0] = k # save fee failure
                blockfilled[1] = l # save tx number failure
                break_flag = 1
                break
    
    if all(num == 0 for num in blockfilled):
        if mempool[1] != 0:
            blockfilled[0] = 1
            blockfilled[1] = mempool[1]
        elif mempool [0] != 0:
            blockfilled[0] = 0
            blockfilled[1] = mempool[0]
    
    # Calculate fees paid to create block
    for k in range(blockfilled[0]):
        block_fee_total += mempool[k] * fees[k]
    block_fee_total += (blockfilled[1] - 1) * fees[blockfilled[0]]

    # Remove included tx from mempool
    for k in range(blockfilled[0]):
        mempool[k] = 0
    mempool[blockfilled[0]] -= blockfilled[1]
    
    # Penalty calculation for entire block
    B = (M_B / M_N) - 1 # B can be thought of as % increase in block weight
    P_B = R_Base * B**2 # Calculate Penalty value
    if B <= 0: P_B = 0 # Penalty calculation only valid for B > 0
    
    # Update Long Term Median Lists
    sorted_M_L_list.pop(bisect.bisect_left(sorted_M_L_list, M_L_list[0])) # Remove oldest M_L value from sorted_M_L_list
    M_L_list.pop(0) # Remove oldest M_L value from M_L_list
    M_L_list.append(M_L_weight) # Append newest M_L value to M_L_list
    bisect.insort(sorted_M_L_list, M_L_weight) # Insert newest M_L value into correct index of sorted_M_L_list
    
    # Update Short Term Median Lists
    sorted_M_S_list.pop(bisect.bisect_left(sorted_M_S_list, M_S_list[0])) # Remove oldest M_B value from sorted_M_S_list
    M_S_list.pop(0) # Remove oldest M_B value from M_S_list
    M_S_list.append(M_S_weight) # Append newest M_S value to M_S_list
    bisect.insort(sorted_M_S_list, M_S_weight) # Insert newest M_S value into correct index of sorted_M_S_list
    
    # Perform wallet calculations, if desired
    if WALLET_CALC == 1:
        # Wallet Fee Medians
        M_BW = (sorted_M_BW_list[mid_100k] + sorted_M_BW_list[~mid_100k]) / 2 # Median of list of wallet blocks
        M_LW = (sorted_M_LW_list[mid_100k] + sorted_M_LW_list[~mid_100k]) / 2 # Median of list of long term wallet weights
        M_LW_weight = max((min(M_BW, 1.7 * M_LW_prev), Z_M, M_LW_prev / 1.7)) # Long term wallet block weight
        M_SW = (sorted_M_SW_list[mid_100] + sorted_M_SW_list[~mid_100]) / 2 # Median of list of short term weights
        M_SW_weight = max(M_BW, M_LW) # Short term wallet block weight
        M_NW = min(M_SW, 50 * M_LW) # Median for wallet fee penalty calculation
        
        # Wallet Fee Calculations
        B_RLW = T_R / M_LW # Used for low and normal fees, M_FW = M_LW
        B_R = T_R / Z_M # Used for medium and high fees
        F_L = R_Base * B_RLW**2 # Low tx fee for reference tx
        f_L = R_Base * B_RLW / M_LW # Low tx fee per byte for a given M_LW
        f_N = 4 * f_L # Normal tx fee per byte for a given M_LW
        f_M = 16 * R_Base * B_R / M_LW  # Medium tx fee per byte for a given M_LW
        f_P = 2 * R_Base / M_NW # Maximum penalty (B = 1) tx fee per byte for a given M_NW
        f_H = 4 * f_M * max(1, M_LW / (32 * B_R * M_NW)) # High tx fee per byte
        
        # Update Wallet Fee Median Lists
        sorted_M_BW_list.pop(bisect.bisect_left(sorted_M_BW_list, M_BW_list[0])) # Remove oldest M_BW value from sorted_M_BW_list
        M_BW_list.pop(0) # Remove oldest M_BW value from M_BW_list
        M_BW_list.insert(100000 - 11, M_B) # Append newest M_B value to M_BW_list before 0s
        bisect.insort(sorted_M_BW_list, M_B) # Insert newest M_B value into correct index of sorted_M_BW_list
        sorted_M_LW_list.pop(bisect.bisect_left(sorted_M_LW_list, M_LW_list[0])) # Remove oldest M_LW value from sorted_M_LW_list
        M_LW_list.pop(0) # Remove oldest M_LW value from M_LW_list
        M_LW_list.insert(100000 - 11, M_LW_weight) # Append newest M_LW value to M_LW_list
        bisect.insort(sorted_M_LW_list, M_LW_weight) # Insert newest M_LW value into correct index of sorted_M_LW_list
        sorted_M_SW_list.pop(bisect.bisect_left(sorted_M_SW_list, M_SW_list[0])) # Remove oldest M_SW value from sorted_M_SW_list
        M_SW_list.pop(0) # Remove oldest M_SW value from M_SW_list
        M_SW_list.insert(100 - 11, M_SW_weight) # Append newest M_SW value to M_SW_list before 0s
        bisect.insort(sorted_M_SW_list, M_SW_weight) # Insert newest M_SW value into correct index of sorted_M_SW_list
    
    # Store M_L for calculation in next block
    M_L_prev = M_L # Store M_L for next M_L_weight calculation
    
    # Store data for plotting
    M_L_archive.append(M_L) # Long term median archive
    M_L_weight_archive.append(M_L_weight) # Long term weight archive
    M_S_archive.append(M_S) # Short term median archive
    M_S_weight_archive.append(M_S_weight) # Short term weight archive
    M_B_archive.append(M_B) # Block weight archive
    M_N_archive.append(M_N) # Penalty median archive
    for item in range(len(mempool)):
        mempool_archive[i][item] = mempool[item]
        broadcast_archive[i][item] = broadcast[item] # broadcast archive
        blockfilled_archive[i][item] = blockfilled[item]
    fee_sum_archive.append(sum(fee_set))
    F_T_archive.append(F_T)
    P_archive.append(P_B) # Penalty archive
    Block_fee_archive.append(block_fee_total) # Additional fee to overcome penalty increase archive
    f_I_archive.append(f_I) # Minimum fee per byte archive
    
    if i % 10000 == 0: print('Running iteration ', i) # Print running status

if PLOT_RESULT == 1:
    
    multival = 10 # Points per frame, allows faster plotting.
    
    x = list(range(n)) # List counting up to number of simulated blocks
    fig, ((ax0, ax1), (ax2, ax3)) = plt.subplots(2,2) # Figure with two subplots
    fig.suptitle('Dynamic Block Demonstration')
    ax1.set(ylabel="Block Size")
    ax0.set(ylabel="Transactions Broadcast to Network")
    ax2.set(xlabel="Block", ylabel="Total fees per block")
    ax3.set(xlabel="Block", ylabel="Penalty")
    
    ax0.yaxis.label.set_size(20)
    ax1.yaxis.label.set_size(20)
    ax2.yaxis.label.set_size(20)
    ax3.yaxis.label.set_size(20)
    ax2.xaxis.label.set_size(20)
    ax3.xaxis.label.set_size(20)
    
    line0, = ax0.plot([], [], lw=2, color='g')
    line1, = ax1.plot([], [], lw=2, color='c')
    line2, = ax2.plot([], [], lw=2, color='b')
    line3, = ax3.plot([], [], lw=2, color='r')
    line = [line0, line1, line2, line3]
    ax1.set_ylim(0, 1.1 * max(M_B_archive)) # Block Size
    ax1.set_xlim(0, n)
    ax1.grid()
    ax0.set_ylim(0, 1.1 * max(input_volume_archive)) # Transaction Volume
    ax0.set_xlim(0, n)
    ax0.grid()
    ax2.set_ylim(0, 1.1 * max(Block_fee_archive)) # Total fees paid for block
    ax2.set_xlim(0, n)
    ax2.grid()
    ax3.set_ylim(0, 1.1 * max(P_archive)) # Penalty
    ax3.set_xlim(0, n)
    ax3.grid()
    
    
    def animate(i):
        
        global multival
        # plotting speed
        for ax in [ax0, ax1, ax2, ax3]:
            xmin, xmax = ax.get_xlim()
            ymin, ymax = ax.get_ylim()

        # Update lines
        line[1].set_data(x[:i*multival], M_B_archive[:i*multival])   
        line[0].set_data(x[:i*multival], input_volume_archive[:i*multival])  
        line[2].set_data(x[:i*multival], Block_fee_archive[:i*multival])  
        line[3].set_data(x[:i*multival], P_archive[:i*multival])
        return line,

    ani = animation.FuncAnimation(fig, animate, interval=12, repeat=False, save_count = 500)
    plt.tight_layout() # Plot padding
    
    
    plt.show()
    plt.pause(15)
    plt.close()
    
    #f = r"C:\Users\XXXX\Desktop\animation_v4.gif" 
    #writergif = animation.PillowWriter(fps=30) 
    #ani.save(f, writer=writergif)
