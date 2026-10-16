import pandas as pd
import re

df = pd.read_csv('processed_data/master_ambitionbox.csv')
df = df.drop_duplicates(subset=['company_name', 'company_rating', 'other_data']).copy()
print("Deduplicated df:", len(df))
print("Avg rating:", round(df['company_rating'].mean(), 2))

# Let's inspect parts of other_data
# In AmbitionBox, other_data typically contains:
# "Industry , Size Employees , Type , Age years old , Location +X more"
# Examples:
# 'Pharma , 10k-50k Employees , Public , 72 years old , Ahmedabad +152 more'
# 'Pharma , 10k-50k Employees , Fortune India 500 , 47 years old , Ahmedabad +116 more'
# 'Telecom , 5k-10k Employees , Public , 6 years old , Ahmedabad +637 more'
# 'Software Product , 1k-5k Employees , 13 years old , Ahmedabad +53 more'
# 'Marketing & Advertising , 11-50 Employees , 6 years old , Ahmedabad'

def parse_row(text, fallback_city):
    if not isinstance(text, str) or not text.strip():
        return {
            'industry': '—',
            'size': '—',
            'type': '—',
            'age': None,
            'location': fallback_city
        }
    
    parts = [p.strip() for p in text.split(',') if p.strip()]
    
    industry = '—'
    size = '—'
    comp_type = '—'
    age = None
    location = fallback_city
    
    # Common company types
    known_types = [
        'Public', 'Private', 'Startup', 'Government', 'Conglomerate',
        'Fortune India 500', 'Forbes Global 2000', 'MNC', 'Non-Profit', 'JV'
    ]
    
    for p in parts:
        p_clean = p.strip()
        p_lower = p_clean.lower()
        
        # Check size (e.g., "10k-50k Employees", "1 Lakh+ Employees", "11-50 Employees", "1-10 Employees")
        if 'employee' in p_lower:
            size = re.sub(r'(?i)\s*employees?', '', p_clean).strip()
        
        # Check age (e.g., "72 years old", "1 year old", "6 years old")
        elif 'year' in p_lower and 'old' in p_lower:
            m = re.search(r'(\d+)\s*years?\s*old', p_clean, re.I)
            if m:
                age = int(m.group(1))
        
        # Check type
        elif any(kt.lower() == p_lower for kt in known_types) or 'private' in p_lower or 'public' in p_lower or 'startup' in p_lower:
            comp_type = p_clean
            
        # Check location (e.g. "Ahmedabad +152 more" or city name)
        elif '+' in p_clean and 'more' in p_lower:
            # e.g. "Ahmedabad +152 more" -> "Ahmedabad"
            loc = re.sub(r'\+\d+\s*more', '', p_clean).strip()
            if loc:
                location = loc
        elif p_clean in ['Ahmedabad', 'Bangalore', 'Chennai', 'Gurugram', 'Hyderabad', 'Indore', 'Jaipur', 'Mumbai', 'Noida', 'Pune'] or (len(parts) > 1 and p == parts[-1] and not any(k in p_lower for k in ['employee', 'year', 'old'])):
            # Potential location if last item
            loc = re.sub(r'\+\d+\s*more', '', p_clean).strip()
            if loc and len(loc) < 30:
                location = loc
                
    # First part is almost always Industry if it's not size/age/type/location
    if parts:
        first = parts[0].strip()
        first_lower = first.lower()
        if ('employee' not in first_lower and 
            'year' not in first_lower and 
            first not in known_types and 
            '+' not in first and
            first != location):
            industry = first

    return {
        'industry': industry,
        'size': size,
        'type': comp_type,
        'age': age,
        'location': location
    }

parsed = [parse_row(row['other_data'], row['city']) for _, row in df.iterrows()]
pdf = pd.DataFrame(parsed)

print("\nParsed summary:")
print("Unique industries:", pdf['industry'].nunique(), "Sample industries:", pdf['industry'].value_counts().head(10))
print("Unique locations:", pdf['location'].nunique())
print("Unique sizes:", pdf['size'].value_counts())
print("Unique types:", pdf['type'].value_counts().head(10))
print("Age summary:", pdf['age'].describe())
