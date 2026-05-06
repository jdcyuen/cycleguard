import json
import re

text = "FDRXX** $37,249.32 SNDK $5,754.66 MU $3,212.52 WDC $3,102.81 SMH $28,239.89 AAPL $6,562.00 IEMG $5,899.12 FBTC $20,815.63 FTEC $23,455.94 GOOG $12,178.66 ICVT $36,912.00 FZILX $11,930.45 VYMI $6,394.48 IAUM $26,520.74 FZROX $115,875.12 SCHD $108,980.86 SCHG $36,619.53 JEPQ $23,052.88 COST $8,209.62 FXNAX $99,573.33 DBMF $38,146.86 VUSB $41,723.94 BINC $56,253.25 IBID $20,076.54 SGOV $82,142.40 IBIC $20,091.88 IBIE $20,076.09 IBIF $20,083.56 IBIG $20,083.46 JEPI $27,438.82 CLS $13,457.00 NVDA $5,873.97 Pending activity ($3,215.00)"

matches = re.findall(r'([A-Za-z]+)\*?\*?\s+\$?([\d,]+\.\d{2})', text)
portfolio = {}
for k, v in matches:
    if k.lower() == 'activity': continue
    portfolio[k] = float(v.replace(',', ''))

with open('e:/CycleGuard/src/data/portfolio_state.json', 'w') as f:
    json.dump(portfolio, f, indent=2)

print('Portfolio Updated:', portfolio)
