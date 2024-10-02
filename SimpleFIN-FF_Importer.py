import requests
import json
import csv
from datetime import datetime, timedelta
import subprocess

# Variables
simplefin_username = '-INSERT USERNAME-'
simplefin_password = '-INSERT PASSWORD-'
csvfile = '/PATH/TO/CREATED_FILE.CSV'
importrules = '/PATH/TO/FIREFLY/IMPORT_RULES.JSON'

# Get current time
current_time = datetime.now()

# Calculate time 7 days ago
seven_days_ago = current_time - timedelta(days=3)

# Convert to epoch time
epoch_time = int(seven_days_ago.timestamp())

# URL of the webpage you want to scrap
url = f'https://{simplefin_username}:{simplefin_password}@beta-bridge.simplefin.org/simplefin/accounts?start-date={epoch_time}'

# Send an HTTP GET request to the URL
response = requests.get(url)

# Check if the request was successful (status code 200)
if response.status_code == 200:
    # Get the content of the response
    webpage_content = response.text

    # Convert to CSV

    # Read the JSON file
    #with open('data.json', 'r') as json_file:
    data = json.loads(webpage_content)

    # Extract the list of accounts from the 'accounts' key
    accounts = data.get('accounts', [])

    # Function to convert epoch time to YYYY-MM-DD format
    def convert_epoch_to_date(epoch_time):
        return datetime.utcfromtimestamp(epoch_time).strftime('%Y-%m-%d')

    # Open a CSV file for writing
    with open(f'{csvfile}', 'w', newline='') as csv_file:
        if accounts:
            # Define the CSV headers
            headers = [
                'account_id', 'account_name', 'account_currency', 'account_balance',
                'transaction_id', 'transaction_date', 'transaction_posted', 'transaction_amount', 'transaction_description', 'transaction_payee', 'transaction_memo'
            ]
            csv_writer = csv.DictWriter(csv_file, fieldnames=headers)
            csv_writer.writeheader()

            # Write the data rows
            for account in accounts:
                account_info = {
                    'account_id': account.get('id'),
                    'account_name': account.get('name'),
                    'account_currency': account.get('currency'),
                    'account_balance': account.get('balance')
                }
                # If there are transactions, break them out
                for transaction in account.get('transactions', []):
                    # Added to dal with reinvestment account from one of the banks I use
                    if transaction.get('description') != 'REINVESTMENT CASH (XXXXXXXXX) (Cash) Cash':
                        transaction_posted = convert_epoch_to_date(transaction.get('posted')) if transaction.get('posted') else ''
                        transaction_date = convert_epoch_to_date(transaction.get('transacted_at')) if transaction.get('transacted_at') else ''
                        transaction_info = {
                            'transaction_id': transaction.get('id'),
                            'transaction_date': transaction_date,
                            'transaction_posted': transaction_posted,
                            'transaction_amount': transaction.get('amount'),
                            'transaction_description': transaction.get('description'),
                            'transaction_payee': transaction.get('payee'),
                            'transaction_memo': transaction.get('memo')
                        }
                        # Combine account info with transaction info
                        if transaction_info['transaction_id']:  # Only write if transaction_id is not blank
                            row = {**account_info, **transaction_info}
                            csv_writer.writerow(row)

    print("JSON to CSV conversion complete.")
    print("Staring import in to Firefly III.")

    # Define the command to be executed
    command = [
        'docker', 'exec',
        'firefly_iii_importer',
        'php', 'artisan',
        'importer:import',
        '/import/import.json',
        '/import/importme.csv'
    ]

    # Run the command
    result = subprocess.run(command, capture_output=True, text=True)

    # Check the result
    if result.returncode == 0:
        print("Command executed successfully!")
        print("Output:", result.stdout)
    else:
        print("Command failed with return code:", result.returncode)
        print("Error:", result.stderr)

else:
    print(f"Failed to retrieve the webpage. Status code: {response.status_code}")
