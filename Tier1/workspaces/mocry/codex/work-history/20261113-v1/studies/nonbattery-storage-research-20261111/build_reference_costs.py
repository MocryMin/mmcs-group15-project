"""Extract matched 100 MW / 10 h storage cases from the PNNL public workbook."""
import hashlib
import json
import math
from pathlib import Path

from openpyxl import load_workbook

ROOT = Path(__file__).resolve().parent
WORKBOOK = ROOT.parent / 'equipment-research-20261110-v3.1/evidence/PNNL-cost-performance-2024.xlsx'
SOURCE = 'https://www.pnnl.gov/projects/esgc-cost-performance/download-reports'

TECHNOLOGIES = {
    'PSH': (2023, 'Pumped-storage hydropower; reservoir and powerhouse cost case.'),
    'CAES': (2023, 'Cavern CAES technology benchmark. Match fuel and thermal recovery boundaries before adopting for a fuel-free plant.'),
    'Gravitational': (2021, 'Composite of gravity systems; not the price or performance of the Rudong EVx.'),
    'Thermal': (2023, 'Composite of thermal and liquid-air systems; not a Carrington or SynchroStor quotation.'),
    'Hydrogen': (2021, 'Electrolyser, compression, cavern and fuel-cell system; exclude the shared electrolysis equipment when costing only an add-on.'),
}


def extract():
    book = load_workbook(WORKBOOK, read_only=True, data_only=True)
    table = book['Database']
    header = next(table.iter_rows(max_row=1, values_only=True))
    assert header == ('Technology', 'Year', 'Power_MW', 'Duration_hr', 'Estimate_type',
                      'Parameter_category', 'Parameter', 'Value')
    groups = {}
    for row_number, row in enumerate(table.iter_rows(min_row=2, values_only=True), 2):
        tech, year, power, duration, estimate, category, parameter, value = row
        if tech in TECHNOLOGIES and year == TECHNOLOGIES[tech][0] and (power, duration) == (100, 10):
            group = groups.setdefault((tech, estimate), {})
            assert parameter not in group
            group[parameter] = {'value': value, 'category': category, 'workbook_row': row_number}
    book.close()

    profiles = []
    for tech, (year, boundary) in TECHNOLOGIES.items():
        scenarios = {}
        for estimate in ('Low', 'Point', 'High'):
            cells = groups[(tech, estimate)]
            number = lambda name: cells[name]['value']
            capital = number('Total Installed Cost ($)')
            annual = number('Fixed O&M ($/kW-year)') * 100_000
            life = number('Calendar Life (yrs)')
            if estimate == 'Point':
                components = [
                    detail['value'] * (100_000 if label.endswith('($/kW)') else 1_000_000)
                    for label, detail in cells.items()
                    if detail['category'] == 'Capital Cost' and not label.startswith('Total Installed Cost')
                    and label.endswith(('($/kW)', '($/kWh)'))
                ]
                assert math.isclose(sum(components), capital, abs_tol=2_000), (tech, capital, components)
            scenarios[estimate.lower()] = {
                'installed_capital_USD_reported': capital,
                'fixed_OM_USD_reported_per_year': annual,
                'roundtrip_efficiency': number('RTE (%)'),
                'calendar_life_years': life,
                'primary_DoD': number('Primary DOD (%)'),
                'rest_before_charge_hours': number('Rest Before Charge (hrs)'),
                'rest_after_discharge_hours': number('Rest After Discharge (hrs)'),
                'source_parameters': cells,
            }
        profiles.append(dict(technology=tech, reference_year_in_workbook=year,
            discharge_MW=100, nominal_duration_hours=10, rated_energy_MWh=1000,
            cost_and_technology_boundary=boundary, scenarios=scenarios))
    return dict(source=SOURCE, workbook=str(WORKBOOK.relative_to(ROOT.parent)), worksheet='Database',
        sha256=hashlib.sha256(WORKBOOK.read_bytes()).hexdigest(),
        price_note='Original reported USD and workbook reference years are retained. Convert to the project GBP2020 basis before monetary optimisation.',
        open_fields=['site limits', 'electrical charging capacity', 'daily standing losses',
                     'variable operating cost and fuel boundary', 'project-specific renewal'],
        profiles=profiles)


if __name__ == '__main__':
    data = extract()
    (ROOT / 'REFERENCE_COSTS.json').write_text(json.dumps(data, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    print('Verified and extracted', len(data['profiles']), 'technologies with three estimates each.')
