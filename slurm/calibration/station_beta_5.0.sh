#!/bin/bash
#SBATCH --partition=short
#SBATCH --nodes=1
#SBATCH --cpus-per-task=48
#SBATCH --mem=500G
#SBATCH --time=0-12:00:00
#SBATCH --job-name=calib_station_0.1
#SBATCH --output=/home/mundhra.ve/poker_thesis/calibration/station/0.1/job.log
#SBATCH --error=/home/mundhra.ve/poker_thesis/calibration/station/0.1/job.err
#SBATCH --mail-type=END,FAIL
#SBATCH --mail-user=mundhra.ve@northeastern.edu

# ── EDIT THESE THREE LINES ──────────────────────────────────────────────────
ARCHETYPE="station"       # maniac | station
UTILITY_TYPE=2           # 1=maniac, 2=station
PARAM_VALUE=5.0          # the alpha (maniac) or beta (station) value to test
# ────────────────────────────────────────────────────────────────────────────

OUTDIR="/home/mundhra.ve/poker_thesis/calibration/${ARCHETYPE}/${PARAM_VALUE}"
BASELINE="/home/mundhra.ve/poker_thesis/results/baseline_36_36/strategy.iter-255697373k.secs-208800"
GAMEDEF="/home/mundhra.ve/poker_thesis/poker-cfrm/games/holdem.limit.2p.36_36.game"
ABS="/home/mundhra.ve/poker_thesis/holdem_100b_cfrm.abs"
SOLVER="/home/mundhra.ve/poker_thesis/open-pure-cfr-buckets/pure_cfr"
MEASURE="/home/mundhra.ve/poker_thesis/measure_raise_freq.py"

export LD_LIBRARY_PATH=/shared/centos7/boost/1.80.0/lib:$LD_LIBRARY_PATH
module load python/3.13.5
source /home/mundhra.ve/poker_thesis/openspiel_env_explorer/bin/activate

mkdir -p ${OUTDIR}

# Write config file with utility params
cat > ${OUTDIR}/params.conf << EOF
UTILITY_TYPE ${UTILITY_TYPE}
ALPHA $([ "$ARCHETYPE" = "maniac" ] && echo $PARAM_VALUE || echo 0.0)
BETA $([ "$ARCHETYPE" = "station" ] && echo $PARAM_VALUE || echo 0.0)
LAMBDA 1.0
EOF

echo "=== Starting calibration solve ==="
echo "Archetype:   ${ARCHETYPE}"
echo "Param value: ${PARAM_VALUE}"
echo "Output dir:  ${OUTDIR}"
echo "Started:     $(date)"

# Run solver starting from converged baseline, 12 hours
${SOLVER} ${GAMEDEF} ${OUTDIR}/strategy \
    --load-dump=${BASELINE} \
    --card-abs=FILE:${ABS} \
    --threads=48 \
    --checkpoint=3600 \
    --max-walltime=04:23:00:00 \
    --config=${OUTDIR}/params.conf

echo "=== Solve complete. Measuring raise frequency ==="
echo "Completed:   $(date)"

# Find most recent strategy file
LATEST_PLAYER=$(ls -t ${OUTDIR}/strategy.*.player 2>/dev/null | head -1)

if [ -z "$LATEST_PLAYER" ]; then
    echo "ERROR: No player file found in ${OUTDIR}"
    exit 1
fi

echo "Using strategy: ${LATEST_PLAYER}"

python3 ${MEASURE} ${LATEST_PLAYER} --hands 200000 --seed 42 \
    | tee ${OUTDIR}/raise_freq.txt

echo "=== Done ==="
