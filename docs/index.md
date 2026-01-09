# Overview
FRAM core package is the central package of the [FRAM]({{ framlinks.fram }}) modelling framework developed by [the Norwegian Water Resources and Energy Directorate (NVE)]({{ framlinks.nve }}). The package contains functionality for data transformation and definitions of interfaces. 

Power market models access data through FRAM **core model** - a model object that holds the data. Core model uses generic data structures and different abstraction levels to perform advanced data manipulations like aggregation, dissaggregation, handling time resolution, unit conversion etc.

![FRAM core](img/framcore.svg)

## Installation
To install only FRAM core package, run `pip install fram-core`. But we recommend that you rather start by installing our [simple demo]({{ framlinks.demo }}) to better understand how FRAM works.

## Core model
The core model object is populated with the data from the database using Populator() in [FRAM data]({{ framlinks.data }}) package. Core model components hold data about different components in the power system.

Core model represents data as expressions and uses "lazy" approach, i.e. the calculations are not done immediately but are postponed. This approach gives a much better performance when processing large data quantities. Data processing expressions are saved inside the components of the core model.  

## Components
Core model contains **high-level** and **low-level** components.

### High-level components
High-level components are "recognizable" components such as thermal power plants, consumers, transmission lines. They can be "decomposed" into low-level components.

### Low-level components
Low-level components are the most basic components that can be used to represent the high-level components - **node** and **flow**. They can describe anything in the power market model. 

### Conversion between high-level and low-level components
The advantage of decomposing high-level components into flow and node is that you can create generic algorithms with minimal code to manipulate the data and avoid duplicating code for similar operations. For example, you can write one generic function to find all hydropower plants or storage systems or to calculate yearly production, demand, export or import. Learn more about high-level and low-level components in the [FRAM documentation]({{ framlinks.fram-HL-components }})  on these components.

## Interfaces
FRAM core package contains definition of interfaces necessary to run FRAM. See also [more technical details](tech_details.md) for information about interfaces, the Model object and other objects in FRAM core.

- **Populator**

Abstract class that defines methods that must be implemented in a populator. [FRAM data]({{ framlinks.data }}) package contains our own implementation of populator that supports our database format. If you want to use your own database, you can write your own implementation of populator based on this interface.

- **Solver**

Abstract class that defines methods that must be implemented in a model solver. [FRAM JulES]({{ framlinks.julesAPI }}) package contains our implementation of a solver for JulES power market model. Each market model is connected to FRAM using its own solver implementation. 

- **Aggregator**

Abstract class that handles aggregation and disaggregation of components, for instance grouping components based on geography into a new component and restoring the detailed components. See Code Reference for general implementation of [Aggregator](reference.md/#framcore.aggregators.Aggregator), and for different components like [NodeAggregator](reference.md/#framcore.aggregators.NodeAggregator) and [HydroAggregator](reference.md/#framcore.aggregators.HydroAggregator). Aggregators are added to Model when used (Aggregator.aggregate(model)), and can be undone in LIFO order with model.disaggregate().

