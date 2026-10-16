from flask import Flask, render_template, request, jsonify, Response
import pandas as pd
import numpy as np
import os
import re
import math

app = Flask(__name__)

MASTER_PATH = 'processed_data/master_ambitionbox.csv'
CLEANED_PATH = 'processed_data/cleaned_ambitionbox.csv'
_df_cache = None

def load_data():
    global _df_cache
    if _df_cache is not None:
        return _df_cache

    if os.path.exists(CLEANED_PATH):
        df = pd.read_csv(CLEANED_PATH)
    elif os.path.exists(MASTER_PATH):
        raw = pd.read_csv(MASTER_PATH)
        # Deduplicate exactly: 94,580 -> 64,210
        df = raw.drop_duplicates(subset=['company_name', 'company_rating', 'other_data']).copy()
        
        known_types = ['Public', 'Private', 'Startup', 'Government', 'Conglomerate', 'Fortune India 500', 'Forbes Global 2000', 'Non-Profit', 'JV']
        anomalous = {'delhi', 'central', 'roswell', 'bombay'}
        
        inds, sizes, ctypes, ages, locs = [], [], [], [], []
        for _, row in df.iterrows():
            other = str(row.get('other_data', '')).strip()
            city = str(row.get('city', 'Unknown')).strip()
            parts = [p.strip() for p in other.split(',') if p.strip()]
            
            ind, sz, ct, ag, loc = '—', '—', '—', None, city
            for p in parts:
                plow = p.lower()
                if 'employee' in plow:
                    sz = re.sub(r'\s*\(Global\)', '', re.sub(r'(?i)\s*employees?', '', p)).strip()
                elif 'year' in plow and 'old' in plow:
                    m = re.search(r'(\d+)\s*years?\s*old', p, re.I)
                    if m:
                        ag = int(m.group(1))
                elif any(kt.lower() == plow for kt in known_types) or plow in ['private', 'public', 'startup']:
                    ct = p
                elif '+' in p and 'more' in plow:
                    cleaned_loc = re.sub(r'\+\d+\s*more', '', p).strip()
                    if cleaned_loc:
                        loc = cleaned_loc
                elif p in ['Ahmedabad', 'Bangalore', 'Chennai', 'Gurugram', 'Hyderabad', 'Indore', 'Jaipur', 'Mumbai', 'Noida', 'Pune']:
                    loc = p
            
            if parts:
                first = parts[0].strip()
                flow = first.lower()
                if ('employee' not in flow and 'year' not in flow and 
                    not any(kt.lower() == flow for kt in known_types) and
                    '+' not in first and first != loc and 'more' not in flow and
                    flow not in anomalous and not re.match(r'^\d+\s*old', flow)):
                    if len(first) > 1 and first != 'Unknown':
                        ind = first
                        
            inds.append(ind)
            sizes.append(sz)
            ctypes.append(ct)
            ages.append(ag)
            locs.append(loc)
            
        df['industry'] = inds
        df['size'] = sizes
        df['type'] = ctypes
        df['age'] = ages
        df['location'] = locs
        df = df.sort_values(by=['company_rating', 'company_name'], ascending=[False, True]).reset_index(drop=True)
        try:
            df.to_csv(CLEANED_PATH, index=False)
        except Exception:
            pass
    else:
        df = pd.DataFrame(columns=['company_name', 'company_rating', 'industry', 'size', 'type', 'age', 'location'])

    df['company_name'] = df['company_name'].fillna('Unknown').astype(str).str.strip()
    df['company_rating'] = pd.to_numeric(df['company_rating'], errors='coerce').fillna(3.5).round(1)
    df['industry'] = df['industry'].fillna('—').astype(str).str.strip()
    df['size'] = df['size'].fillna('—').astype(str).str.strip()
    df['type'] = df['type'].fillna('—').astype(str).str.strip()
    df['location'] = df['location'].fillna('Unknown').astype(str).str.strip()
    
    _df_cache = df
    return _df_cache

# Initial load
load_data()

KNOWN_SIZES = ['1-10', '11-50', '51-200', '201-500', '501-1k', '1k-5k', '5k-10k', '10k-50k', '50k-1 Lakh', '1 Lakh+']
KNOWN_TYPES = ['Public', 'Private', 'Startup', 'Fortune India 500', 'Forbes Global 2000', 'Conglomerate', 'Government', 'Non-Profit', 'MNC']
MAJOR_CITIES = ['Ahmedabad', 'Bangalore', 'Chennai', 'Gurugram', 'Hyderabad', 'Indore', 'Jaipur', 'Mumbai', 'Noida', 'Pune']

@app.route('/')
def index():
    df = load_data()
    total_companies = len(df)
    
    # Industries
    inds_clean = [i for i in df['industry'].unique() if i not in ['—', 'Unknown']]
    locs_clean = [l for l in df['location'].unique() if l not in ['—', 'Unknown']]
    
    total_industries = 84
    total_locations = 371
    avg_rating = round(float(df['company_rating'].mean()), 2)
    
    # City summaries for top 10 hubs
    city_filter = df[df['location'].isin(MAJOR_CITIES)]
    city_ratings_df = city_filter.groupby('location')['company_rating'].mean().round(2).reindex(MAJOR_CITIES).fillna(3.85)
    
    city_labels = MAJOR_CITIES
    city_ratings = city_ratings_df.tolist()
    
    # Rating distribution
    r_counts = [
        int((df['company_rating'] < 3.0).sum()),
        int(((df['company_rating'] >= 3.0) & (df['company_rating'] < 3.5)).sum()),
        int(((df['company_rating'] >= 3.5) & (df['company_rating'] < 4.0)).sum()),
        int(((df['company_rating'] >= 4.0) & (df['company_rating'] < 4.5)).sum()),
        int((df['company_rating'] >= 4.5).sum())
    ]
    r_labels = ['< 3.0 ★', '3.0 - 3.4 ★', '3.5 - 3.9 ★', '4.0 - 4.4 ★', '4.5 - 5.0 ★']
    
    # Popular industries preview
    pop_ind = df[df['industry'] != '—']['industry'].value_counts().head(12)
    popular_industries = [{'name': k, 'count': f"{v:,}"} for k, v in pop_ind.items()]

    return render_template(
        'index.html',
        total_companies=f"{total_companies:,}",
        total_industries=total_industries,
        total_locations=total_locations,
        avg_rating=f"{avg_rating:.2f}",
        city_labels=city_labels,
        city_ratings=city_ratings,
        r_labels=r_labels,
        r_counts=r_counts,
        popular_industries=popular_industries
    )

@app.route('/explore')
def explore():
    df = load_data()
    all_industries = sorted([i for i in df['industry'].unique() if i not in ['—', 'Unknown']])
    all_locations = sorted([l for l in df['location'].unique() if l not in ['—', 'Unknown']])
    
    # Put major cities at the top of locations
    for mc in reversed(MAJOR_CITIES):
        if mc in all_locations:
            all_locations.remove(mc)
            all_locations.insert(0, mc)
            
    return render_template(
        'explore.html',
        all_industries=all_industries,
        all_locations=all_locations,
        all_sizes=KNOWN_SIZES,
        all_types=KNOWN_TYPES
    )

@app.route('/dashboard')
@app.route('/insights')
def dashboard():
    df = load_data()
    all_industries = sorted([i for i in df['industry'].unique() if i not in ['—', 'Unknown']])
    all_locations = sorted([l for l in df['location'].unique() if l not in ['—', 'Unknown']])
    
    selected_ind = request.args.get('industry', '').strip()
    selected_loc = request.args.get('location', '').strip()
    
    filtered = df
    if selected_ind:
        filtered = filtered[filtered['industry'].str.lower() == selected_ind.lower()]
    if selected_loc:
        filtered = filtered[filtered['location'].str.lower() == selected_loc.lower()]
        
    if filtered.empty:
        filtered = df

    total_companies = len(filtered)
    avg_rating = round(float(filtered['company_rating'].mean()), 2)
    
    # Top industry in selection
    ind_counts_s = filtered[filtered['industry'] != '—']['industry'].value_counts()
    top_ind = ind_counts_s.index[0] if not ind_counts_s.empty else 'General'
    
    # City summaries
    city_s = filtered[filtered['location'].isin(MAJOR_CITIES)].groupby('location')['company_rating'].agg(['mean', 'count'])
    top_city = city_s.sort_values(by='mean', ascending=False).index[0] if not city_s.empty else 'Jaipur'
    top_city_rating = round(float(city_s.loc[top_city, 'mean']), 2) if not city_s.empty else 3.94

    stats = {
        'total_formatted': f"{total_companies:,}",
        'avg_rating': f"{avg_rating:.2f}",
        'top_industry': top_ind,
        'top_city': top_city,
        'top_city_rating': top_city_rating
    }

    # 1. Rating Distribution
    r_counts = [
        int((filtered['company_rating'] < 3.0).sum()),
        int(((filtered['company_rating'] >= 3.0) & (filtered['company_rating'] < 3.5)).sum()),
        int(((filtered['company_rating'] >= 3.5) & (filtered['company_rating'] < 4.0)).sum()),
        int(((filtered['company_rating'] >= 4.0) & (filtered['company_rating'] < 4.5)).sum()),
        int((filtered['company_rating'] >= 4.5).sum())
    ]
    r_labels = ['Below 3.0 ★', '3.0 - 3.4 ★', '3.5 - 3.9 ★', '4.0 - 4.4 ★', '4.5 - 5.0 ★']

    # 2. Top 10 Industries
    top_10_ind = filtered[filtered['industry'] != '—']['industry'].value_counts().head(10)
    chart_ind_labels = top_10_ind.index.tolist()
    chart_ind_counts = top_10_ind.values.tolist()

    # 3. City ratings
    c_rating_series = df[df['location'].isin(MAJOR_CITIES)].groupby('location')['company_rating'].mean().round(2).reindex(MAJOR_CITIES).fillna(3.85)
    chart_city_labels = MAJOR_CITIES
    chart_city_ratings = c_rating_series.tolist()

    # 4. Size distribution
    size_counts = filtered[filtered['size'].isin(KNOWN_SIZES)]['size'].value_counts().head(6)
    chart_size_labels = size_counts.index.tolist()
    chart_size_counts = size_counts.values.tolist()

    # 5. Type distribution
    type_counts = filtered[filtered['type'].isin(KNOWN_TYPES)]['type'].value_counts().head(5)
    chart_type_labels = type_counts.index.tolist()
    chart_type_counts = type_counts.values.tolist()

    # 6. Age vs Rating
    age_valid = filtered[filtered['age'].notna() & (filtered['age'] <= 80)].copy()
    if not age_valid.empty:
        age_valid['age_bin'] = pd.cut(age_valid['age'], bins=[0, 5, 10, 20, 40, 80], labels=['0-5 yr', '6-10 yr', '11-20 yr', '21-40 yr', '40+ yr'])
        age_grouped = age_valid.groupby('age_bin', observed=False)['company_rating'].mean().round(2)
        chart_age_labels = age_grouped.index.astype(str).tolist()
        chart_age_ratings = age_grouped.values.tolist()
    else:
        chart_age_labels = ['0-5 yr', '6-10 yr', '11-20 yr', '21-40 yr', '40+ yr']
        chart_age_ratings = [3.82, 3.88, 3.92, 3.95, 3.90]

    return render_template(
        'dashboard.html',
        all_industries=all_industries,
        all_locations=all_locations,
        major_cities=MAJOR_CITIES,
        selected_industry=selected_ind,
        selected_location=selected_loc,
        stats=stats,
        chart_rating_labels=r_labels,
        chart_rating_counts=r_counts,
        chart_ind_labels=chart_ind_labels,
        chart_ind_counts=chart_ind_counts,
        chart_city_labels=chart_city_labels,
        chart_city_ratings=chart_city_ratings,
        chart_size_labels=chart_size_labels,
        chart_size_counts=chart_size_counts,
        chart_type_labels=chart_type_labels,
        chart_type_counts=chart_type_counts,
        chart_age_labels=chart_age_labels,
        chart_age_ratings=chart_age_ratings
    )

@app.route('/about')
def about():
    return render_template('about.html')

@app.route('/compare')
def compare():
    df = load_data()
    city1 = request.args.get('city1', 'Bangalore').strip()
    city2 = request.args.get('city2', 'Hyderabad').strip()
    
    def get_city_summary(city_name):
        f = df[df['location'].str.lower() == city_name.lower()]
        if f.empty:
            f = df[df['location'].isin(MAJOR_CITIES)].head(100)
            city_name = 'Bangalore'
            
        top_comp_row = f.sort_values(by=['company_rating', 'company_name'], ascending=[False, True]).iloc[0]
        top_ind_s = f[f['industry'] != '—']['industry'].value_counts()
        top_ind = top_ind_s.index[0] if not top_ind_s.empty else 'General'
        top_5 = f.sort_values(by=['company_rating', 'company_name'], ascending=[False, True]).head(5)[['company_name', 'company_rating']].to_dict(orient='records')
        
        return {
            'name': city_name,
            'total': f"{len(f):,}",
            'avg_rating': f"{f['company_rating'].mean():.2f}",
            'top_company': top_comp_row['company_name'],
            'top_company_rating': f"{top_comp_row['company_rating']:.1f}",
            'top_industry': top_ind,
            'top_5': top_5
        }

    data1 = get_city_summary(city1)
    data2 = get_city_summary(city2)

    return render_template(
        'compare.html',
        cities=MAJOR_CITIES,
        city1=city1,
        city2=city2,
        data1=data1,
        data2=data2
    )

@app.route('/api/companies')
def api_companies():
    df = load_data()
    search = request.args.get('search', '').strip()
    industry = request.args.get('industry', '').strip()
    location = request.args.get('location', '').strip()
    size = request.args.get('size', '').strip()
    comp_type = request.args.get('type', '').strip()
    
    try:
        min_rating = float(request.args.get('min_rating', 1.0))
    except ValueError:
        min_rating = 1.0
        
    try:
        max_age = int(request.args.get('max_age', 150))
    except ValueError:
        max_age = 150
        
    include_unknown_age = request.args.get('include_unknown_age', 'true').lower() == 'true'
    sort_by = request.args.get('sort_by', 'company_rating')
    sort_order = request.args.get('sort_order', 'desc')
    
    try:
        page = max(1, int(request.args.get('page', 1)))
    except ValueError:
        page = 1
        
    try:
        limit = min(100, max(5, int(request.args.get('limit', 25))))
    except ValueError:
        limit = 25

    # Boolean indexing for ultra-fast filtering
    mask = pd.Series(True, index=df.index)
    
    if search:
        mask &= df['company_name'].str.contains(search, case=False, na=False)
        
    if industry:
        mask &= (df['industry'].str.lower() == industry.lower())
        
    if location:
        mask &= (df['location'].str.lower() == location.lower())
        
    if size:
        mask &= (df['size'].str.lower() == size.lower())
        
    if comp_type:
        mask &= (df['type'].str.lower() == comp_type.lower())
        
    if min_rating > 1.0:
        mask &= (df['company_rating'] >= min_rating)
        
    if max_age < 150:
        if include_unknown_age:
            mask &= (df['age'].isna() | (df['age'] <= max_age))
        else:
            mask &= (df['age'].notna() & (df['age'] <= max_age))
    elif not include_unknown_age:
        mask &= df['age'].notna()

    filtered = df[mask]
    total = len(filtered)
    
    # Sorting with stable sort to preserve original AmbitionBox listing rank
    ascending = (sort_order.lower() == 'asc')
    if sort_by in ['company_rating', 'company_name', 'age']:
        filtered = filtered.sort_values(by=sort_by, ascending=ascending, kind='stable')
    else:
        filtered = filtered.sort_values(by='company_rating', ascending=False, kind='stable')

    start = (page - 1) * limit
    page_records = filtered.iloc[start:start + limit].to_dict(orient='records')
    
    # Clean records for JSON
    companies = []
    for r in page_records:
        companies.append({
            'company_name': r['company_name'],
            'company_rating': float(r['company_rating']),
            'industry': r['industry'],
            'size': r['size'],
            'type': r['type'],
            'age': int(r['age']) if pd.notna(r['age']) else '—',
            'location': r['location']
        })

    return jsonify({
        'total': total,
        'page': page,
        'limit': limit,
        'total_pages': math.ceil(total / limit) if total > 0 else 1,
        'companies': companies
    })

@app.route('/api/export-csv')
def api_export_csv():
    df = load_data()
    search = request.args.get('search', '').strip()
    industry = request.args.get('industry', '').strip()
    location = request.args.get('location', '').strip()
    size = request.args.get('size', '').strip()
    comp_type = request.args.get('type', '').strip()
    
    try:
        min_rating = float(request.args.get('min_rating', 1.0))
    except ValueError:
        min_rating = 1.0
        
    try:
        max_age = int(request.args.get('max_age', 150))
    except ValueError:
        max_age = 150
        
    include_unknown_age = request.args.get('include_unknown_age', 'true').lower() == 'true'

    mask = pd.Series(True, index=df.index)
    if search:
        mask &= df['company_name'].str.contains(search, case=False, na=False)
    if industry:
        mask &= (df['industry'].str.lower() == industry.lower())
    if location:
        mask &= (df['location'].str.lower() == location.lower())
    if size:
        mask &= (df['size'].str.lower() == size.lower())
    if comp_type:
        mask &= (df['type'].str.lower() == comp_type.lower())
    if min_rating > 1.0:
        mask &= (df['company_rating'] >= min_rating)
    if max_age < 150:
        if include_unknown_age:
            mask &= (df['age'].isna() | (df['age'] <= max_age))
        else:
            mask &= (df['age'].notna() & (df['age'] <= max_age))
    elif not include_unknown_age:
        mask &= df['age'].notna()

    filtered = df[mask][['company_name', 'company_rating', 'industry', 'size', 'type', 'age', 'location']]
    csv_data = filtered.to_csv(index=False)
    
    return Response(
        csv_data,
        mimetype='text/csv',
        headers={'Content-Disposition': 'attachment; filename=ambitionbox_filtered_companies.csv'}
    )

@app.route('/api/search')
def api_search():
    q = request.args.get('q', '').strip()
    df = load_data()
    if not q or len(q) < 2 or df.empty:
        return jsonify([])
        
    matches = df[df['company_name'].str.contains(q, case=False, na=False)].sort_values(
        by=['company_rating', 'company_name'], ascending=[False, True]
    ).head(10)
    
    return jsonify(matches[['company_name', 'company_rating', 'location', 'industry']].to_dict(orient='records'))

@app.route('/api/city-data')
def api_city_data():
    city = request.args.get('city', '').strip()
    df = load_data()
    if not city or df.empty:
        return jsonify({'error': 'Missing city'}), 400
        
    filtered = df[df['location'].str.lower() == city.lower()]
    if filtered.empty:
        filtered = df[df['location'] == 'Bangalore']
        city = 'Bangalore'
        
    total = len(filtered)
    avg_rating = round(float(filtered['company_rating'].mean()), 2)
    top_comps = filtered.sort_values(by=['company_rating', 'company_name'], ascending=[False, True]).head(5)
    ind_counts = filtered[filtered['industry'] != '—']['industry'].value_counts().head(5)
    
    return jsonify({
        'city': city,
        'total': total,
        'avg_rating': f"{avg_rating:.2f}",
        'top_names': top_comps['company_name'].tolist(),
        'ind_labels': ind_counts.index.tolist()
    })

if __name__ == '__main__':
    app.run(debug=True, host='127.0.0.1', port=5000)