# Simulation of transaction ramp
# This is a work in progress. Use at your own peril.

# NOTE: R implementation gives slightly different results from Python


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
M_L_list = rep(300000, 100000) #list of 100000 previous M_L values
M_S_list = rep(100000, 100) #list of 100 previous M_S values
mempool = 0 # Size of unconfirmed transactions, bytes
newly_broadcast_tx_bytes = 0 #newly broadcasted transaction bytes
n=300000 # Number of blocks to simulate

#Data for plotting
M_L_archive = vector("numeric", n) # Long term median archive
M_L_weight_archive = vector("numeric", n) # Long term weight archive
M_S_archive = vector("numeric", n) # Short term median archive
M_B_archive = vector("numeric", n) # Block weight archive
M_N_archive = vector("numeric", n) # Penalty median archive
mempool_archive = vector("numeric", n) # mempool archive
P_archive = vector("numeric", n) # Penalty archive
f_I_archive = vector("numeric", n) # Minimum fee per byte archive


# Process n blocks
for (i in seq_len(n)) {
  
  # Median calculations
  M_L_from_list = median(M_L_list) # Median of list of long term weights
  M_L = max(c(300000, M_L_from_list)) # Force M_L into valid range
  M_L_weight = max(c(
    min(c(M_B, 1.7 * M_L_prev)), 
    300000, 
    M_L_prev / 1.7)) # Long term block weight
  M_L_prev = M_L # Store M_L for next M_L_weight calculation
  M_S = median(M_S_list) # Median of list of short term weights
  M_N = max(c(
    300000,
    min(c(max(c(300000, M_S)), 50 * M_L)))) # Median for Penalty calculation
  
  # Penalty calculation
  B = (M_B / M_N) - 1
  P_B = R_Base * B**2
  if ( B <= 0 ) {
    P_B = 0
  }
   
  # Fee Calculations
  f_I = 0.95 * R_Base * T_R / (M_L**2) # Minimum fee per byte, M_F = M_L
  
  # Prepare values for next block
  M_B_max = 2 * M_N # Maximum weight of next block
  
  #Simulate tx ramp
  newly_broadcast_tx_bytes = newly_broadcast_tx_bytes + 1000
  mempool = mempool + newly_broadcast_tx_bytes # Add newly broadcast tx bytes to mempool
  #if ( i > 500000) {
  #  mempool = 0
  #}
  
  M_B = min(c(M_B_max, mempool)) # Calculate size of next block
  # Calculate size of mempool
  if ( M_B == mempool ) { # If M_B includes entire mempool
    mempool = 0 # mempool is now empty
  } else {
    mempool = mempool - M_B # remove M_B from mempool
  }
    
  # Update Long Term Median Lists
  M_L_list <- c(M_L_list[-1], M_L_weight) # Remove oldest entry, and add current M_L
  
  # Update Short Term Median Lists
  M_S_list <- c(M_S_list[-1], M_B) # Remove oldest entry, and add current M_S
  
  # Store data for plotting
  M_L_archive[i] <- M_L # Long term median archive
  M_L_weight_archive[i] <- M_L_weight # Long term weight archive
  M_S_archive[i] <- M_S # Short term median archive
  M_B_archive[i] <- M_B # Block weight archive
  M_N_archive[i] <- M_N # Penalty median archive
  mempool_archive[i] <- mempool
  P_archive[i] <- P_B # Penalty archive
  f_I_archive[i] <- f_I # Minimum fee per byte archive
  
  if ( i %% 10000 == 0) {
    print(paste0('Running iteration ', i))
  } 
}

png("Plots/R/M_L_archive-R.png")
plot(M_L_archive, type = "l")
dev.off()

png("Plots/R/M_L_weight_archive-R.png")
plot(M_L_weight_archive, type = "l")
dev.off()

png("Plots/R/M_S_archive-R.png")
plot(M_S_archive, type = "l")
dev.off()

png("Plots/R/M_B_archive-R.png")
plot(M_B_archive, type = "l")
dev.off()

png("Plots/R/M_N_archive-R.png")
plot(M_N_archive, type = "l")
dev.off()

png("Plots/R/mempool_archive-R.png")
plot(mempool_archive, type = "l")
dev.off()

png("Plots/R/P_archive-R.png")
plot(P_archive, type = "l")
dev.off()

png("Plots/R/f_I_archive-R.png")
plot(f_I_archive, type = "l")
dev.off()
