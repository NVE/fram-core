# More technical details 

[FRAM]({{ framlinks.fram }}) relies on well-defined interfaces to separate, for example, system description, data handling, and solver integration. This modular design enables extensions and improvements without impacting existing logic, supporting both scalability and robust development. 

[FRAM core](index.md) holds the functionality used to describe and manipulate the modelled energy system, handle time series operations, and holds the definition of key interfaces in FRAM. 

Core also has APIs for Solvers (to run market models) and Populators (input routines to populate a Model), but the specific Solvers and Populators are implemented outside of Core. For Populator to NVE’s database structure, see [FRAM data]({{ framlinks.data }}) and for Solver for JulES power market model, see [FRAM Jules]({{ framlinks.julesAPI }}). 

The following are more detailed descriptions of key aspects of FRAM core, meant to be a support for developers and users of FRAM by elaborating on implementation choices and concepts. The code base of FRAM core is documented in [Code Reference](reference.md). 

## The Model object 

In FRAM core, the energy system is represented with the Model object. This object contains data such as Components, TimeVectors, Curves and Expressions. Model can also contain Aggregators applied to the Model. 

* Components describe the main elements in the energy system. Can have additional attributes. 
* TimeVector and Curve hold the time series data. 
* Expressions are used for data manipulation of TimeVectors and Curves. Can be queried. 
* Aggregators handle aggregation and disaggregation of Components. 

Each of these concepts are described below. 

## Components 

### High-level and low-level components  

We have high-level and low-level components in FRAM core. Result attributes are initialized in the high-level components. When they are transferred to low-level components, and the results are set by a model like JulES, the results will also appear in the high-level components. 

See also [FRAM documentation]({{ framlinks.fram-HL-components }}) for more information about these components.  

#### High-level components 
High-level components, such as a hydropower module, can be decomposed into low-level components like flows and nodes. The high-level description lets analysts work with recognizable domain objects, while the low-level descriptions enable generic algorithms that minimize code duplication and simplify data manipulation.  

#### Low-level components: nodes, flows 
Nodes, flows and arrows are the main building blocks in FRAM's low-level representation of energy systems. A node representd a point where a commodity can possibly be traded, stored or pass through. Movement between nodes is represented by flows with arrows. Flows represent a commodity flow, and can have arrows that each describe contribution of the Flow into a Node. The arrows have direction to determine input or output, and parameters for the contribution of the flow to the node (conversion, efficiency and loss). 

## LevelProfiles 

LevelProfiles are the attributes that hold timeseries data for components. Timeseries data in FRAM is mostly represented as Level * Profile. Level and Profile represent two distinct dimensions of time. This is because we want to simulate future system states with historical weather patterns. Therefore, Level represents the system state at a given time (data_dim), while Profile represents the scenario dimension (scen_dim).  

Example: A Level could represent the installed capacity of solar plants towards 2030, while the Profile could represent the historical variation between 1991-2020. 

#### Level and Profile can have two main formats:  
* A maximum Level with a Profile that varies between 0 and 1. The max format is, for example, used for capacities. 
* An average Level with a Profile with a mean of 1 (can have a ReferencePeriod). Can, for example be used for prices and flows. 

The system needs to be able to convert between the two formats. This is especially important for aggregations (for example weighted averages) where all the TimeVectors need to be on the same format for a correct result.  

Simple example of conversion: pairing a max Level of 100 MW with a mean-one Profile [0, 1, 2]. Asking for this on the max format will return the series 100*[0, 0.5, 1] MW, while on the average format it will return 50*[0, 1, 2] MW. 

Queries to LevelProfile need to provide a database, the desired target TimeIndex for both dimensions, the target unit and the desired format.  

Currently supported queries for LevelProfile: 
* _self.get_data_value(db, scen_dim, data_dim, unit, is_max_level)_
* _self.get_scenario_vector(db, scen_dim, data_dim, unit, is_float32,)_

In addition, we have the possibility to shift, scale, and change the intercept of the LevelProfiles. Then we get the full representation: Scale * (Level + Level_shift) * Profile + Intercept 

## Expressions 

Expressions (Expr) are used to represent Levels and Profiles. Expr are mathematical expressions with TimeVectors and Curves. The simplest Expr is a single TimeVector, while a more complicated expression could be a weighted average of several TimeVectors or Expressions. 

Expr are classified as stock, flow or none of them. See [Stock and flow - Wikipedia](https://en.wikipedia.org/wiki/Stock_and_flow). In FRAM we only support flow data as a rate of change. So, for example, a production timeseries has to be in MW, and not in MWh. Converting between the two versions of flow would add another level of complexity both in Expr and in TimeVector operations. 

Expr are also classified as Level, Profile or none of them (depending on what they represent). This classification, together with stock or flow, is used to check if the built Expr are legal operations. (Expr that are Level can contain its connected Profile Expr. This is used in the queries to evaluate Levels according to their ReferencePeriod.) 

Calculations using Expr are evaluated lazily, reducing unnecessary numerical operations during data manipulation. Computations involving values and units occur only when the Expr is queried.  

__FRAM only supports calculations using +, -, *, and / in Expr__, and we have no plans to change this. Expanding beyond these would turn Expr into a complex programming language rather than keeping it as a simple and efficient system for common time-series calculations. More advanced operations are still possible through eager evaluation, so this is not a limitation. It simply distributes responsibilities across system components in a way that is practical from a maintenance perspective. 

We use SymPy to support unit conversions. Already computed unit conversion factors are cached to minimize redundant calculations. 

Currently supported queries for Expr (see [Aggregators](#aggregators) for more about how they are used): 
* _Get_level_value(expr, db, unit, data_dim, scen_dim, is_max)_  
    * Supports all expressions. Will evaluate level Exprs at data_dim, and profile Exprs as an average over scen_dim (both as constants). 
    * Has optimized fastpath methods for sums, products and aggregations. The rest uses a fallback method with SymPy. 

* _Get_profile_vector(expr, db, data_dim, scen_dim, is_zero_one, is_float32)_  
    * Supports expr = sum(weight[i] * profile[i]) where weight[i] is a unitless constant Expr with value >= 0, and profile[i] is a unitless profile Expr. 

## TimeVectors 

TimeVectors holds timeseries data. A TimeVector can return a vector with values, a TimeIndex, the level or profile format, a unit and a reference period. TimeVectors can store timeseries data in Loaders that point to databases. Data is only retrieved and cached when the TimeVector is queried. 

## TimeIndex 

A TimeIndex can return number of periods, i.e., whether it has 52-week years, if it represents a single year, if it represents whole years, if values can be extrapolated outside of the first and last time point, and if it is constant. 

It also holds the main functionality that extracts data to the correct time period and resolution:  

* _self.get_period_average(vector, start_time, duration, is_52_week_years)_ and  
* _self.write_into_fixed_frequency(target_vector, target_timeindex, input_vector)_, which is especially important to the design.  

A conversion of the data into a specific time period and resolution follows these steps: 
1. If the TimeIndex is not a FixedFrequencyTimeIndex, convert the TimeIndex and the vector to this format. 
2. Then convert the data to the target TimeVector. 

It is easier to efficiently do time series operations between FixedFrequencyTimeIndex and we only need to implement all the other conversion functionality once here. For example, converting between 52-week and ISO-time TimeVectors, selecting a period, extrapolation or changing the resolution. 

When we implement a new TimeIndex, we only need to implement the conversion to FixedFrequencyTimeIndex and the rest of the conversion functionality can be reused. 

## Aggregators 

Aggregators handles aggregation and disaggregation of Components.

The general approach for aggregation is to group Components, aggregate Components in the same group to (a) new Component(s), delete the detailed Components, and add the mapping to _self._aggregation_map_. 

The general approach for disaggregation is to restore the detailed Components, move results from aggregated Components to detailed Components, and delete the aggregated Components. 

Aggregators applied to Model can be undone in Last In, First Out (LIFO) order with Model._disaggregate()_. 

Aggregator._aggregate()_ has to be called first, before _disaggregate()_ can be called. It is also not allowed to call _aggregate()_ twice in a row for the same Aggregator.  

It is recommended to only use the same Aggregator type once on the same components of a Model. If you want to go from one aggregation level to another, it is better to use Model._disaggregate()_ first and then aggregate again. This is to keep the logic simple and avoid complex expressions. 

Levels and profiles are aggregated separately and then combined into attributes. 

We have chosen to eagerly evaluate weights for aggregation (weighted averages) and disaggregation of levels and profiles. This approach supports any form of aggregation by varying the weights, and complex weights can be created by eagerly evaluating expressions and using the result to compute those weights.  

This is a balance between eagerly evaluating everything and setting up complex expressions. Eagerly evaluating everything would require setting up new TimeVectors after evaluation, which is not ideal. While setting up complex expressions gives expressions that are harder to work with and slower to query from.  

This trade-off simplifies adding logic that recognises if result expressions come from aggregations or disaggregations. When aggregating or disaggregating these, we can go back to the original results rather than setting up complex expressions that for examples aggregates the disaggregated results. 

## Techniques for efficient data processing

* TimeVectors can store timeseries data in Loaders that point to databases. Data is only retrieved and cached when the TimeVector is queried. 

* Converting data from a specific TimeVector to a different period and resolution is always done through FixedFrequencyTimeIndex. Timeseries operations can be implemented more efficiently when the timeseries have fixed frequencies. 

* Calculations using Expr are evaluated lazily, reducing unnecessary numerical operations during data manipulation. Computations involving values and units occur only when the Expr is queried. 

* We use 1-D Numpy arrays and in-place operations to efficiently manipulate timeseries data. This includes converting time series data to the desired resolution and evaluating expressions that consist of multiple TimeVectors. 

* Queries of expressions can be cached depending on the database type (e.g. CacheDB instead of ModelDB). Computed unit conversion factors in the queries are also cached to minimize redundant calculations. 

* Aggregators recognise if result expressions come from aggregations or disaggregations. When aggregating or disaggregating these, we can go back to the original results rather than setting up complex expressions that for examples aggregates the disaggregated results.
