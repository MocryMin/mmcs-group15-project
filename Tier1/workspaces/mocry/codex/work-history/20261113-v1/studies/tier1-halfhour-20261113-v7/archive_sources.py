"""Make this local numerical study reproducible without its sibling folders."""
from pathlib import Path
import shutil
ROOT=Path(__file__).resolve().parent
files={
 'data-repair-20261104-v2':['repair_data.py','REPAIR_AUDIT.json']+[f'evidence/{k}.json.gz' for k in ['agpt','fuelhh','neso','demand']],
 'tier1-multiproduct-20261110-v6':['configuration.json','inputs/daily_generation_by_fuel.csv','inputs/daily_demand.csv','inputs/wind_farm_generation.csv',
   'results/A_comparable_main_schedule.csv','results/A_comparable_main.json','results/B_comparable_main.json','results/annual_breakdown.csv'],
 'gb-price-stress-20261112':['halfhour-market-index.csv']}
for folder,names in files.items():
    for name in names:
        source=ROOT.parent/folder/name;target=ROOT/'source_data'/folder/name
        target.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(source,target)
print('Archived source files',sum(map(len,files.values())))
