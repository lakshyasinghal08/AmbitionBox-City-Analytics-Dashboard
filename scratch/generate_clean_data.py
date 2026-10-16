import pandas as pd
import re
import os

MASTER_PATH = 'processed_data/master_ambitionbox.csv'
CLEANED_PATH = 'processed_data/cleaned_ambitionbox.csv'

df = pd.read_csv(MASTER_PATH)

# Deduplicate exactly: 94,580 -> 64,210
df = df.drop_duplicates(subset=['company_name', 'company_rating', 'other_data']).copy()

df['company_name'] = df['company_name'].fillna('Unknown').astype(str).str.strip()
df['company_rating'] = pd.to_numeric(df['company_rating'], errors='coerce').fillna(3.5).round(1)
df['city'] = df['city'].fillna('Unknown').astype(str).str.strip()
df['other_data'] = df['other_data'].fillna('').astype(str).str.strip()

known_types = [
    'Public', 'Private', 'Startup', 'Government', 'Conglomerate',
    'Fortune India 500', 'Forbes Global 2000', 'Non-Profit', 'JV'
]

known_sizes = [
    '1-10', '11-50', '51-200', '201-500', '501-1k', '1k-5k', '5k-10k', '10k-50k', '50k-1 Lakh', '1 Lakh+'
]

anomalous_inds = {'delhi', 'central', 'roswell', 'bombay'}

def parse_record(other, city):
    if not other:
        return '—', '—', '—', None, city
    
    parts = [p.strip() for p in other.split(',') if p.strip()]
    if not parts:
        return '—', '—', '—', None, city
        
    industry = '—'
    size = '—'
    ctype = '—'
    age = None
    location = city
    
    for p in parts:
        plow = p.lower()
        # Size
        if 'employee' in plow:
            s_clean = re.sub(r'(?i)\s*employees?', '', p).strip()
            s_base = re.sub(r'\s*\(Global\)', '', s_clean).strip()
            size = s_base
        # Age
        elif 'year' in plow and 'old' in plow:
            m = re.search(r'(\d+)\s*years?\s*old', p, re.I)
            if m:
                age = int(m.group(1))
        # Type
        elif any(kt.lower() == plow for kt in known_types) or plow in ['private', 'public', 'startup']:
            ctype = p
        elif 'fortune' in plow or 'forbes' in plow or 'conglomerate' in plow or 'non-profit' in plow:
            ctype = p
        # Location with +more
        elif '+' in p and 'more' in plow:
            loc = re.sub(r'\+\d+\s*more', '', p).strip()
            if loc:
                location = loc
        elif p in ['Ahmedabad', 'Bangalore', 'Chennai', 'Gurugram', 'Hyderabad', 'Indore', 'Jaipur', 'Mumbai', 'Noida', 'Pune']:
            location = p

    # Industry determination
    first = parts[0].strip()
    flow = first.lower()
    if ('employee' not in flow and 
        'year' not in flow and 
        not any(kt.lower() == flow for kt in known_types) and
        '+' not in first and
        first != location and
        'more' not in flow and
        flow not in anomalous_inds and
        not re.match(r'^\d+\s*old', flow)):
        if len(first) > 1 and first != 'Unknown':
            industry = first

    return industry, size, ctype, age, location

industries = []
sizes = []
types = []
ages = []
locations = []

for _, row in df.iterrows():
    ind, sz, ct, ag, loc = parse_record(row['other_data'], row['city'])
    industries.append(ind)
    sizes.append(sz)
    types.append(ct)
    ages.append(ag)
    locations.append(loc)

df['industry'] = industries
df['size'] = sizes
df['type'] = types
df['age'] = ages
df['location'] = locations

valid_inds = sorted([i for i in df['industry'].unique() if i != '—'])
print(f"Cleaned valid industries count: {len(valid_inds)}")
print(f"Unique locations count: {df['location'].nunique()}")

# Sort default by rating desc using stable sort to preserve original order
df = df.sort_values(by='company_rating', ascending=False, kind='stable').reset_index(drop=True)

df.to_csv(CLEANED_PATH, index=False)
print("Saved cleaned data to:", CLEANED_PATH)
