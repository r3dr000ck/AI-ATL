if [ "$#" -ne 3 ]; then
    echo "Usage: ./run.sh TICKER START_DATE END_DATE"
    echo "Example: ./run.sh META 2025-08-01 2025-09-01"
    exit 1
fi

python3 ./data/stock.py download $1 --start $2 --end $3 --out ../data/gemini.csv
python3 ./models/gemini_1.py
python3 ./models/gemini.py