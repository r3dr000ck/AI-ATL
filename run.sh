python3 ./data/stock.py download META --start 2023-07-01 --end 2023-07-31 --out ../data/meta-july.csv
python3 ./models/gemini_1.py
python3 ./models/gemini.py