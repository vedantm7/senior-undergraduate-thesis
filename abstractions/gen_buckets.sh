#!/bin/bash
#SBATCH --job-name=poker_buckets
#SBATCH --partition=short
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=32
#SBATCH --mem=64G
#SBATCH --time=36:00:00
#SBATCH --output=/home/mundhra.ve/poker_thesis/buckets_%j.log
#SBATCH --mail-type=BEGIN,END,FAIL
#SBATCH --mail-user=mundhra.ve@northeastern.edu

module load gcc/11.1.0
module load boost/1.80.0

cd ~/poker_thesis/poker-cfrm

./cluster-abs --save-to /home/mundhra.ve/poker_thesis/holdem_100b.abs --buckets 1,100,100,100 --metric mixed_nooo --nb-samples 0,1000,1000,1000 --threads 32 --handranks /home/mundhra.ve/poker_thesis/poker-cfrm/handranks.dat

echo "Bucket generation complete! Exit code: $?"
ls -lh /home/mundhra.ve/poker_thesis/holdem_100b.abs
