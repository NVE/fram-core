Model Framework
===============

Model framework allows to build and run different power market models and compare them against each other. It gets data from a common, not model-specific, database and efficiently performs all necessary data transformations and operations needed to build a model, solve it and get the results.  

Model framework simplifies working with models for analysts and reduces the time needed to build and run models and get results. It ensures consistency between models, as they are created from the same dataset.
Each model is only integrated into the model framework once, and then the analysts can run models and scenarios, sequentially or in parallel, adjusting the workflow depending on the specific analysis needs.

Main features:
- Possible to build APIs for any power market model. In this repository you can find API and tutorials for running an open-source power market model JuLES.
- Able to efficiently perform complex operations on data: aggregate, dissagregate, handle time resolution, geographical resolution, unit standards and different detail levels of a different models.
- Has smart recumpute that allows to skip the computation operations if the input has not been changed.
- Is fast and has efficient memory use.

.. toctree::
   :maxdepth: 1
   :titlesonly:
   :caption: Getting started

   install
   simple_demo

.. toctree::
   :maxdepth: 1
   :titlesonly:
   :caption: Documentation

   description
   how_to_contribute
   user_guide


Indices and tables
==================
* :ref:`genindex`
* :ref:`modindex`

