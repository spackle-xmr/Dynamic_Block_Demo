# This is a work in progress. Use at your own peril.

import bisect
import matplotlib.pyplot as plt
import matplotlib.animation as animation

# Initialization
n = 1000000 # Number of blocks to simulate
WALLET_CALC = 0 # Select whether to perform Wallet calculations. MUCH SLOWER
PLOT_RESULT = 0 # Select whether to create plots/animations
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
mempool = 0 # Size of unconfirmed tx, bytes

# Initialize Wallet Fee Lists
M_LW_prev = 300000 # Previously effective long term wallet fee median
M_BW_list = [100000]*99990 # List of 99990 previous M_BW values
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
mempool_archive = [] # Mempool archive
P_archive = [] # Penalty archive
F_T_archive = [] # Additional fee to overcome penalty increase archive
f_I_archive = [] # Minimum fee per byte archive


# Function for controlling tx input to model
def tx_input(): 
    global selection
    if i == 0:
        print("Welcome! This is a Monero dynamic block size simulator. You have some options...")
        print("1. Linear Transaction Ramp")
        print("2. Fast Linear Transaction Ramp")
        print("3. Fast Parabolic Transaction Ramp")
        print("4. Fast Exponential Transaction Ramp")
        print("5. Maximum flood")
        selection = input("Type the number for your selection and press enter: ")
    if selection == '1': controlled_input = 100000 + 10 * i # Linear Ramp starting at 100k
    if selection == '2': controlled_input = 100000 + 1000 * i # Fast Linear Ramp starting at 100k
    if selection == '3': controlled_input = (316 + (i / 15))**2 # Fast Parabolic Ramp starting at 100k
    if selection == '4': controlled_input = 300000 * (1.6**(9.8 + (i / 50000)) - 99.75)  # Fast Exponential Ramp starting at 100k
    if selection == '5': controlled_input = M_B_max # Maximum tx flood
    if i > 500000: controlled_input = 100000 # End of tx ramp, return to low volume
    return controlled_input


for i in range(n): # Process n blocks
    
    # Median calculations
    M_L = (sorted_M_L_list[mid_100k] + sorted_M_L_list[~mid_100k]) / 2 # Median of list of long term weights
    M_L_weight = max(min(M_B, 1.7 * M_L_prev), Z_M, M_L_prev / 1.7) # Long term block weight
    M_S = (sorted_M_S_list[mid_100] + sorted_M_S_list[~mid_100]) / 2 # Median of list of short term weights
    M_S_weight = max(M_B, M_L) # Short term block weight
    M_N = min(M_S, 50 * M_L) # Median for penalty calculation
    
    # Calculate size of next block
    M_B_max = 2 * M_N # Maximum weight of next block
    mempool += tx_input() # Add newly broadcast tx bytes to mempool
    M_B = min(M_B_max, mempool) # Calculate size of next block
    
    # Calculate size of mempool after filling next block
    if M_B == mempool: mempool = 0 # If mempool fully emptied into block it is zero
    else: mempool -= M_B # Else subtract block bytes from mempool
    
    # Penalty calculation for next block
    B = (M_B / M_N) - 1 # B can be thought of as % increase in block weight
    P_B = R_Base * B**2 # Calculate Penalty value
    if B <= 0: P_B = 0 # Penalty calculation only valid for B > 0
    
    # Fee Calculations
    T_T = T_R # Tx size for F_T calculation, using reference tx size for demonstration
    B_F_T = B # B value used to calculate F_T
    if M_N - T_T < M_B < M_N: # If only a part of T_T is in penalty zone
        T_T = T_T - (M_N - M_B) # Consider only portion of tx in penalty zone
        B_F_T = 0 # Set (B value used to calculate F_T) = 0
    B_T = T_T / M_N # Increase from adding additional tx to block
    F_T = R_Base * (2 * B_F_T * B_T + B_T**2) # Additional fee required to overcome the increase in penalty, F_T = P_T
    if B_F_T + B_T <= 0: F_T = 0 # Calculated F_T only valid for B + B_T > 0
    f_I = 0.95 * R_Base * T_R / (M_L**2) # Minimum fee per byte, M_F = M_L
    
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
    mempool_archive.append(mempool) # Mempool size archive
    P_archive.append(P_B) # Penalty archive
    F_T_archive.append(F_T) # Additional fee to overcome penalty increase archive
    f_I_archive.append(f_I) # Minimum fee per byte archive
    
    if i % 10000 == 0: print('Running iteration ', i) # Print running status

if PLOT_RESULT == 1:
    # Plotting --this is kinda rough--
    multival = 50 # Points per frame, allows faster plotting.
    multiscale = 2 # Scaling rate for multival.
    extra = 0 # Correction for multival transition
    x_adjustments = 0 # Number of times x axis has ranged
    x = list(range(n)) # List counting up to number of simulated blocks
    fig, ((ax0, ax1), (ax2, ax3)) = plt.subplots(2,2) # Figure with two subplots
    fig.suptitle('Dynamic Block Demonstration')
    ax0.set(ylabel="Block Size")
    ax1.set(ylabel="Mempool Size")
    ax2.set(xlabel="Block", ylabel="Tx Fee to Overcome Penalty")
    ax3.set(xlabel="Block", ylabel="Penalty")
    line0, = ax0.plot([], [], lw=2, color='g')
    line1, = ax1.plot([], [], lw=2, color='c')
    line2, = ax2.plot([], [], lw=2, color='b')
    line3, = ax3.plot([], [], lw=2, color='r')
    line = [line0, line1, line2, line3]
    ax0.set_ylim(0, 5e5) # Block Size
    ax0.set_xlim(0, 2000)
    ax0.grid()
    ax1.set_ylim(0, 1e7) # Mempool Size
    ax1.set_xlim(0, 2000)
    ax1.grid()
    ax2.set_ylim(0, 5e-4) # Tx Fee to Overcome Penalty
    ax2.set_xlim(0, 2000)
    ax2.grid()
    ax3.set_ylim(0,5e-2) # Penalty
    ax3.set_xlim(0, 2000)
    ax3.grid()
    
    
    def animate(i):
        global multival, extra, x_adjustments, scalecalc
        # Autorange axes and plotting speed
        for ax in [ax0, ax1, ax2, ax3]:
            xmin, xmax = ax.get_xlim()
            ymin, ymax = ax.get_ylim()
            if ax == ax0: ytest = M_B_archive[(i-extra)*multival]
            elif ax == ax1: ytest = mempool_archive[(i-extra)*multival]
            elif ax == ax2: ytest = F_T_archive[(i-extra)*multival]
            elif ax == ax3: ytest = P_archive[(i-extra)*multival]
            if x[(i-extra)*multival] >= xmax:
                ax.set_xlim(xmin, multiscale * xmax)
                ax.figure.canvas.draw()
                if ax == ax0: 
                    x_adjustments += 1
                    if x_adjustments % 2 == 0: # Every other x axis autoscale
                        multival *= multiscale # Speed up simulation
                        extra = i // multiscale  # Correct i*multival to current index. Skips around a bit, but simple.
            if ytest >= ymax:
                ax.set_ylim(ymin, 2 * ymax)
                ax.figure.canvas.draw()
        # Update lines
        line[0].set_data(x[:(i-extra)*multival] , M_B_archive[:(i-extra)*multival])   
        line[1].set_data(x[:(i-extra)*multival], mempool_archive[:(i-extra)*multival])  
        line[2].set_data(x[:(i-extra)*multival], F_T_archive[:(i-extra)*multival])  
        line[3].set_data(x[:(i-extra)*multival], P_archive[:(i-extra)*multival])
        return line,
    
    ani = animation.FuncAnimation(fig, animate, interval=1, repeat=False, save_count = 5000)
    plt.tight_layout() # Plot padding
    
    plt.show()
    plt.pause(60)
    plt.close()
    
    #f = r"C:\Users\USER\Desktop\animation_v3.gif" 
    #writergif = animation.PillowWriter(fps=30) 
    #ani.save(f, writer=writergif)
