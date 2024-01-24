from flask import Flask, request, jsonify
import pandas as pd

import datetime
from datetime import datetime


app = Flask(__name__)


class AgricultureCommoditySystem:
    def __init__(self):
        self.transactions = {}  # To store daily transactions
        self.inventory = {}  # To store daily closing stock of commodities
        self.prices = {}  # To store daily prices of commodities
        self.cash_inflow_outflow = {}  # To store daily cash inflow/outflow

    def record_transaction(self, date, quantities):
        self.transactions[date] = quantities
        self.update_inventory(date)

    def update_inventory(self, date):
        if date not in self.transactions:
            return

        if date not in self.inventory:
            self.inventory[date] = {}
        previous_date = pd.Timestamp(date) - pd.Timedelta(days=1)
        if previous_date in self.inventory:
            # Use the closing stock from the previous day as opening stock for the current day
            opening_stock = self.inventory[previous_date]
            self.inventory[date] = opening_stock.copy()
            
        for commodity, quantity in self.transactions[date].items():
            if commodity not in self.inventory[date]:
                self.inventory[date][commodity] = quantity
            else:
                self.inventory[date][commodity] += quantity

    def record_daily_prices(self, date, prices):
        self.prices[date] = prices

    def record_cash_inflow_outflow(self, date, cash_values):
        if date not in self.cash_inflow_outflow:
            self.cash_inflow_outflow[date] = {}

        for i, commodity in enumerate(cash_values.index):
            cash_flow = cash_values.iloc[i]
            if commodity not in self.cash_inflow_outflow[date]:
                self.cash_inflow_outflow[date][commodity] = {'cash_inflow': 0, 'cash_outflow': 0}
            if cash_flow >= 0:
                self.cash_inflow_outflow[date][commodity]['cash_inflow'] += cash_flow
            else:
                self.cash_inflow_outflow[date][commodity]['cash_outflow'] += abs(cash_flow)


    def add_new_commodity(self, commodity_name):
        for date in self.transactions:
            if commodity_name not in self.transactions[date]:
                self.transactions[date][commodity_name] = 0
                self.update_inventory(date)

        # Set initial price to 0 for the new commodity
        for date in self.prices:
            self.prices[date][commodity_name] = 0

        # Set initial cash inflow/outflow to 0 for the new commodity
        for date in self.cash_inflow_outflow:
            if commodity_name not in self.cash_inflow_outflow[date]:
                self.cash_inflow_outflow[date][commodity_name] = {'cash_inflow': 0, 'cash_outflow': 0}



    # Inside the calculate_daily_profit_loss method
    def calculate_daily_profit_loss(self, input_date):
        print(f"Calculating daily profit/loss for date: {input_date}")
        try:
            date_str = input_date.strftime('%Y-%m-%d')
        except ValueError:
            print("Invalid date format. Please use the format 'YYYY-MM-DD'.")
            return {}
        date_timestamp = pd.to_datetime(date_str, format='%Y-%m-%d')

        if date_timestamp not in self.transactions or date_timestamp not in self.prices or date_timestamp not in self.cash_inflow_outflow:
            print("Data not available for the specified date.")
            return {}

        previous_date = date_timestamp - pd.Timedelta(days=1)
        opening_stock = self.inventory.get(previous_date, {})
        total_daily_profit_loss = 0
        result = {'date': date_str, 'items': []}

        for commodity, quantity in self.transactions[date_timestamp].items():
            closing_stock = opening_stock.get(commodity, 0) 
            daily_price = self.prices[date_timestamp].get(commodity, 0)
            inflow_outflow = quantity * daily_price
            total_daily_profit_loss += inflow_outflow

            result['items'].append({
                'commodity': commodity,
                'closing_stock': int(closing_stock),
                'daily_price': float(daily_price),
                'inflow_outflow': float(inflow_outflow)
            })
        # print("self.cash_inflow_outflow==",self.cash_inflow_outflow)
        result['total_profit_loss'] = float(total_daily_profit_loss)
        timestamp_object = pd.Timestamp(date_timestamp)
        # Access the dictionary using the Timestamp object
        inner_dict = self.cash_inflow_outflow.get(timestamp_object, {})
        result['cash_inflow'] = float(inner_dict['Date']['cash_inflow'])
        result['cash_outflow'] = float(inner_dict['Date']['cash_outflow'])
        print("Calculation result:", result)
        return jsonify(result)

    def calculate_total_profit_loss(self):
        total_period_profit_loss = 0
        total_cash_inflow = 0
        total_cash_outflow = 0
        result = {'total_items': []}
        for date_timestamp in self.transactions:
            total_daily_profit_loss = 0
            daily_items = {'date': date_timestamp.strftime('%Y-%m-%d'), 'items': []}
            for commodity, quantity in self.transactions[date_timestamp].items():
                closing_stock = self.inventory[date_timestamp].get(commodity, 0)
                daily_price = self.prices[date_timestamp].get(commodity, 0)
                inflow_outflow = quantity * daily_price
                total_daily_profit_loss += inflow_outflow

                daily_items['items'].append({
                    'commodity': commodity,
                    'closing_stock': closing_stock,
                    'daily_price': daily_price,
                    'inflow_outflow': inflow_outflow
                })

            daily_items['total_profit_loss'] = total_daily_profit_loss
            inner_dict = self.cash_inflow_outflow.get(date_timestamp, {})
            daily_items['cash_inflow'] = float(inner_dict.get('Date', {}).get('cash_inflow', 0))
            daily_items['cash_outflow'] = float(inner_dict.get('Date', {}).get('cash_outflow', 0))

            result['total_items'].append(daily_items)
            total_period_profit_loss += total_daily_profit_loss
            total_cash_inflow += daily_items['cash_inflow']
            total_cash_outflow += daily_items['cash_outflow']

        result['total_period_profit_loss'] = total_period_profit_loss
        result['total_cash_inflow'] = total_cash_inflow
        result['total_cash_outflow'] = total_cash_outflow
        result_df = pd.DataFrame(result['total_items'])
        return result_df


def read_excel_data(file_path):
    # Read data from Excel file
    df_quantity = pd.read_excel(file_path, sheet_name='Quantity', index_col='Date')
    df_average_price = pd.read_excel(file_path, sheet_name='Avegrage Price', index_col='Date')
    df_cash_inflow_outflow = pd.read_excel(file_path, sheet_name='Calculation Inflow Outflow', index_col=0)
    # If the date column is not named, assign a default name 'Date'
    if 'Date' not in df_cash_inflow_outflow.columns:
        df_cash_inflow_outflow = df_cash_inflow_outflow.rename(columns={df_cash_inflow_outflow.columns[0]: 'Date'})
    return df_quantity, df_average_price, df_cash_inflow_outflow

agriculture_system = AgricultureCommoditySystem()

@app.route('/load_excel_data', methods=['POST'])
def load_excel_data():
    req_data = request.get_json()
    file_path = req_data['file_path']

    # Read data from Excel file
    df_quantity, df_average_price, df_cash_inflow_outflow = read_excel_data(file_path)


    # Record transactions
    for date, row in df_quantity.iterrows():
        transactions_data = {commodity: row[commodity] for commodity in row.index}
        agriculture_system.record_transaction(date, transactions_data)

    for date, row in df_average_price.iterrows():
        prices_data = {commodity: row[commodity] for commodity in row.index}
        agriculture_system.record_daily_prices(date, prices_data)    

    for date, row in df_cash_inflow_outflow.iterrows():
        agriculture_system.record_cash_inflow_outflow(date, row)


    return jsonify({'message': 'Data loaded successfully'})

@app.route('/daily_profit_loss', methods=['GET'])
def get_daily_profit_loss():
    date_str = request.args.get('date')
    if not date_str:
        return jsonify({'error': 'Date parameter is missing or invalid.'})
    try:
        date = pd.Timestamp(date_str)
    except ValueError:
        return jsonify({'error': 'Invalid date format. Please use the format YYYY-MM-DD.'})

    print("Received date parameter:", date) 
    result = agriculture_system.calculate_daily_profit_loss(date)
    return result


@app.route('/total_profit_loss', methods=['GET'])
def get_total_profit_loss():
    result = agriculture_system.calculate_total_profit_loss()
    json_result = result.to_json(orient='records')
    return json_result

@app.route('/add_commodity', methods=['POST'])
def add_commodity():
    req_data = request.get_json()
    commodity_name = req_data.get('commodity_name')

    if not commodity_name:
        return jsonify({'error': 'Commodity name is missing in the request.'})

    agriculture_system.add_new_commodity(commodity_name)

    return jsonify({'message': f'Commodity {commodity_name} added successfully.'})

if __name__ == '__main__':
    app.run(debug=True)


