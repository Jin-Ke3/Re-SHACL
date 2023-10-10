# Re-SHACL

## DataSet:

* Please download datasets:
    * EnDe-Lite50(without_Ontology).ttl
    * EnDe-Lite100(without_Ontology).ttl
    * EnDe-Lite1000(without_Ontology).ttl
    * EnDe-10(without_Ontology).ttl
    * EnDe-30(without_Ontology).ttl <-- Generating
    * EnDe-60(without_Ontology).ttl <-- Generating
    * EnDe-100(without_Ontology).ttl

* EnDe-Lite covers 30 classes.
* EnDe involves 427 classes (including the 30 classes above)

* Please add all datasets to "source/Datasets/".

## Experiments:

  * Run the experiments by running the scripts in the category "Validation". 
    * The performance of pySHACL and ReSHACL is currently tested in three rounds on each dataset, resulting in average runtimes (s). pySHACL-OWL's performance is only experimented with one round on each dataset (because it is too time-consuming).
  
  * The validation results are recorded in the folder corresponding to each data set in "Outputs".
    * The validation result **graph** is stored in the "validationGraph" folder. 
    * Validation reports are stored in the "validationReports" folder. 
    * The runtime and number of violations are recorded in the file "RunTimeResults.txt".