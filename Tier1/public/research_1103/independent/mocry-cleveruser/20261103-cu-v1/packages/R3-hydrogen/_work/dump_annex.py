import openpyxl

wb = openpyxl.load_workbook('h2_production_costs_2021_annex.xlsx', read_only=True, data_only=True)

def dump(name, maxrow=90, maxcol=14):
    ws = wb[name]
    print("=====", name, ws.max_row, ws.max_column)
    for r, row in enumerate(ws.iter_rows(min_row=1, max_row=min(maxrow, ws.max_row),
                                         max_col=maxcol, values_only=True), 1):
        cells = ["" if c is None else (round(c, 4) if isinstance(c, float) else str(c))
                 for c in row]
        line = " | ".join(str(c) for c in cells).strip()
        if line.strip(" |"):
            print(r, line[:300])

dump('Technical and cost assumptions', 120, 12)
dump('2020_E', 70, 12)
