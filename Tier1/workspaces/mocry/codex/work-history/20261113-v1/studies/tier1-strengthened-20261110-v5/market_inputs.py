"""Extract the UK demand envelope from the downloaded Observatory workbooks."""
import calendar
import hashlib
import json
from pathlib import Path

import pandas as pd
from openpyxl import load_workbook

ROOT = Path(__file__).resolve().parent


def build():
    records = []
    sources = []
    for year in (2022, 2023, 2024):
        path = ROOT / 'evidence' / f'hydrogen-demand-{year}-update2025.xlsx'
        sheet = load_workbook(path, read_only=True, data_only=True)['Annual consumption aggregated']
        assert [sheet.cell(7, c).value for c in range(2, 9)] == [
            'Country', 'End-use', 'Number of plants', 'Clean consumption T/Y',
            'Other consumption T/Y', 'Total consumption', 'Year']
        for rownum, row in enumerate(sheet.iter_rows(max_col=8, values_only=True), start=1):
            if row[1] == 'United Kingdom':
                assert row[7] == year
                clean, other, total = float(row[4] or 0), float(row[5] or 0), float(row[6])
                assert abs(total - clean - other) < 1e-7
                records.append(dict(year=year, country=row[1], end_use=row[2],
                                    clean_tonnes=clean, other_tonnes=other, total_tonnes=total,
                                    workbook=path.name, sheet=sheet.title, excel_row=rownum))
        sources.append(dict(year=year, file='evidence/' + path.name,
                            sha256=hashlib.sha256(path.read_bytes()).hexdigest(),
                            url=f'https://observatory.clean-hydrogen.europa.eu/sites/default/files/2025-09/'
                                f'Hydrogen%20demand%20{year}%20%28Update%202025%29.xlsx'))
    detail = pd.DataFrame(records)
    annual = detail.groupby('year')[['clean_tonnes', 'other_tonnes', 'total_tonnes']].sum().reset_index()
    annual['calendar_days'] = annual.year.map(lambda y: 366 if calendar.isleap(int(y)) else 365)
    annual['average_tonnes_per_day'] = annual.total_tonnes / annual.calendar_days
    # A deliberately broad national displacement envelope, not an estimated customer order.
    cap = float(annual.average_tonnes_per_day.max() * 1000)
    assert len(detail) == 24
    detail.to_csv(ROOT / 'research' / 'uk_hydrogen_end_uses.csv', index=False)
    annual.to_csv(ROOT / 'research' / 'uk_hydrogen_annual_demand.csv', index=False)
    definition = dict(
        source='European Hydrogen Observatory; 2025 update; UK annual consumption 2022–2024',
        source_page='https://observatory.clean-hydrogen.europa.eu/hydrogen-landscape/end-use/hydrogen-demand',
        status='research-derived national upper-envelope scenario, not a verified local daily maximum',
        national_smooth_cap_kg_day=cap,
        selection='maximum published annual UK consumption estimate divided by actual calendar days',
        temporal_assumption='smooth daily absorption; annual averages do not establish physical daily peaks',
        commercial_assumption='all national end uses are potentially replaceable in the upper-envelope case; '
                              'no claim that captive consumption or this volume is available at the assumed netback',
        upper_envelope_share=1.0,
        sensitivity_shares=[.001, .01, .1, 1.0],
        clean_consumption_scope='reported clean subset is a different market-scale indicator, not the capacity of '
                                'all possible new clean-hydrogen buyers',
        sources=sources, annual=annual.to_dict('records'))
    (ROOT / 'research' / 'market_cap.json').write_text(
        json.dumps(definition, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    return cap


if __name__ == '__main__':
    print('NATIONAL_UPPER_ENVELOPE_KG_DAY', build())
