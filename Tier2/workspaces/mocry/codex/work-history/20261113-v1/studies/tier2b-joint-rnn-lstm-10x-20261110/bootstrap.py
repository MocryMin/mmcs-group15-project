"""Freeze current data and the former joint-model validation-selected scope."""
from pathlib import Path
import json
import hashlib

ROOT=Path(__file__).resolve().parent
DATA=ROOT.parent/"tier2b-transformer-10x-20261110"
JOINT=ROOT.parent/"tier2b-nextday-rnn-lstm-20261109"


def main():
    for name in ("inputs/model_daily.csv","inputs/SOURCE_MANIFEST.json","data.py","requirements.txt"):
        p=ROOT/name;p.parent.mkdir(parents=True,exist_ok=True)
        assert not p.exists();p.write_bytes((DATA/name).read_bytes())
    assert hashlib.sha256((ROOT/"inputs/model_daily.csv").read_bytes()).hexdigest()=="addc31ee1e01de947c025eb2b47aa7a09e3680e3ca189ea904edf9bd73fae475"
    (ROOT/"reference").mkdir(exist_ok=True)
    for name in ("scalers.json","splits.csv"):(ROOT/"reference"/name).write_bytes((DATA/name).read_bytes())
    for name in ("run_nextday.py","PROTOCOL.json","results/SELECTION_FROZEN.json"):
        p=ROOT/"reference"/name;p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes((JOINT/name).read_bytes())
    choice=json.loads((ROOT/"reference/results/SELECTION_FROZEN.json").read_text())
    assert choice["RNN"]["lookback"]==28 and choice["LSTM"]["lookback"]==56
    config={m:{"lookback":choice[m]["lookback"],"lr":choice[m]["lr"],"source":"Previous joint next-day validation selection; not the per-target independent smoke windows"} for m in ("RNN","LSTM")}
    (ROOT/"CONFIGS_FROZEN.json").write_text(json.dumps(config,indent=2)+"\n",encoding="utf-8")
    print(json.dumps(config))


if __name__=="__main__":main()
