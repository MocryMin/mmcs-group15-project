import os, csv, json, re

PKG = r'.cc-scratch/tier2b/v12/pkg'
ME = os.path.join(PKG, 'model-evidence')
EV = os.path.join(PKG, 'evidence')
OUT = r'.cc-scratch/tier2b/v12/checks'
os.makedirs(OUT, exist_ok=True)
checks = []

def add(name, expected, got, ok, note=''):
    checks.append({'check': name, 'expected': expected, 'got': got, 'ok': bool(ok), 'note': note})

def rd(p):
    with open(p, encoding='utf-8', newline='') as fh:
        return list(csv.DictReader(fh))

def fl(x):
    try:
        return float(x)
    except Exception:
        return 0.0

def close(a, b, tol):
    try:
        return abs(float(a) - float(b)) <= tol + 1e-12
    except Exception:
        return False

# ================= Table III.1: independent recomputation from evidence ledgers =================
rep = rd(os.path.join(EV, 'replays.csv'))
pinfo = rd(os.path.join(EV, 'plant-information.csv'))

def means(rows, key):
    n = len(rows)
    return {c: sum(fl(r.get(c, 0)) for r in rows) / n for c in key}

def sel(rows, policy, case, blocks=None):
    out = [r for r in rows if r['policy'] == policy and r['case'] == case and (blocks is None or r['blocks'] == blocks)]
    return out

COLS = ['gross_battery_GBP', 'battery_annual_equiv_cost_GBP', 'net_battery_GBP', 'plant_cost_GBP',
        'portfolio_net_GBP', 'delivered_MWh', 'demand_MWh', 'unused_MWh', 'renewable_capture_MWh',
        'renewable_surplus_MWh', 'hydrogen_t']
pf = sel(pinfo, 'A', 'plant_forecast_forecast')
po = sel(pinfo, 'A', 'plant_oracle')
m_pf, m_po = means(pf, COLS), means(po, COLS)
PLANT = m_pf['plant_cost_GBP']
base_gross = m_pf['portfolio_net_GBP'] + PLANT  # hydrogen receipts plus change in electricity sales

# printed Table III.1 rows: (label, ledger policy, case, blocks, plant?, gross, batt, net, served%, unused GWh, capture GWh, H2 kt)
rows31 = [
    ('A: plant, forecast',      None, None, None, True,  16.49, 0.00, 11.95, 89.980, 7962.0, 28.7, 3.40),
    ('A: plant, foresight',     None, None, None, True,  17.47, 0.00, 12.93, 89.506, 9167.0, 31.0, 3.40),
    ('A: reactive rule',        'A', 'reactive', '1',     True,  20.74, 4.70, 11.50, 89.995, 7919.5, 48.5, 3.40),
    ('A: rolling forecast',     'A', 'selected', '1',     True,  21.96, 4.70, 12.72, 89.989, 7927.1, 44.7, 3.40),
    ('A: 12 h truth paths',     'A', 'twelve_hour_truth', '1', True, 25.48, 4.70, 16.24, 89.998, 7901.2, 56.9, 3.40),
    ('A: rolling forecast 11',  'A', 'selected', '11',    True,  71.96, 51.67, 15.75, 90.061, 7625.4, 182.1, 3.41),
    ('B: direct sales',         'B', 'direct', '0',       False,  0.00, 0.00,  0.00, 90.934, 5725.1, 0.0, 0.00),
    ('B: previous slot',        'B', 'previous_slot', '1',False,  6.16, 4.70,  1.46, 90.957, 5662.4, 28.0, 0.00),
    ('B: classifier',           'B', 'selected', '1',     False,  5.96, 4.70,  1.26, 90.956, 5663.1, 27.8, 0.00),
    ('B: true surplus sign',    'B', 'truth_gate', '1',   False,  6.83, 4.70,  2.13, 90.961, 5651.4, 32.9, 0.00),
    ('B: classifier 11',        'B', 'selected', '11',    False, 58.50, 51.67,  6.83, 91.147, 5124.2, 270.8, 0.00),
]
for label, pol, case, blocks, is_plant, gross_p, batt_p, net_p, served_p, unused_p, cap_p, h2_p in rows31:
    if is_plant and case is None:
        m = m_pf if 'forecast' in label else m_po
    else:
        rs = sel(rep, pol, case, blocks)
        if not rs:
            add(f'III.1 {label}', 'ledger rows', 'none', False); continue
        m = means(rs, COLS)
    gross = (m['portfolio_net_GBP'] - m['net_battery_GBP'] + m['gross_battery_GBP']
             + (m['plant_cost_GBP'] if pol in (None, 'A') else 0)) / 1e6
    net = m['portfolio_net_GBP'] / 1e6
    batt = m['battery_annual_equiv_cost_GBP'] / 1e6
    served = m['delivered_MWh'] / m['demand_MWh'] * 100
    unused = m['unused_MWh'] / 1000
    cap = m['renewable_capture_MWh'] / 1000
    h2 = m['hydrogen_t'] / 1000
    got = (round(gross, 2), round(batt, 2), round(net, 2), round(served, 3), round(unused, 1), round(cap, 1), round(h2, 2))
    ok = (close(gross_p, gross, 0.006) and close(batt_p, batt, 0.006) and close(net_p, net, 0.006)
          and close(served_p, served, 0.0015) and close(unused_p, unused, 0.06)
          and close(cap_p, cap, 0.06) and close(h2_p, h2, 0.006))
    add(f'III.1 recompute {label} (gross/batt/net/served/unused/capture/H2)', 
        (gross_p, batt_p, net_p, served_p, unused_p, cap_p, h2_p), got, ok,
        f'n={len(pf) if (is_plant and case is None) else len(sel(rep, pol, case, blocks))} windows')

add('III.1 plant cost mean = 4.5413m (6 x 756,537)', 4.5413, round(PLANT / 1e6, 4), close(4.5413, PLANT / 1e6, 5e-5),
    f'ledger plant_cost_GBP mean {PLANT:.0f}')
add('III.1 caption prints the plant cost used in every A row', '4.54', round(PLANT / 1e6, 2), close(4.54, PLANT / 1e6, 0.005))
add('B rows carry zero plant cost', 0.0, round(means(sel(rep, 'B', 'selected', '1'), COLS)['plant_cost_GBP'], 6),
    abs(means(sel(rep, 'B', 'selected', '1'), COLS)['plant_cost_GBP']) < 1e-6)

# every-window claim and 92.4%
pf_net = [fl(r['portfolio_net_GBP']) for r in pf]
add('A plant gain positive in every window', 6, sum(1 for v in pf_net if v > 0), all(v > 0 for v in pf_net),
    f'min {min(pf_net)/1e6:.3f}m max {max(pf_net)/1e6:.3f}m')
add('92.4% of 12.93 = 11.95 (ratio)', 92.42, round(means(pf, COLS)['portfolio_net_GBP'] / means(po, COLS)['portfolio_net_GBP'] * 100, 2),
    close(92.4, means(pf, COLS)['portfolio_net_GBP'] / means(po, COLS)['portfolio_net_GBP'] * 100, 0.05))
add('forecast controller earns 18% of realised-information benchmark (A)',
    '18', round(means(sel(rep,'A','selected','1'), COLS)['net_battery_GBP'] / means(sel(rep,'A','twelve_hour_truth','1'), COLS)['net_battery_GBP'] * 100, 1),
    close(18, means(sel(rep,'A','selected','1'), COLS)['net_battery_GBP'] / means(sel(rep,'A','twelve_hour_truth','1'), COLS)['net_battery_GBP'] * 100, 0.6))
add('previous-slot rule earns 69% of B realised-information benchmark',
    '69', round(means(sel(rep,'B','previous_slot','1'), COLS)['portfolio_net_GBP'] / means(sel(rep,'B','truth_gate','1'), COLS)['portfolio_net_GBP'] * 100, 1),
    close(69, means(sel(rep,'B','previous_slot','1'), COLS)['portfolio_net_GBP'] / means(sel(rep,'B','truth_gate','1'), COLS)['portfolio_net_GBP'] * 100, 0.6))
b0 = means(sel(rep, 'B', 'direct', '0'), COLS); b1 = means(sel(rep, 'B', 'previous_slot', '1'), COLS)
b11 = means(sel(rep, 'B', 'selected', '11'), COLS)
add('one block raises B served demand by 0.02 pp', 0.02,
    round(b1['delivered_MWh']/b1['demand_MWh']*100 - b0['delivered_MWh']/b0['demand_MWh']*100, 3),
    close(0.02, b1['delivered_MWh']/b1['demand_MWh']*100 - b0['delivered_MWh']/b0['demand_MWh']*100, 0.005))
add('eleven blocks raise B served demand by 0.21 pp', 0.21,
    round(b11['delivered_MWh']/b11['demand_MWh']*100 - b0['delivered_MWh']/b0['demand_MWh']*100, 3),
    close(0.21, b11['delivered_MWh']/b11['demand_MWh']*100 - b0['delivered_MWh']/b0['demand_MWh']*100, 0.005))
add('A plant captures 28.7 of 2,911 GWh surplus per window', (28.7, 2911.0),
    (round(m_pf['renewable_capture_MWh']/1000, 1), round(m_pf['renewable_surplus_MWh']/1000, 1)),
    close(2911, m_pf['renewable_surplus_MWh']/1000, 1.0), 'surplus from ledger')

# information decomposition (D.1 / section 2.1)
pfo = means(sel(pinfo, 'A', 'plant_forecast_oracle'), COLS)
pof = means(sel(pinfo, 'A', 'plant_oracle_forecast'), COLS)
base = m_pf['portfolio_net_GBP']
add('D.1 intraday-only (forecast commitment, realised allocation) = 12.80m', 12.80, round(pfo['portfolio_net_GBP']/1e6, 2),
    close(12.80, pfo['portfolio_net_GBP']/1e6, 0.006))
add('D.1 hindsight commitment, forecast allocation = 12.11m', 12.11, round(pof['portfolio_net_GBP']/1e6, 2),
    close(12.11, pof['portfolio_net_GBP']/1e6, 0.006))
add('D.1 averaging first/second order: 0.83 intraday + 0.15 commitment', (0.83, 0.15),
    (round(((pfo['portfolio_net_GBP']-base)+(m_po['portfolio_net_GBP']-pof['portfolio_net_GBP']))/2e6, 2),
     round(((pof['portfolio_net_GBP']-base)+(m_po['portfolio_net_GBP']-pfo['portfolio_net_GBP']))/2e6, 2)),
    close(0.83, ((pfo['portfolio_net_GBP']-base)+(m_po['portfolio_net_GBP']-pof['portfolio_net_GBP']))/2e6, 0.006)
    and close(0.15, ((pof['portfolio_net_GBP']-base)+(m_po['portfolio_net_GBP']-pfo['portfolio_net_GBP']))/2e6, 0.006))

# ================= Table D.2(a) =================
a_exp = {'2M': ('0.1416','0.0011','0.1210','0.0031','0.1139'),
         '10M': ('0.1390','0.0041','0.1196','0.0051','0.1003'),
         '50M': ('0.1351','0.0027','0.1238','0.0014','0.1078'),
         '100M': ('0.1358','0.0028','0.1354','0.0040','0.1132'),
         '200M': ('0.1433','0.0048','0.1313','0.0132','0.1254'),
         '1B': ('0.1604','0.0021','0.1483','0.0039','0.1744')}
size_map = {'2M':2000000,'10M':10000000,'50M':50000000,'100M':100000000,'200M':200000000,'1B':1000000000}
pool = {}
for f, szcol in [('tier2b-gpu-overfit-5m-1b/comparison.csv','target'),
                 ('tier2b-gpu-scale-100m-200m/comparison.csv','size')]:
    for r in rd(os.path.join(ME, f)):
        if r['family'].strip() != 'Transformer':
            continue
        pool.setdefault(int(float(r[szcol])), (f, r))
for label, exp in a_exp.items():
    hit = pool.get(size_map[label])
    if not hit:
        add(f'D.2(a) {label}', exp, 'row missing', False); continue
    f, r = hit
    got = (round(fl(r['val_total_mean']),4), round(fl(r['val_total_std']),4), round(fl(r['test_total_mean']),4),
           round(fl(r['test_total_std']),4), round(fl(r['final_train_mean']),4))
    ok = all(close(e, g, 5e-5) for e, g in zip(exp, got))
    add(f'D.2(a) {label} val mean/sd, Sep-Dec mean/sd, final train', exp, got, ok, os.path.basename(os.path.dirname(f)))

# ================= Table D.2(b) =================
b_exp = {'Ridge': ('0.102','0.1020','0.0810','0.0807'),
         'rnn-2132': ('4.829','0.1215','0.1029','0.0973'),
         'lstm-1060': ('4.829','0.1028','0.0801','0.0868'),
         '1x128': ('0.150','0.1028','0.0805','0.0876'),
         '1x768': ('4.830','0.0838','0.0715','0.0727'),
         '1x864': ('6.097','0.0833','0.0647','0.0728'),
         '1x1024': ('8.537','0.0841','0.0650','0.0765'),
         '2x576': ('5.398','0.0819','0.0682','0.0737'),
         '3x448': ('4.892','0.0826','0.0714','0.0702'),
         '4x768': ('19.011','0.0874','0.0657','0.0769'),
         '8x768': ('37.919','0.0881','0.0703','0.0778')}
seen = {}
for dirpath, _, files in os.walk(os.path.join(ME, 'tier2b-asof-20261119')):
    if 'architecture_comparison.csv' in files:
        for r in rd(os.path.join(dirpath, 'architecture_comparison.csv')):
            if r['horizon'] != '12h':
                continue
            if r['period'] == '2025-09–12':
                seen.setdefault(r['model'], {}).update({'val': r['val_12h_mse'], 'test': r['mse'], 'params': r['parameters']})
            elif r['period'] == '2026-06–08' and 'test' in seen.get(r['model'], {}):
                seen[r['model']]['summer'] = r['mse']
top = {r['model'].strip(): r for r in rd(os.path.join(ME, 'tier2b-asof-20261119/comparison.csv'))}
for r in rd(os.path.join(ME, 'tier2b-asof-20261119/summer-2026/comparison.csv')):
    k = {'Ridge':'Ridge','Transformer 4×768':'4x768','Transformer 8×768':'8x768'}.get(r['model'].strip())
    if k:
        seen.setdefault(k, {})['summer'] = r['new_12h']
for name, exp in b_exp.items():
    rec = dict(seen.get(name, {}))
    if name in top or (name == 'Ridge' and 'ridge' in top):
        _t = top.get(name) or top.get('ridge'); rec.setdefault('val', _t['val']); rec.setdefault('test', _t['test'])
        rec.setdefault('_from_top', True)
    if name == 'Ridge' and 'val' not in rec:
        add(f'D.2(b) {name}', exp, 'not found', False); continue
    if 'val' not in rec or 'summer' not in rec:
        add(f'D.2(b) {name}', exp, 'incomplete', False, str(sorted(rec))); continue
    par = round(fl(rec['params'])/1e6, 3) if rec.get('params') else None
    got = (par, round(fl(rec['val']),4), round(fl(rec['test']),4), round(fl(rec['summer']),4))
    ok = (close(exp[1], rec['val'], 5e-5) and close(exp[2], rec['test'], 5e-5)
          and close(exp[3], rec['summer'], 5e-5) and (par is None or close(exp[0], fl(rec['params'])/1e6, 5e-4)))
    add(f'D.2(b) {name} params/val/Sep-Dec/Jun-Aug', exp, got, ok,
        'params from top-level comparison (author reported)' if par is None else '')

# ================= Figure D.2 =================
for m, (step_exp, mse_exp) in {'1x128': ('1050','0.1028'), '1x768': ('460','0.0838'),
                               '1x864': ('860','0.0833'), '1x1024': ('440','0.0841')}.items():
    d = os.path.join(ME, 'tier2b-asof-20261119', m)
    best = json.load(open(os.path.join(d, 'best.json'), encoding='utf-8'))
    got = (str(best['step']), round(fl(best['validation_mse']), 4))
    add(f'Fig D.2 {m} selected step + validation MSE', (step_exp, mse_exp), got,
        got[0] == step_exp and close(mse_exp, best['validation_mse'], 5e-5))
t = rd(os.path.join(ME, 'tier2b-asof-20261119/1x1024/training.csv'))
last = t[-1]
add('Fig D.2 8.537M final update train/val MSE 0.0657 / 0.0928', ('0.0657','0.0928'),
    (round(fl(last['train_mse']),4), round(fl(last['val_mse']),4)),
    close('0.0657', last['train_mse'], 5e-5) and close('0.0928', last['val_mse'], 5e-5), f"final step {last['step']}")
add('Fig D.2 x-axis 0..1080', (0, 1080), (int(t[0]['step']), int(last['step'])),
    int(t[0]['step']) == 0 and int(last['step']) == 1080, f'{len(t)} points')

# ================= Table D.3 =================
mg = rd(os.path.join(ME, 'tier2b-feature-research-20261119/transformer-tuning-20261119/matched_generation_ablation_scores.csv'))
def mg_get(model, split):
    for r in mg:
        if r['model'] == model and r['split'] == split and r['target'] == 'generation' and r['horizon'] == '24-slot':
            return r
for label, model, exp in [('direct seasonal deviation','ablate_same_2x256_without_ridge',('0.06659','0.06578','0.08267')),
                          ('add Ridge, four heads','a_2deep_c24',('0.06369','0.06342','0.07805')),
                          ('add Ridge, eight heads','match_heads8',('0.06368','0.06138','0.07775'))]:
    got, ok = [], True
    for trip, e in zip(['test25','jan_may26','test26'], exp):
        r = mg_get(model, trip)
        if r is None:
            got.append(None); ok = False; continue
        got.append(round(fl(r['MSE']), 5))
        ok = ok and close(e, r['MSE'], 5e-6)
    add(f'D.3 {label} 12h(=24-slot) generation MSE, 3 periods', exp, tuple(got), ok, model)
py = rd(os.path.join(ME, 'tier2b-feature-research-20261119/transformer-tuning-20261119/pooled_year_scores.csv'))
def py_get(model):
    for r in py:
        if r['model'] == model and r['target'] == 'joint' and r['horizon'] == '24-slot':
            return r
v1, gb, ce = py_get('v1'), py_get('generation_blend'), py_get('component_extension')
add('D.3 pooled joint 24-slot 0.04376 -> 0.04233 -> 0.04110', (0.04376, 0.04233, 0.04110),
    (round(fl(v1['MSE']),5), round(fl(gb['MSE']),5), round(fl(ce['MSE']),5)),
    close(0.04376, v1['MSE'], 5e-6) and close(0.04233, gb['MSE'], 5e-6) and close(0.04110, ce['MSE'], 5e-6))
red = (1 - fl(ce['MSE'])/fl(v1['MSE']))*100
add('D.3 all-v2 branches 6.1% below v1, 95% interval 4.5-7.6%', ('6.1','4.5','7.6'),
    (round(red,2), round(fl(ce['low95_pct']),2), round(fl(ce['high95_pct']),2)),
    close(6.1, red, 0.05) and close(4.5, fl(ce['low95_pct']), 0.05) and close(7.6, fl(ce['high95_pct']), 0.05))

# ================= Table D.4 =================
qp = {r['method']: r for r in rd(os.path.join(ME, 'tier2b-a-quote-residual-20261120/comparison.csv')) if r['window'] == 'pooled'}
for label, key, exp in [('Direct v2 forecast','v2',('10.09','334.2','-45.4')),
                        ('75% v2 + 25% quote','mix_25pct_q',('9.23','379.6','0.0')),
                        ('50% v2 + 50% quote','mix_50pct_q',('8.70','389.7','10.1')),
                        ('25% v2 + 75% quote','mix_75pct_q',('8.59','376.0','-3.6')),
                        ('Quote only','quote',('8.94','273.3','-106.3')),
                        ('Quote plus full Huber residual','best_nonzero_residual',('6.64','223.5','-156.1'))]:
    r = qp.get(key)
    if r is None:
        add(f'D.4 {label}', exp, 'no pooled row', False); continue
    got = (round(fl(r['MAE']),2), round(fl(r['net_GBP'])/1e3,1), round(fl(r['delta_vs_mix_25pct_q_GBP'])/1e3,1))
    add(f'D.4 {label} first-4h MAE / net k / change k', exp, got,
        close(exp[0], r['MAE'], 0.006) and close(exp[1], fl(r['net_GBP'])/1e3, 0.05)
        and close(exp[2], fl(r['delta_vs_mix_25pct_q_GBP'])/1e3, 0.05), key)
asr = {r['method']: r for r in rd(os.path.join(ME, 'tier2b-a-constrained-training-20261121/assessment.csv')) if r['window'] == 'pooled'}
for label, key, exp in [('Partial Huber residual, cash floor','huber_floor',('6.87','428.0','48.4')),
                        ('Partial residual, action penalty','decision_unconstrained',('6.71','425.8','46.2')),
                        ('Partial residual, penalty and floor','decision_floor',('6.89','425.9','46.3'))]:
    r = asr.get(key)
    if r is None:
        add(f'D.4 {label}', exp, 'missing', False); continue
    got = (round(fl(r['MAE']),2), round(fl(r['net_GBP'])/1e3,1), round(fl(r['delta_GBP'])/1e3,1))
    add(f'D.4 {label} MAE / net k / change k', exp, got,
        close(exp[0], r['MAE'], 0.006) and close(exp[1], fl(r['net_GBP'])/1e3, 0.05) and close(exp[2], fl(r['delta_GBP'])/1e3, 0.05), key)
add('D.4 pooled span 363.5 days', 363.5, round(fl(asr['mix_75_25']['days']), 1), close(363.5, asr['mix_75_25']['days'], 1e-6))
add('D.4 50% quote earns +10.1k but paired interval spans zero', '-29.6..47.3',
    (round(fl(qp['mix_50pct_q']['lo95_vs_mix_25pct_q_GBP'])/1e3,1), round(fl(qp['mix_50pct_q']['hi95_vs_mix_25pct_q_GBP'])/1e3,1)),
    close(-29.6, fl(qp['mix_50pct_q']['lo95_vs_mix_25pct_q_GBP'])/1e3, 0.05))

# ================= Table D.5 =================
bt = rd(os.path.join(ME, 'tier2b-b-threshold-loss-20261122/comparison.csv'))
wins = ['test25', 'jan_may26', 'test26']
def pool_b(method):
    rows = [r for r in bt if r['method'] == method and r['window'] in wins]
    if len(rows) != 3:
        return None
    net = sum(fl(r['net_gbp']) for r in rows)/1e6
    slots = sum(fl(r['slots']) for r in rows)
    acc = sum(fl(r['TP'])+fl(r['TN']) for r in rows)/slots*100
    sa = [r['sum_abs'] for r in rows]
    mae = None if any(x in ('', None) for x in sa) else sum(fl(x) for x in sa)/slots
    return round(net,3), round(acc,2), (None if mae is None else round(mae,1))
for label, key, exp in [('History classifier','history_classifier',('1.817','96.34',None)),
                        ('History, Huber','history_anchor_0',('1.629','95.63','287.4')),
                        ('History, Huber + threshold loss (lambda=0.95)','history_anchor_0.95',('1.805','96.27','247.2')),
                        ('History + public features, joint loss','public_last_0.95',('1.677','96.57','234.1')),
                        ('v2 start + public features, Huber','v2_anchor_0',('0.378','93.52','411.9')),
                        ('v2 start + public features, joint loss (lambda=0.15)','v2_anchor_0.15',('0.324','93.40','417.8'))]:
    got = pool_b(key)
    if got is None:
        add(f'D.5 {label}', exp, 'rows missing', False); continue
    ok = close(exp[0], got[0], 0.0005) and close(exp[1], got[1], 0.005) and \
         (exp[2] is None or (got[2] is not None and close(exp[2], got[2], 0.05)))
    add(f'D.5 {label} net m / accuracy / gap MAE MWh', exp, got, ok, key)
h0, h95 = pool_b('history_anchor_0'), pool_b('history_anchor_0.95')
add('D.5 threshold loss adds 176.1k on the history pair', 176.1, round((h95[0]-h0[0])*1000, 1),
    close(176.1, (h95[0]-h0[0])*1000, 0.6))
add('D.5 public-feature history variant earns 140.1k less than classifier',
    140.1, round((pool_b('history_classifier')[0]-pool_b('public_last_0.95')[0])*1000, 1),
    close(140.1, (pool_b('history_classifier')[0]-pool_b('public_last_0.95')[0])*1000, 0.6))

# ================= D.6 =================
dret = rd(os.path.join(ME, 'tier2b-direct-transformer-20261120/returns.csv'))
def dret_pooled(method):
    rows = [r for r in dret if r['method'] == method and r['window'] in wins]
    return None if len(rows) != 3 else sum(fl(r['net_GBP']) for r in rows)/1e6
add('D.6 direct 1x768 policy yields +0.140m in the A pilot', 0.140, round(dret_pooled('1x768_selected'), 3),
    close(0.140, dret_pooled('1x768_selected'), 0.0006))
add('D.6 direct 3x448 policy yields -0.020m', -0.020, round(dret_pooled('3x448_selected'), 3),
    close(-0.020, dret_pooled('3x448_selected'), 0.0006))
lh = [r for r in rd(os.path.join(ME, 'tier2b-a-learned-24h-20261123/comparison.csv')) if r['blocks'] == '25']
lhmap = {r['forecast']: fl(r['net_gbp'])/1e6 for r in lh}
add('D.6 25 blocks: 12h forecast -0.05m, +12h historical means +4.96m, learned 24h -2.38m',
    (-0.05, 4.96, -2.38), (round(lhmap.get('old12'), 2), round(lhmap.get('seasonal24'), 2), round(lhmap.get('learned24'), 2)),
    close(-0.05, lhmap.get('old12'), 0.006) and close(4.96, lhmap.get('seasonal24'), 0.006) and close(-2.38, lhmap.get('learned24'), 0.006))

# ================= calendar bridge =================
cb = {r['case']: r for r in rd(os.path.join(EV, 'calendar-oracle-bridge.csv'))}
c1 = cb.get('Tier 1 calendar horizon'); c2 = cb.get('Tier 2B dates, continuous horizon'); c3 = cb.get('Tier 2B dates, six reset windows')
add('bridge Tier 1 calendar horizon 13.46m/yr over 2192 days', (13.4596, '2192'),
    (round(fl(c1['annual_mean_net_GBP'])/1e6, 4), c1['days']),
    close(13.4596, fl(c1['annual_mean_net_GBP'])/1e6, 5e-5) and c1['days'] == '2192')
add('bridge Tier 2B dates 12.93m/yr, continuous and six resets agree', (12.9256, 12.9256),
    (round(fl(c2['annual_mean_net_GBP'])/1e6, 4), round(fl(c3['annual_mean_net_GBP'])/1e6, 4)),
    close(12.9256, fl(c2['annual_mean_net_GBP'])/1e6, 5e-5) and close(12.9256, fl(c3['annual_mean_net_GBP'])/1e6, 5e-5))
add('bridge Xpress gap zero on all three cases', '0,0,0',
    ','.join(str(round(fl(cb[k]['Xpress_gap_GBP']), 6)) for k in
            ['Tier 1 calendar horizon', 'Tier 2B dates, continuous horizon', 'Tier 2B dates, six reset windows']),
    all(abs(fl(cb[k]['Xpress_gap_GBP'])) < 1e-6 for k in
        ['Tier 1 calendar horizon', 'Tier 2B dates, continuous horizon', 'Tier 2B dates, six reset windows']))

# ================= references =================
txt = open(r'.cc-scratch/tier2b/v12/report12.txt', encoding='utf-8', errors='replace').read()
refnums = [int(m) for m in re.findall(r'^\[(\d+)\]', txt, re.M)]
add('References [1]..[31] consecutive, 31 entries', list(range(1,32)), refnums, refnums == list(range(1,32)),
    f'{len(refnums)} entries found')
add('New [31] Vaswani et al. (2017) present', 'Vaswani', 'Vaswani' if 'Vaswani' in txt else 'absent', 'Vaswani' in txt)
cited = sorted({int(x) for x in re.findall(r'\[\s*(\d+)\s*\]', txt)})
add('Every reference 1..31 is cited in the body/appendix', sorted(range(1, 32)), cited,
    set(range(1,32)).issubset(set(cited)), f'max cited {max(cited) if cited else None}')

n_ok = sum(1 for c in checks if c['ok'])
summary = {'total': len(checks), 'passed': n_ok, 'failed': len(checks) - n_ok}
json.dump({'generated_by': 'check_v12.py', 'summary': summary, 'checks': checks},
          open(os.path.join(OUT, 'checks_v12.json'), 'w', encoding='utf-8'), indent=1)
print('\nSUMMARY', summary)
for c in checks:
    if not c['ok']:
        print('FAIL |', c['check'], '| exp', c['expected'], '| got', c['got'], '|', c['note'])
