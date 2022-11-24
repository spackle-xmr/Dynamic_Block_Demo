# Simulation of transaction ramp
# This is a work in progress. Use at your own peril.

# NOTE: R implementation gives slightly different results from Python


# Initialization
B = 0.6 #base block reward
block_weight = 100000 #first new block_weight for running simulation
TW_ref = 3000 #reference transaction weight for fee
cumulative_median_ref = 300000 #reference median for fee.
blocks_longterm_weights = rep(300000, 100000) #list of 100000 previous block longterm weights
hundred_blocks_weights = rep(100000, 100) #list of 100 previous block weights (normal weights, not longterm weights)
previous_effective_longterm_median = 300000
n = 500000 #number of blocks to simulate
newly_broadcast_tx_bytes = 100000 #newly broadcasted transaction bytes
mempool_unconfirmed = 0 # size of mempool bytes

#Data for plotting
longterm_median_archive= vector("numeric", n)
longterm_weights_archive= vector("numeric", n)
block_weights_archive= vector("numeric", n)
f_min_actual_archive= vector("numeric", n)
penalty_archive= vector("numeric", n)
mempool_unconfirmed_archive= vector("numeric", n)
max_next_block_weight_archive= vector("numeric", n)

#Median Calc speedup
sorted_blocks_longterm_weights= sort(blocks_longterm_weights)
longterm_mid= floor(length(blocks_longterm_weights) / 2)
sorted_hundred_blocks_weights= sort(hundred_blocks_weights)
weights_mid= floor(length(hundred_blocks_weights) / 2)
#End Initialization


bisect.insort <- function(a, x) {
  insertion.point <- findInterval(x, a, rightmost.closed = TRUE)
  append(x = a, values = x, after = insertion.point)
}


#Iterate n blocks
for (i in seq_len(n)) {
  
  #Process Current Block
  
  #Calculate Medians
  median_100000blocks_longterm_weights= median(sorted_blocks_longterm_weights) #Median calculation for longterm weight
  median_100_blocks_weights= median(sorted_hundred_blocks_weights) #Median calculation for shortterm weight
  
  effective_longterm_median= max(c(300000, median_100000blocks_longterm_weights)) # effective longterm median for current block
  
  #longterm_block_weight= min(block_weight, 1.4 * previous_effective_longterm_median) #longterm block weight
  longterm_block_weight= max(c(
    min(c(block_weight, 1.7 * previous_effective_longterm_median)),
    300000,
    previous_effective_longterm_median / 1.7)) #v16
  
  cumulative_weights_median= max(c(
    300000,
    min(c(max(c(300000, median_100_blocks_weights)), 50 * effective_longterm_median)))) #cumulative weights median
  
  max_next_block_weight = 2 * cumulative_weights_median # maximum weight of next block
  
  
  P= B * ((block_weight/cumulative_weights_median)-1)**2 #Block Reward Penalty
  if ( (block_weight/cumulative_weights_median)-1 <= 0 ) {
    P = 0
  }
  
  smallest_median= max(c(300000,min(c(median_100_blocks_weights, effective_longterm_median))))
  
  f_min_actual = 0.95 * B * TW_ref / (effective_longterm_median**2) # Minimum fee per byte v16
  
  previous_effective_longterm_median= effective_longterm_median #Store current effective longterm median
  
  #Update longterm weights
  remove_item= findInterval(blocks_longterm_weights[1], sorted_blocks_longterm_weights, rightmost.closed = TRUE)
  sorted_blocks_longterm_weights <- sorted_blocks_longterm_weights[(-1) * remove_item]
  blocks_longterm_weights <- c(blocks_longterm_weights[-1], longterm_block_weight)
  sorted_blocks_longterm_weights <- bisect.insort(sorted_blocks_longterm_weights, longterm_block_weight)
  
  
  #Update block weights
  remove_item= findInterval(hundred_blocks_weights[1], sorted_hundred_blocks_weights, rightmost.closed = TRUE)
  sorted_hundred_blocks_weights <- sorted_hundred_blocks_weights[(-1) * remove_item]
  hundred_blocks_weights <- c(hundred_blocks_weights[-1], block_weight)
  sorted_hundred_blocks_weights <- bisect.insort(sorted_hundred_blocks_weights, block_weight)
  
  
  #Prepare values for next block
  
  
  #TX LINEAR RAMP
  if (i < 300000) {
    newly_broadcast_tx_bytes = newly_broadcast_tx_bytes + 1000
  } else {
    newly_broadcast_tx_bytes = 300000
  }
  
  
  #TX FLOOD
  # newly_broadcast_tx_bytes = max_next_block_weight # uncomment for max size blocks
  
  
  #TX PARABOLIC RAMP
  # if i < 350000:
  #  newly_broadcast_tx_bytes = 4.4e-3 * i**2
  # else:
  #  newly_broadcast_tx_bytes = 300000
  
  
  #add new tx to mempool
  mempool_unconfirmed = mempool_unconfirmed + newly_broadcast_tx_bytes
  
  #Calculate size of next block
  block_weight=min(c(max_next_block_weight,mempool_unconfirmed)) #guide with newly_broadcast_tx_bytes
  
  #account for bytes left out of block
  if (block_weight == mempool_unconfirmed) {
    mempool_unconfirmed = 0
  } else {
    mempool_unconfirmed = mempool_unconfirmed - max_next_block_weight
  }
  
  #Store data for plotting
  longterm_median_archive[i] <- effective_longterm_median
  longterm_weights_archive[i] <- longterm_block_weight
  block_weights_archive[i] <- block_weight
  f_min_actual_archive[i] <- f_min_actual
  penalty_archive[i] <- P
  mempool_unconfirmed_archive[i] <- mempool_unconfirmed
  max_next_block_weight_archive[i] <- max_next_block_weight
  
  
  #Print Simulation Progress
  if (i %% 10000 == 0) {
    print(paste0('Running Iteration=', i))
  }
}

png("Plots/R/longterm_median_archive-R.png")
plot(longterm_median_archive, type = "l")
dev.off()

png("Plots/R/longterm_weights_archive-R.png")
plot(longterm_weights_archive, type = "l")
dev.off()

png("Plots/R/block_weights_archive-R.png")
plot(block_weights_archive, type = "l")
dev.off()

png("Plots/R/f_min_actual_archive-R.png")
plot(f_min_actual_archive, type = "l")
dev.off()

png("Plots/R/mempool_unconfirmed_archive-R.png")
plot(mempool_unconfirmed_archive, type = "l")
dev.off()

png("Plots/R/penalty_archive-R.png")
plot(penalty_archive, type = "l")
dev.off()
 
 
