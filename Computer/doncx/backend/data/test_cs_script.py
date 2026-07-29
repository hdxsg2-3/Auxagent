import sys
sys.path.insert(0, 'e:/火山引擎/gm/Computer/doncx/backend')
from services.llm_service import LLMService

s = LLMService()
result = s.process_customer_service('Hello, I want to know when my order will arrive.', 'amazon')

import json
with open('e:/火山引擎/gm/Computer/doncx/backend/data/test_cs.json', 'w', encoding='utf-8') as f:
    json.dump(result, f, ensure_ascii=False, indent=2)

print('done')
