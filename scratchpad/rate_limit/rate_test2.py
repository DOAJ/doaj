#!/usr/bin/env python3
# https://github.com/DOAJ/doajPM/issues/1984#issuecomment-493055146

import rstr
import requests
import time

counter = 0

with open(f'codes_555.csv', 'w') as f:
    while counter < 100:
        time.sleep(0.555)    
        issn = rstr.xeger(r'^\d{4}-\d{3}(\d|X|x){1}$')
        resp = requests.get(f'https://doaj.org/api/v1/search/journals/issn:{issn}')
        
        print(f'{issn}\t{resp.status_code}')
        f.write(f'{time.clock()}, {resp.status_code}\n')        
        counter += 1
