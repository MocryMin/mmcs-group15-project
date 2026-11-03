# Project_Brief.pdf — text extract (pages 1-6 )
Derived artefact: produced by `tools/extract_brief.py` with PyMuPDF PyMuPDF 2.0: Python bindings for the MuPDF 1.28.5 library.. The PDF `Project_Brief.pdf` is authoritative; line breaks and table layout in this text extract are approximate. Page markers below follow the PDF pagination.
Source PDF sha256: b9672d12850a3e02bd0c0ed3e248a5c19cb5b10140fbc6ebde8ae35571213631


---

## Page 1

Modelling, Methodology and Consulting Skills (MMCS) 
Optimisation Models for Renewable 
Energy Investment and Flexibility 
MSc Operational Research - Project brief for academic year 2026/27 
Introduction 
Students will act as technical consultants engaged by a hypothetical Scottish renewable energy 
investment consortium. The client is considering investment in new renewable generation in Scotland, 
together with flexible assets that can absorb or shift electricity when renewable generation is not well 
aligned with demand and available routes for using that electricity. 
The project combines strategic investment decisions with operational scheduling. Students must decide 
how a pre-defined infrastructure performs across changing demand, renewable generation and market 
conditions. There are two options for further development, either exploring investment in alternative 
infrastructure or building a temporal analysis which can allow the stakeholder project their investment 
over time. The main modelling work should be implemented in Python using the Xpress optimiser. 
The project is intentionally open-ended. There is no single required objective function, model 
architecture or data processing route. A successful submission should demonstrate a robust modelling 
methodology, clear assumptions, appropriate use of data and public information, technical validation 
and a consulting style interpretation of the results. 
 
 
Contents 
Client context ................................................................................................................................... 2 
Data provided ................................................................................................................................... 2 
Your modelling challenge ................................................................................................................. 2 
Tier 1 (mandatory) - Making use of surplus renewable energy ......................................................... 3 
Tier 2 (option A) - Generation investment ...................................................................................... 3 
Tier 2 (option B) - A sustainable strategy through time .................................................................... 4 
What the client expects .................................................................................................................... 5 
Appendix ........................................................................................................................................... 6


---

## Page 2

Client context 
You are working as a team of technology consultants advising a hypothetical organisation considering 
significant investment in renewable energy infrastructure. The client has already received a proposed 
solution from another consultancy but was not satisfied that it provided a sufficiently convincing 
investment strategy. Your task is to scrutinise the problem independently, challenge the assumptions 
behind a simple solution and develop an improved strategy supported by quantitative analysis. 
The central question is: 
What combination of renewable generation and flexible energy technologies should the 
client invest in and how should those assets be used to create a financially and 
operationally sustainable strategy? 
This is a combination of investment and optimisation problem, hence do not consider it as a detailed 
electrical engineering exercise. Your recommendations should be understandable to a senior investor as 
well as technically defensible. The project concept combines strategic investment choices with 
decisions about how infrastructure should be operated and expects the modelling to be implemented in 
a clear technical way.  
For the purposes of this project, treat the infrastructure using the supplied datasets as the client's 
existing position. This represents the starting point inherited from the previous consultancy. Your role is 
to determine how effectively that infrastructure can be used and then to demonstrate whether a more 
sophisticated strategy materially improves the client's position. The supplied generation, demand and 
pricing data represent a constructed energy system and should not be interpreted as a detailed picture of 
Scottish transmission constraints or actual curtailment events. 
Data provided 
You will receive five core datasets as a starting point.  
▪ 
daily_generation_by_fuel.csv contains daily electricity generation by fuel type – including wind, 
solar, hydro, nuclear, gas and other generation technologies.  
▪ 
daily_generation_total.csv - total daily generation. This is the aggregate of the fuel level 
generation data. 
▪ 
daily_demand.csv - daily electricity demand over several years (since 2020), allowing you to 
examine both typical conditions and periods when supply and demand are more challenging. 
▪ 
wind_farm_generation.csv - the daily generation profile associated with the wind farm 
infrastructure used in the baseline case. 
▪ 
daily_market_index_price.csv - historical daily wholesale electricity value, expressed in 
£/MWh.   
 
The datasets cover broadly the same period from 2020 onwards. You should begin by understanding and 
checking the data, prior to constructing the design and development of an optimisation model. Consider 
whether dates align correctly, whether observations are missing or unusual, how generation varies by 
technology and when renewable production is high or low relative to demand. Document any data 
adjustments you would like to propose. 
You may supplement the input data with clearly referenced public information where this improves your 
model, particularly for technology investment costs or scenarios. The supplied datasets are intended to 
allow you to focus on the initial modelling, analysis and work towards consulting recommendation. 
Your modelling challenge 
There are two stages to the modelling challenge. All teams should first develop the Tier 1 foundational 
(vanilla) model. Once this has been implemented, validated and interpreted, teams should select one of 
two extension routes: Tier 2A or Tier 2B. Tier 2A focuses on changing the infrastructure and investment


---

## Page 3

portfolio, while Tier 2B focuses on improving the way the existing portfolio is operated and assessed over 
time. Teams are not expected to complete both Tier 2 options. Depth, justification and interpretation of 
the chosen extension are more important than attempting to include every possible feature. 
Tier 1 (mandatory) - Making use of surplus renewable energy 
The first step is to recognise that renewable electricity is not always produced when it is most useful. At 
some points there may be more renewable generation available than can immediately be used. 
Using the infrastructure and historical generation profiles represented in the supplied data, build a 
foundational optimisation model that identifies when electricity is available beyond immediate demand 
and investigates whether battery storage and/or hydrogen production can make better use of it. Your 
principal investment decisions should relate to how much battery and/or electrolyser capacity is worth 
adding and how much otherwise unused renewable energy these technologies can capture. 
For battery storage, use a standard 2-hour battery. This 
means that, for example, a 50 MW battery can store 
100 MWh of electricity. Assume 90% roundtrip 
efficiency and that normally only 20%-80% of the 
battery's total capacity is used. As an indicative 
investment assumption, use €0.288 million per MWh 
of storage capacity. The amount of battery capacity to 
build should be a decision variable. 
For hydrogen, you may consider a PEM electrolyser. A 
commercial 20 MW ITM Power POSEIDON system can 
be used as a reference but again – the amount built 
should be a decision. Assume that the electrolyser can 
operate between 20% and 100% of installed capacity 
and requires approximately 55.9 kWh of electricity to produce 1 kg of hydrogen. In plain terms, surplus 
renewable electricity can therefore be converted into a product with potential economic value.  
You should investigate and justify an appropriate electrolyser investment cost. For an initial economic 
scenario, you may use approximately £9.5/kg of hydrogen as a benchmark but you should recognise that 
this is based on a UK policy supported hydrogen value (rather than a guaranteed commercial selling 
price). Testing lower and higher hydrogen values is therefore encouraged. 
The key client question at this level is:  
Given the existing generation infrastructure, how much battery or hydrogen capacity 
should the client invest in and is the additional value created sufficient to justify that 
investment? 
Tier 1 models should use a simplified treatment of time – detailed chronological operation of storage is 
not required at this stage. 
Tier 2 (option A) - Generation investment 
The key question here is whether the client should change the generation infrastructure assumed in the 
baseline case. Extend your foundational model by considering an alternative generation infrastructure. 
Using the historical data as evidence of how different generation technologies behave, determine what 
generation capacity the investor should support or develop, should they decide to invest in new 
infrastructure. A useful starting point may be to explore in-development projects across Scotland and the 
wider UK area (a recommended source as a starting point: Renewable Energy Planning Database: 
quarterly extract - GOV.UK). 
Your model should answer questions such as:  
▪ 
Which technologies should the client invest in?  
▪ 
How much capacity should be developed?  
▪ 
What level of demand can the proposed portfolio serve?  
▪ 
How much renewable generation could be produced but not usefully consumed?


---

## Page 4

Investment cost should be part of the decision. You 
will therefore need to compare the additional energy or 
benefit created by an investment with the amount of 
capital required. 
This provides the client's infrastructure investment 
strategy and a benchmark against which sophisticated 
solutions can be compared. Your optimisation should 
distinguish between the infrastructure already 
represented in the supplied data and new investment 
decisions introduced by your team. A strong Tier 2A 
analysis will show the marginal benefit of additional 
infrastructure, identify where diminishing returns arise 
and compare additional generation investment with 
further investment in battery or hydrogen capacity. 
Tier 2 (option B) - A sustainable strategy through time 
In the consulting industry, a convincing solution presents how strategy and decision making are 
influenced over time, i.e. make use of time series. 
In the Tier 2B extension you should explicitly preserve the chronology of the supplied data. Unlike the Tier 
1 approximation, decisions on one day should influence what is possible on later days. For example, a 
battery should have a state of charge that carries from one period to the next and electricity or hydrogen 
value may vary with market conditions. Teams should investigate seasonal behaviour, prolonged periods 
of high or low renewable generation and unusually high demand or market prices.   
A battery cannot discharge electricity today unless 
energy has previously been stored. Similarly, the value 
of renewable generation depends on when it is 
available relative to demand. An investment that 
appears attractive when annual averages are 
considered may perform poorly during periods of low 
renewable output, high demand or prolonged surplus 
generation. 
Your advanced model should therefore determine how 
the investment portfolio performs day by day over 
time. It should identify how the assets should be 
operated. 
As defined earlier, the client ultimately wants to understand what a successful and sustainable strategy 
looks like. Sustainability here should be considered broadly:  
▪ 
sensible use of investment capital, i.e. return on investment (ROI) is a factor for every investor 
▪ 
good use of renewable energy – in the context of the UK and global sustainability goals 
▪ 
resilience to changing conditions, i.e. a recommendation that remains flexible, not dependent on 
a particular set of assumptions. 
You might therefore test alternative levels of demand, renewable generation, battery costs, hydrogen 
values or investment budgets. You should identify which assumptions materially change the 
recommended strategy. The objective could be, for example, to: 
▪ 
minimise cost 
▪ 
maximise renewable utilisation 
▪ 
minimise unused generation 
▪ 
maximise economic value 
▪ 
or balance several of these considerations.  
The important requirement is that you explain why your chosen objective (or a combination of multiple) 
represents the client's interests.


---

## Page 5

What the client expects 
Your final recommendation should go beyond reporting the output of an optimisation models. The client 
wants to know what to invest in, how much to invest and why the recommendation is better than a 
simpler strategy. Furthermore, a very important question of interest is what could cause the 
recommendation to change. 
You should therefore demonstrate that you have challenged your own model.  
✓ Check that the results make sense and display appropriate visualisations. 
✓ Compare the optimised solution with simple alternatives.  
✓ Explain which assumptions have the greatest influence through sensitivity analysis.  
✓ Distinguish clearly between conclusions supported by the data and assumptions introduced for 
modelling purposes. 
You will have access to supervision throughout the project. However, the modelling choices, validation 
and recommendation remain the responsibility of your team. 
A successful project will tell a clear consulting story: understand the problem, establish a credible 
baseline, improve the use of renewable energy through investment and flexibility, stress test the strategy 
over time (if Tier 2B is chosen) and give the client a concise recommendation about where its money 
should go.


---

## Page 6

Appendix 
Battery and electrolyser parameters and recommended sources: 
Subject area 
Recommendation 
Notes 
Source 
Battery size 
2-hour battery 
If 50 MW of battery capacity is built, 
assume it can store 100 MWh. Installed 
MW should be a decision variable. 
Tesla Megapack 
Battery efficiency 
90% round-trip 
efficiency 
This allows for some electricity being lost 
when energy is stored and later released. 
 
Battery usable range 
20%-80% of total 
capacity 
As a modelling assumption, prevent the 
model from repeatedly using the battery 
from completely empty to completely 
full.  
  
 
Battery investment 
cost 
€0.288m per MWh 
Multiply installed battery energy capacity 
by this figure to estimate investment 
cost.  
Danish Energy Agency - Energy 
Storage 
 
(the data sheet) 
 
Electrolyser type 
PEM (can be another 
type) 
Treat this as flexible electricity demand 
that produces hydrogen when electricity 
is available. 
ITM Power POSEIDON 
 
Electrolyser scale 
20 MW reference, but 
capacity should be a 
decision variable 
20 MW provides a realistic commercial 
benchmark, whilechoosing the amount 
worth building. 
 
Electrolyser operating 
range 
20%-100% of installed 
capacity 
Hence, a 20 MW electrolyser would 
normally operate between 4 MW and 20 
MW when running. 
 
Hydrogen production 
The electrolyser needs 
about 55.9 kWh of 
electricity to produce 1 
kg of hydrogen. 
Convert electricity used by the 
electrolyser into kilograms of hydrogen 
produced. 
 
Hydrogen value 
£9.5/kg as a core 
scenario 
Use this to estimate the value of hydrogen 
produced, but also test lower and higher 
values. It is a supported benchmark, not a 
guaranteed market price. 
Net Zero Hydrogen Fund: HAR1 
successful projects (published 
December 2023) - GOV.UK 
 
For weighted average strike price 
of £241/MWh 
 
£241/MWh x 39.4 
kWh/kg / 1000 = 
£9.5/kg (see the 
sources in the last 
column) 
Hydrogen Transport and Storage 
Cost Report 
 
For energy content of 
hydrogen 39.4 kWh/kg
