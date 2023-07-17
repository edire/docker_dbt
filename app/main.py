#%% Imports

import os
from demail.gmail import SendEmail
import json
import dlogging
import pandas as pd
from ddb.bigquery import SQL
from datetime import datetime as dt


logger = dlogging.NewLogger(__file__, use_cd=True)
package_name = os.getenv('package_name')
logger.info(f'beginning package: {package_name}')
current_time = dt.now()


#%% Bigquery Connection Info

logger.info('Bigquery Connection Info')

con = SQL(os.getenv('dbt_keyfile'))
dataset = os.getenv('dataset')
name = f'{dataset}_stage.dbt_run_results'


#%% Read In Results

logger.info('Read In Results')

current_filepath = os.path.dirname(os.path.abspath(__file__))
filepath = os.path.join(current_filepath, os.getenv('git_dir'), 'target', 'run_results.json')
with open(filepath, 'r') as f:
    js = f.read()
js = json.loads(js)


#%% Parse Results

logger.info('Parse Results')

num_success = 0
num_warn = 0
num_error = 0
num_skip = 0
num_total = 0
bytes_processed = 0

error_list = ''
warn_list = ''

for x in js['results']:
    if x['status'] == 'success' or x['status'] == 'pass':
        num_success += 1
    elif x['status'] == 'warn':
        num_warn += 1
        logger.warning(x['unique_id'] + ' - ' + x['message'])
        warn_list += x['unique_id'] + ' - ' + x['message'] + '\n\n'
    elif x['status'] == 'error':
        num_error += 1
        logger.critical(x['unique_id'] + ' - ' + x['message'])
        error_list += x['unique_id'] + ' - ' + x['message'] + '\n\n'
    elif x['status'] == 'skipped':
        num_skip += 1
    try:
        bytes_processed += x['adapter_response']['bytes_processed']
    except:
        pass
    num_total += 1

elapsed_time = js['elapsed_time']


#%% Check Send Email

logger.info('Check Send Email')
send_email = None

if error_list != '':
    logger.info('Error Email Required')
    send_email = 'error'
elif str(current_time.hour) in os.getenv('send_summary_hr').split(',') and current_time.minute <= int(os.getenv('send_summary_minute')):
    logger.info('Summary Email Required')
    send_email = 'summary'
else:
    logger.info('No Email Required')


#%% Store results in SQL

logger.info('Store results in SQL')

results_dict = {
    'package': package_name,
    'results_time': current_time,
    'is_success': 1 if num_success == num_total else 0,
    'num_success': num_success,
    'num_warn': num_warn,
    'num_error': num_error,
    'num_skip': num_skip,
    'num_total': num_total,
    'elapsed_time': elapsed_time,
    'errors': error_list,
    'warnings': warn_list,
    'gb_processed': round(bytes_processed / (1000 ** 3), 1),
    'send_email': 1 if send_email != None else 0
}

df = pd.DataFrame.from_dict(results_dict, orient='index').T
df = df.infer_objects()
con.to_sql(df, name, if_exists='append', index=False)


#%% Send Email

if send_email == 'error':
    logger.info('Send Error Email')
    to_email_addresses=os.getenv('email_fail')
    subject=f'Error - {package_name}'
    body = [
        f'Total Elapsed Time: {elapsed_time}'
        , '<br>'
        , f'PASS={num_success}   WARN={num_warn}   ERROR={num_error}   SKIP={num_skip}   TOTAL={num_total}'
        , '<br>'
        , 'Errors:'
        , error_list
        , '<br><br>'
        , 'Warnings:'
        , warn_list
        ]
    attach_file_address=filepath
    
elif send_email == 'summary':
    logger.info('Send Summary Email')
    to_email_addresses=os.getenv('email_success')
    subject=f'dbt summary'

    sql = f"""
        select *
        from {name}
        where results_time >= date_add(CURRENT_DATETIME, INTERVAL -24 HOUR)
        order by results_time desc
        """
    df_summary = con.read(sql)
    body = df_summary.to_html().replace('\n', '')
    attach_file_address=None


if send_email != None:
    SendEmail(to_email_addresses=to_email_addresses
                        , subject=subject
                        , body=body
                        , attach_file_address=attach_file_address
                        , user=os.getenv('email_uid')
                        , password=os.getenv('email_pwd')
                        )