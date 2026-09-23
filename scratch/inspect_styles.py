with open('frontend/static/css/style.css', 'r', encoding='utf-8') as f:
    css = f.read()

import re

elements_to_check = [
    'modal-backdrop', 'modal-dialog', 'node-details-drawer', 'card-panel',
    'graph-panel', 'finding-card', 'tabs-nav', 'recon-terminal', 'bento-ledger'
]

for el in elements_to_check:
    matches = re.findall(rf'(\.{el}[^{{]*\{{[^}}]+\}})', css)
    print(f"=== {el} ===")
    for m in matches[:3]:
        print(m[:250])
        print()
