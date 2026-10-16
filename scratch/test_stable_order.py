import pandas as pd

df = pd.read_csv('processed_data/master_ambitionbox.csv')
df = df.drop_duplicates(subset=['company_name', 'company_rating', 'other_data']).copy()

# Stable sort by rating desc
df_sorted = df.sort_values(by='company_rating', ascending=False, kind='stable')

# Check first 10 for Ahmedabad
ahm = df_sorted[df_sorted['city'] == 'Ahmedabad'].head(10)
print("Top 10 in Ahmedabad with stable sort:")
for i, (_, r) in enumerate(ahm.iterrows()):
    print(f"{i+1}. {r['company_name']} | {r['company_rating']}")
