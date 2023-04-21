#%% Imports

import os
from demail.gmail import SendEmail
import json
import dlogging

logger = dlogging.NewLogger(__file__, use_cd=True)
package_name = os.getenv('package_name')
logger.info(f'beginning package: {package_name}')


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

error_list = ''
warn_list = ''

for x in js['results']:
    if x['status'] == 'success' or x['status'] == 'pass':
        num_success += 1
    elif x['status'] == 'warn':
        num_warn += 1
        logger.warning(x['message'])
        warn_list += x['message'] + '\n\n'
    elif x['status'] == 'error':
        num_error += 1
        logger.critical(x['message'])
        error_list += x['message'] + '\n\n'
    elif x['status'] == 'skipped':
        num_skip += 1
    num_total += 1

elapsed_time = js['elapsed_time']


#%% Send Email

logger.info('Send Email')

if error_list != '':
    to_email_addresses=os.getenv('email_fail')
    subject=f'Error - {package_name}'
else:
    to_email_addresses=os.getenv('email_success')
    subject=f'Success - {package_name}'

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

SendEmail(to_email_addresses=to_email_addresses
                    , subject=subject
                    , body=body
                    , attach_file_address=filepath
                    , user=os.getenv('email_uid')
                    , password=os.getenv('email_pwd')
                    )