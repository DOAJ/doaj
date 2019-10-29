#!/usr/bin/env python3
# https://github.com/DOAJ/doajPM/issues/1984

import rstr
import requests
import time
import random

CREEP_AFTER = 10
effective_rate = 1.0

def search_doaj():
    issn = rstr.xeger(r'^\d{4}-\d{3}(\d|X|x){1}$')
    resp = requests.get(f'https://doaj.org/api/v1/search/journals/issn:{issn}')
    print(f'{issn}\t{resp.status_code}')
    return resp.status_code

rl_last_run = 10.0

counter = 0
tick = 0
rates = []

while counter < 500:
    # Rate limiting
    diff = time.time() - rl_last_run
    if diff < 1.0 / float(effective_rate):
        time.sleep(1.0 / effective_rate - diff)
    rl_last_run = time.time()    
    
    resp_code = search_doaj()

    # adjust rate limit accoring to status code
    counter +=1
    adj_rate = effective_rate
    if resp_code == 429:
        adj_rate -= 0.1 * random.random()
        tick = counter
    elif counter >= tick + CREEP_AFTER:
        adj_rate += 0.1 * random.random()
        tick = counter

    # Stop us from waiting an infinite amount of time
    if adj_rate < 0.05:
        effective_rate = 0.05
    else:
        effective_rate = adj_rate

    print(f'rate: {effective_rate:.2f}')
    rates.append(effective_rate)

with open(f'rates_{time.time()}.csv', 'w') as f:
    for l in ['{:.2f}'.format(r) for r in rates]:
        f.write(l + '\n')        
