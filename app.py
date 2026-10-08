from flask import Flask, render_template, request
import pandas as pd
import os

app = Flask(__name__)
MASTER_PATH = 'processed_data/master_ambitionbox.csv'

def load_master_data():
    if os.path.exists(MASTER_PATH):
        df = pd.read_csv(MASTER_PATH)
        # Parse industry from other_data if not already present
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
    
    selected_city = request.args.get('city', '').strip()
    companies = []
    stats = {}
    
    # 1. Global City-Level Comparison Data (Fixed Charts)
    city_avg = df.groupby('city')['company_rating'].mean().round(2).reset_index()
    city_counts = df.groupby('city')['company_name'].count().reset_index()
    
    city_labels = city_avg['city'].tolist()
    city_ratings = city_avg['company_rating'].tolist()
    city_counts_list = city_counts['company_name'].tolist()

    # 2. Dynamic City-Specific Data (Triggered on Search)
    top_companies_names = []
    top_companies_ratings = []
    industry_labels = []
    industry_counts = []

    if selected_city:
        filtered = df[df['city'].str.lower() == selected_city.lower()]
        if not filtered.empty:
            companies = filtered.to_dict(orient='records')
            stats['total'] = len(filtered)
            stats['avg_rating'] = round(filtered['company_rating'].mean(), 2)

            # Top 10 Highest Rated Companies in this City
            top_10 = filtered.sort_values(by='company_rating', ascending=False).head(10)
            top_companies_names = top_10['company_name'].tolist()
            top_companies_ratings = top_10['company_rating'].tolist()

            # Industry Breakdown for this City
            ind_counts = filtered['industry'].value_counts().head(5)
            industry_labels = ind_counts.index.tolist()
            industry_counts = ind_counts.values.tolist()

    return render_template('index.html',
                           cities=cities,
                           selected_city=selected_city,
                           companies=companies,
                           stats=stats,
                           city_labels=city_labels,
                           city_ratings=city_ratings,
                           city_counts=city_counts_list,
                           top_companies_names=top_companies_names,
                           top_companies_ratings=top_companies_ratings,
                           industry_labels=industry_labels,
                           industry_counts=industry_counts)

if __name__ == '__main__':
    app.run(debug=True)