import pandas as pd

df = pd.read_csv('processed_data/master_ambitionbox.csv')
df = df.drop_duplicates(subset=['company_name', 'company_rating', 'other_data'])

# Let's see rows where company_rating == 5.0 in the order they appear in the file!
ahmedabad_5 = df[(df['city'] == 'Ahmedabad') & (df['company_rating'] == 5.0)]
print("First 15 5.0 rated companies in Ahmedabad in original dataset order:")
for i, (idx, r) in enumerate(ahmedabad_5.head(15).iterrows()):
    print(f"{i+1}. {r['company_name']} | other_data: {r['other_data']}")
