#!/usr/bin/env bash
set -euo pipefail

base_url="${STRATEGY_REPORT_URL:-http://127.0.0.1:8088}"
scratch="$(mktemp -d)"
trap 'rm -rf "$scratch"' EXIT

cat > "$scratch/demo.srp" <<'SRP'
<策略回測><參數><策略>Smoke</策略><近月代碼>TXF</近月代碼><初始資金>100000</初始資金><最小跳動點>1</最小跳動點><最小跳動金額>200</最小跳動金額></參數><策略交易><Trade index="1" time_stamp="2024/01/02 09:00:00" bs="B" contract="1" price="100"/><Trade index="1" time_stamp="2024/01/03 09:00:00" bs="S" contract="1" price="105"/></策略交易></策略回測>
SRP

python3 - "$scratch/demo.sea" <<'PY'
import sys
import zipfile

toml = '[strategy]\nname="Smoke"\n[params]\n"策略"="Smoke"\n"近月代碼"="TXF"\n"初始資金"="100000"\n"最小跳動點"="1"\n"最小跳動金額"="200"\n'
events = '\n'.join([
    '{"timestamp":"2024-01-02T09:00:00","type":"trade","data":{"instrument_id":"TXF","price":100,"quantity":1,"hedge_id":"1"}}',
    '{"timestamp":"2024-01-03T09:00:00","type":"trade","data":{"instrument_id":"TXF","price":105,"quantity":-1,"hedge_id":"1"}}',
])
with zipfile.ZipFile(sys.argv[1], 'w', zipfile.ZIP_DEFLATED) as archive:
    archive.writestr('demo/strategy.toml', toml)
    archive.writestr('demo/events.jsonl', events)
PY

curl --fail --silent --show-error "$base_url/" | grep -q 'Strategy Report'
curl --fail --silent --show-error "$base_url/api/health" | python3 -c 'import json,sys; assert json.load(sys.stdin)["status"] == "ok"'

for format in srp sea; do
  curl --fail --silent --show-error -F "file=@$scratch/demo.$format" -F 'settings={"mode":"backtest"}' "$base_url/api/report" |
    python3 -c 'import json,sys; r=json.load(sys.stdin); assert r["simple"]["summary"]["net_profit"] == 1000; assert r["compound"]["summary"]["final_capital"] == 101000'
done

printf 'invalid\n' > "$scratch/bad.txt"
status="$(curl --silent --show-error --output /dev/null --write-out '%{http_code}' -F "file=@$scratch/bad.txt" "$base_url/api/report")"
test "$status" = 422
printf 'Strategy Report smoke checks passed at %s\n' "$base_url"
