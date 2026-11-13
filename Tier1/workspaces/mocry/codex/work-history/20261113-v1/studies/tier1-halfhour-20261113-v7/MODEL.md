# Half-hour model and numerical certificate

Let $\Delta=0.5$ hours and $t$ index 105,216 consecutive UTC periods. Every period belongs to a UTC day $d(t)$. In the following equations, energy is MWh and power MW. Implementation converts energy to GWh and money to million GBP2020/year.

Installed battery and electrolyser counts are $N_i,M_j\in\mathbb Z_{\ge0}$. Battery $i$ has usable capacity $W_i$, power $P_i$, one-way efficiency $\eta_i=\sqrt{\mathrm{RTE}_i}$ and daily self-discharge $\delta_i$. Its half-hour retention is $\rho_i=(1-\delta_i)^{\Delta/24}$. Above-minimum usable stock is $s_{it}$; charge, sales discharge and electrolysis discharge are $c_{it},r_{it},u_{it}$. Direct sales and direct electrolysis supply are $q_t,a_t$. Electrolyser input is $h_{jt}$, specific use is $\kappa_j$ MWh/kg, minimum load fraction is $\alpha_j$, rated input power is $P^H_j$, and online count is $z_{jt}$.

$$
q_t+a_t+\sum_i c_{it}\le G_t,\qquad q_t+\sum_i r_{it}\le D_t,\qquad
\sum_j h_{jt}=a_t+\sum_i u_{it}.
$$

$$
s_{it}=\rho_i s_{i,t-1}+\eta_i c_{it}-(r_{it}+u_{it})/\eta_i,
\quad 0\le s_{it}\le N_iW_i,\quad s_{i0}=s_{iT}=0.
$$

$$
0\le c_{it}\le\Delta P_iN_i,\qquad
0\le r_{it}+u_{it}\le\Delta P_iN_i,\qquad
(c_{it}=0)\lor(r_{it}+u_{it}=0).
$$

There is no additional daily throughput window. Initial 20% SOC is accounted for through commissioning cost, while $s$ measures stock above that minimum.

$$
\alpha_j\Delta P_j^H z_{jt}\le h_{jt}\le\Delta P_j^H z_{jt},
\qquad z_{jt}\in\{0,\ldots,M_j\}.
$$

$$
\sum_{t:d(t)=d}\sum_j h_{jt}/\kappa_j\le L\qquad\text{for every UTC day }d.
$$

Hydrogen is sold as produced; the daily cap is a cumulative acceptance limit, not a hydrogen storage variable. Minimum-load constraints apply within each half-hour, with no added minute-scale startup model. All flows are nonnegative.

Policy B adds

$$
q_t=\min(G_t,D_t),\qquad
\sum_i r_{it}=\min\left\{(D_t-G_t)_+,\ \sum_i\min(\eta_i\rho_i s_{i,t-1},\Delta P_iN_i)\right\}.
$$

Thus batteries cannot hold back deliverable energy during a current shortfall. The output available in a half-hour is limited by both stock and power. The same shared output limit prevents using that output twice for sales and electrolysis.

Profit is the six-year mean of electricity and net hydrogen receipts, less annual-equivalent installed-asset costs. The annual-equivalent cost retains v6's 5% real discount rate, battery/electrolyser lives of 15/30 years and stack renewal assumptions. Subtracting the same-policy no-investment business is only an objective offset and does not change the optimiser.

## Computation and certificate

`model.py` implements these conditions as a mixed-integer model with adaptive addition of operating disjunctions. Every saved exact candidate is independently checked against all original conditions, including those not initially present in the relaxation. Minimum-load feasibility is reconstructible from $z=\lceil h/(\Delta P^H)\rceil$ since all candidate minimum fractions are at most one half.

The global upper bound relaxes integer investment, minimum loading, battery mode exclusivity and B's nonlinear battery priority. It retains all periods, energy balances, power limits, capacity limits and daily hydrogen caps. In B, direct sales remain fixed; charging is therefore impossible when $G_t\le D_t$, and battery sales are impossible when $D_t\le G_t$. These necessary conditions are also imposed on the pricing subproblems.

All comparable electrolysers have the same annual cost per input MW. In the continuous relaxation, the most efficient NEPTUNE V/ALPHA50 technology dominates the other products. This argument is used only for the upper bound; feasible integer plans use actual product counts. Less efficient small modules could potentially improve discrete capacity rounding, and the reported global profit gap bounds that possibility.

The master starts with electrolysis and direct sales. Its generation/sales/electrolysis-source dual prices define the opportunity cost of charging and value of each discharge destination. For each battery type, a separate linear programme finds its best complete six-year, single-unit trajectory with zero opening/closing stock. The annual ownership cost minus the best dual-valued operating benefit is the battery column's reduced cost $\bar c_i$. If all $\bar c_i\ge0$, no additional battery column improves the continuous master: the restricted optimum is a valid upper bound for the complete problem. If a reduced cost is negative, the trajectory can be added to the master and the process repeated.

Both policies in the main data have strictly positive reduced costs at the initial master solution. For any feasible integer plan with battery counts $N_i$, the resulting dual inequality is

$$
\Pi\le U-\sum_i\bar c_iN_i,
$$

where $U$ is the relaxed optimum and profit units are consistent. The minimum positive per-unit penalty exceeds $U$ minus the saved zero-battery integer profit. Consequently a plan with at least one battery cannot outperform the saved plan. This establishes the zero-battery investment choice within numerical tolerances, while the remaining total profit gap quantifies the uncertainty about the exact electrolyser module combination.

The half-hour schedules are perfect-foresight historical solutions. They are not forecasts, and their returns are conditional on the inherited constructed-system and hydrogen-market assumptions. Source-shape uncertainty is separate from optimisation error. The flat independent-wind profile and the wind-shape alternative both preserve the same daily wind energy.
