import pandas as pd
import glob
import os

df = pd.read_csv('processed_data/master_ambitionbox.csv')
print("df length:", len(df))

# Check duplicate combinations
for cols in [
    ['company_name'],
    ['company_name', 'city'],
    ['company_name', 'other_data'],
    ['company_name', 'company_rating', 'other_data'],
    ['company_name', 'company_rating', 'city'],
    ['company_name', 'company_rating', 'other_data', 'city']
]:
    rem = len(df.drop_duplicates(subset=cols))
    print(f"drop_duplicates on {cols}: {rem} (diff: {len(df) - rem})")

# Also check if merging the 10 RawData files gives 94580 and deduplicating
files = glob.glob('RawData/*.csv')
raw_dfs = []
for f in files:
    city_name = os.path.basename(f).replace('.csv', '').capitalize()
    rdf = pd.read_csv(f)
    rdf['city'] = city_name
    raw_dfs.append(rdf)
raw_merged = pd.concat(raw_dfs, ignore_index=True)
print("\nRaw merged len:", len(raw_merged))
for col in ['company_name', 'other_data']:
    raw_merged[col] = raw_merged[col].astype(str).str.strip()

print("Raw merged drop dup total:", len(raw_merged.drop_duplicates()))
for cols in [
    ['company_name', 'other_data'],
    ['company_name', 'city'],
    ['company_name', 'company_rating', 'other_data'],
    ['company_name', 'company_rating', 'city'],
    ['company_name', 'company_rating', 'other_data', 'city']
]:
    rem = len(raw_merged.drop_duplicates(subset=cols))
    print(f"Raw drop_duplicates on {cols}: {rem} (diff: {len(raw_merged) - rem})")
