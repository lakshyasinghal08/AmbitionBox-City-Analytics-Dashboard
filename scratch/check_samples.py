import pandas as pd
from test_parse import parse_row, df

sample_names = [
    'Taletel', 'The Leela Corporation', 'Flora Fountain', 'Peanut Square',
    'Praeclarum Tech', 'Browseinfo', 'Silicon Signals', 'Digicorp Information Systems',
    'Edugo Abroad', 'Simptel'
]

for name in sample_names:
    matches = df[df['company_name'] == name]
    if not matches.empty:
        row = matches.iloc[0]
        parsed = parse_row(row['other_data'], row['city'])
        print(f"Name: {name} | Rating: {row['company_rating']} | Parsed: {parsed}")
        print(f"   Raw other_data: {repr(row['other_data'])}\n")
    else:
        print(f"NOT FOUND: {name}")
