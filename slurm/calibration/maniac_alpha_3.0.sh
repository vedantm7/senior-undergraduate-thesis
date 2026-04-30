#!/bin/bash
#SBATCH --partition=short
#SBATCH --nodes=1
#SBATCH --cpus-per-task=48
#SBATCH --mem=200G
#SBATCH --time=2-00:00:00
#SBATCH --job-name=fresh_ma_3.0
#SBATCH --output=/home/mundhra.ve/poker_thesis/calibration/maniac/fresh_3.0/job.log
#SBATCH --error=/home/mundhra.ve/poker_thesis/calibration/maniac/fresh_3.0/job.err
#SBATCH --mail-type=END,FAIL
#SBATCH --mail-user=mundhra.ve@northeastern.edu
export LD_LIBRARY_PATH=/shared/centos7/boost/1.80.0/lib:$LD_LIBRARY_PATH
/home/mundhra.ve/poker_thesis/open-pure-cfr-buckets/pure_cfr \
    /home/mundhra.ve/poker_thesis/poker-cfrm/games/holdem.limit.2p.36_36.game \
    /home/mundhra.ve/poker_thesis/calibration/maniac/fresh_3.0/strategy \
    --card-abs=FILE:/home/mundhra.ve/poker_thesis/holdem_100b_cfrm.abs \
    --threads=48 \
    --checkpoint=3600 \
    --max-walltime=01:23:00:00 \
    --config=/home/mundhra.ve/poker_thesis/calibration/maniac/fresh_3.0/params.conf
