from flask import Flask, render_template, request, jsonify, url_for
import pandas as pd
import os

app = Flask(__name__)
MASTER_PATH = 'processed_data/master_ambitionbox.csv'

def load_master_data():
    if os.path.exists(MASTER_PATH):
        df = pd.read_csv(MASTER_PATH)
        if 'industry' not in df.columns and 'other_data' in df.columns:
            df['other_data'] = df['other_data'].fillna('')
            split_data = df['other_data'].str.split(',', expand=True)
            df['industry'] = split_data[0].str.strip() if len(split_data.columns) > 0 else 'Unknown'
        return df
    return pd.DataFrame()

@app.route('/')
def index():
    df = load_master_data()
    cities = sorted(df['city'].unique().tolist()) if not df.empty and 'city' in df.columns else []
    total_companies = len(df) if not df.empty else 0
    total_cities = len(cities)
    avg_global = round(df['company_rating'].mean(), 2) if not df.empty else 0.0

    city_avg = df.groupby('city')['company_rating'].mean().round(2).reset_index() if not df.empty else pd.DataFrame()
    city_counts = df.groupby('city')['company_name'].count().reset_index() if not df.empty else pd.DataFrame()

    return render_template('index.html',
                           cities=cities,
                           total_companies=total_companies,
                           total_cities=total_cities,
                           avg_global=avg_global,
                           city_labels=city_avg['city'].tolist() if not city_avg.empty else [],
                           city_ratings=city_avg['company_rating'].tolist() if not city_avg.empty else [],
                           city_counts=city_counts['company_name'].tolist() if not city_counts.empty else [])

@app.route('/explore')
def explore():
    df = load_master_data()
    cities = sorted(df['city'].unique().tolist()) if not df.empty and 'city' in df.columns else []
    return render_template('explore.html', cities=cities)

@app.route('/compare')
def compare():
    df = load_master_data()
    cities = sorted(df['city'].unique().tolist()) if not df.empty and 'city' in df.columns else []
    return render_template('compare.html', cities=cities)

@app.route('/api/city-data')
def api_city_data():
    city = request.args.get('city', '').strip()
    df = load_master_data()
    if df.empty or not city:
        return jsonify({'error': 'No city selected'})

    filtered = df[df['city'].str.lower() == city.lower()]
    if filtered.empty:
        return jsonify({'error': 'City not found'})

    total = len(filtered)
    avg_rating = round(filtered['company_rating'].mean(), 2)
    max_rating = float(filtered['company_rating'].max())
    min_rating = float(filtered['company_rating'].min())

    top_10 = filtered.sort_values(by='company_rating', ascending=False).head(10)
    top_names = top_10['company_name'].tolist()
    top_ratings = top_10['company_rating'].tolist()

    ind_counts = filtered['industry'].value_counts().head(5)
    ind_labels = ind_counts.index.tolist()
    ind_values = ind_counts.values.tolist()

    companies_list = filtered[['company_name', 'company_rating', 'other_data']].head(50).to_dict(orient='records')

    return jsonify({
        'total': total,
        'avg_rating': avg_rating,
        'max_rating': max_rating,
        'min_rating': min_rating,
        'top_names': top_names,
        'top_ratings': top_ratings,
        'ind_labels': ind_labels,
        'ind_values': ind_values,
        'companies': companies_list
    })

@app.route('/insights')
def insights():
    df = load_master_data()
    desc_html = df[['company_rating']].describe().to_html(classes='table table-hover table-bordered align-middle text-center bg-white', header=True) if not df.empty else "<p>No data available.</p>"
    return render_template('insights.html', desc_html=desc_html, total_records=len(df))

if __name__ == '__main__':
    app.run(debug=True)