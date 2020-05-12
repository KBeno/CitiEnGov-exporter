# Introduction
This script provides translation from a simple feature collection gml exported from Geoserver into two different formats: *INSPIRE* and *CityGML* (with energyADE extension)

For the *INSPIRE* gml the following xml schema is used:
https://inspire.ec.europa.eu/schemas/bu-core2d/4.0/BuildingsCore2D.xsd

For the *CityGML* gml the following xml shema is used:
http://www.citygmlwiki.org/images/a/ac/EnergyADE.xsd

The goal of this project is to provide datasets from the pilot action of [CitiEnGov](https://www.interreg-central.eu/Content.Node/CitiEnGov.html) in Ferrara to external use in a standardized form.

The script is written in pure Python 3.7.0

The script was written by Benedek Kiss (kiss.benedek@szt.bme.hu) during his placement at Dedagroup Public Services in the framework of Klimate KIC Pioneers into practice program

---

# How to use
the script takes 4 arguments:
- the mode how the input is given: *url* or *file*
- the source xml path (CitiEnGov exported gml)
- the target file path (the new gml to write the data into)
- the name of the standard to make the gml compliant to: *INSPIRE* or *CityGML*

in the command line type this to write out help
```bash
python citiengov_export_gml.py --help
```
example commands:
```bash
python citiengov_export_gml.py -f citiengov.gml inspire.gml INSPIRE
python citiengov_export_gml.py -u "http://..." citygml.gml CityGML
```
