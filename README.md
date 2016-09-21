# parivahan-py


## Get Vehicle Details from Registration Number from parivahan.gov site


### how to use

You can instantiate the ParivahanClient and then call the function for getting the registration details
like this

```python

parivahan = ParivahanClient()
print parivahan.get_registration_details('XX00XX0000')

```


* Free software: MIT license


Credits
---------

This package was created with Cookiecutter_ and the `audreyr/cookiecutter-pypackage`_ project template.

.. _Cookiecutter: https://github.com/audreyr/cookiecutter
.. _`audreyr/cookiecutter-pypackage`: https://github.com/audreyr/cookiecutter-pypackage
