# Re-SHACL

## DataSet:

* Please download datasets:
    * EnDe-Lite50(without_Ontology).ttl : [Download](https://drive.google.com/file/d/14RXnJZL9e6ZdbFtfPH69t1lI5Idbnkze/view?usp=drive_link)
    * EnDe-Lite100(without_Ontology).ttl : [Download](https://drive.google.com/file/d/1xWMp2mSEk0i7X_nHp3JjZRnvt3bPiz96/view?usp=drive_link)
    * EnDe-Lite1000(without_Ontology).ttl : [Download](https://drive.google.com/file/d/1B2Xbukuj93vHeRBvbgnPCoYAxbHcC7Hg/view?usp=drive_link)
      * The genaration of EnDe-Lite datasets cover 30 classes.

    * LUBM datasets from: https://data.uni-hannover.de/dataset/trav-shacl-benchmarks-experimental-settings-and-evaluation/resource/3dcefa6d-d57e-4de7-bc11-56227ae4e119?inner_span=True
      * We follow the LUBM datasets for the paper **Trav-SHACL: Efficiently validating networks of SHACL constraints**.
      * Our experiments used only three SKGs and three MKGs.

* Please add all datasets to `source/Datasets/…`.

## Shapes Graph:

* The shapes graphs needed for the experiment have been stored in the folder `source/ShapesGraphs`.
  * Shape_30 is dedicated to the validation of the EnDe datasets.
  * For different sizes of LUBM datasets we use the three schemas provided in the paper **Trav-SHACL: Efficiently validating networks of SHACL constraints**.

## Experiments:

  * Run the experiments by running the script `run.py`.
  
  * The validation results are recorded in the folder corresponding to each data set in `Outputs`.
    * The validation result **graph** is stored in the `validationGraph` folder. 
    * Validation reports are stored in the `validationReports` folder. 
    * The runtime and number of violations are recorded in the file `RunTimeResults.txt`.