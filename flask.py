from flask import Flask, request, render_template, jsonify
import sqlite3
import pickle
import pandas as pd
from flask_cors import CORS
from sqlalchemy import create_engine, MetaData, Table, select, and_, or_

app = Flask(__name__)
CORS(app)

with open('model.pkl', 'rb') as f:
    model, label_encoders = pickle.load(f)

DATABASE_URL = "sqlite:///business_data.db"
engine = create_engine(DATABASE_URL)
metadata = MetaData(bind=engine)
table = Table('your_table_name', metadata, autoload=True)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/add_data', methods=['POST'])
def add_data():
    data = request.get_json()
    df = pd.DataFrame([data])
    
    predictions = model.predict(df)
    df['good_fit_bool'], df['acquisition_chance'], df['failure_chance'], df['exit_amt'], df['exit_time_period_yrs'], df['potential_TAM'], df['2x_prob_1yr'], df['2x_prob_5yr'], df['10x_prob_1yr'], df['10x_prob_5yr'] = predictions[0]
    
    df.to_sql('your_table_name', engine, if_exists='append', index=False)
    
    return jsonify({'message': 'Data added and predictions saved!'})

@app.route('/search', methods=['GET'])
def search():
    # Extract all parameters from request
    params = request.args

    # Dynamic SQL query building
    conditions = []

    if 'q' in params:
        search_query = params['q']
        conditions.append(or_(table.c.first_name.contains(search_query), table.c.last_name.contains(search_query), table.c.company_bio.contains(search_query), table.c.company_name.contains(search_query)))

    if 'age_range' in params:
        min_age, max_age = map(int, params['age_range'].split('-'))
        conditions.append(table.c.age.between(min_age, max_age))
    
    if 'yoe_range' in params:
        min_yoe, max_yoe = map(int, params['yoe_range'].split('-'))
        conditions.append(table.c.YOE.between(min_yoe, max_yoe))
    
    if 'college_bool' in params:
        conditions.append(table.c.college_bool == int(params['college_bool']))

    if 'uni_tier' in params:
        conditions.append(table.c.uni_tier.in_(params.getlist('uni_tier')))
    
    if 'industry' in params:
        conditions.append(table.c.industry == params['industry'])

    if 'sector' in params:
        conditions.append(table.c.sector == params['sector'])

    if 'city' in params:
        conditions.append(table.c.city == params['city'])

    if 'country' in params:
        conditions.append(table.c.country == params['country'])

    if 'valuation_range' in params:
        min_valuation, max_valuation = map(int, params['valuation_range'].split('-'))
        conditions.append(table.c.valuation.between(min_valuation, max_valuation))

    if 'profitable' in params:
        conditions.append(table.c.profitable == int(params['profitable']))

    if 'growth_rate' in params:
        conditions.append(table.c.growth_rate == int(params['growth_rate']))

    if 'funding_round' in params:
        conditions.append(table.c.funding_round == int(params['funding_round']))

    query = select([table]).where(and_(*conditions))
    result = engine.execute(query)
    companies = [dict(row) for row in result]

    return jsonify(companies)

@app.route('/profile/<company_name>')
def company_profile(company_name):
    query = select([table]).where(table.c.company_name == company_name)
    result = engine.execute(query).fetchone()

    if result:
        return jsonify(dict(result))
    else:
        return jsonify({'error': 'Company not found'}), 404

if __name__ == '__main__':
    app.run(debug=True)
