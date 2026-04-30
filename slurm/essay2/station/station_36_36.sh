#!/bin/bash
#SBATCH --partition=long
#SBATCH --nodes=1
#SBATCH --cpus-per-task=48
#SBATCH --mem=200G
#SBATCH --time=5-00:00:00
#SBATCH --job-name=sta_36_36
#SBATCH --output=/home/mundhra.ve/poker_thesis/results/essay2/station_36_36/job.log
#SBATCH --error=/home/mundhra.ve/poker_thesis/results/essay2/station_36_36/job.err
#SBATCH --mail-type=END,FAIL
#SBATCH --mail-user=mundhra.ve@northeastern.edu

export LD_LIBRARY_PATH=/shared/centos7/boost/1.80.0/lib:$LD_LIBRARY_PATH
module load python/3.13.5
source /home/mundhra.ve/poker_thesis/openspiel_env_explorer/bin/activate

cat > /tmp/station_params.conf << CONF
UTILITY_TYPE 2
BETA 5.0
CONF

/home/mundhra.ve/poker_thesis/open-pure-cfr-buckets/pure_cfr \
    /home/mundhra.ve/poker_thesis/poker-cfrm/games/holdem.limit.2p.36_36.game \
    /home/mundhra.ve/poker_thesis/results/essay2/station_36_36/strategy \
    --card-abs=FILE:/home/mundhra.ve/poker_thesis/holdem_100b_cfrm.abs \
    --threads=48 \
    --checkpoint=3600 \
    --max-walltime=04:23:00:00 \
    --config=/tmp/station_params.conf
