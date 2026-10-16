import pandas as pd
import re

# Load master
df = pd.read_csv('processed_data/master_ambitionbox.csv')
print("Initial shape:", df.shape)

# Exact duplicates
dup_count = df.duplicated().sum()
print("Exact duplicates:", dup_count)

df_clean = df.drop_duplicates().copy()
print("After drop_duplicates:", df_clean.shape)

# Let's see some other_data samples
print("\nSample other_data:")
for x in df_clean['other_data'].dropna().head(20):
    print(repr(x))
