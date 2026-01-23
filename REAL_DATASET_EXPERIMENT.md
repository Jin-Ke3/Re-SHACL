# Real Dataset Experiment Setup - EnDe-Lite50

This document describes the experiments created for the real dataset (EnDe-Lite50).

## Overview

The experiment consists of two main steps:
1. **Python**: Shape entailment with timing (COMPLETED ✓)
2. **Java**: SHACL validation with timing (READY TO RUN)

## Data Files

### Input Files
- **Data Graph**: `source/Datasets/EnDe-Lite50(without_Ontology).ttl` (534,696 triples)
- **Ontology**: `source/dbpedia_ontology.owl` (58,808 triples)
- **Shapes Graphs** (4 files):
  - `source/ShapesGraphs/Shape_30_closed_3.ttl` (13,156 triples)
  - `source/ShapesGraphs/Shape_30_closed_6.ttl` (13,159 triples)
  - `source/ShapesGraphs/Shape_30_closed_15.ttl` (13,168 triples)
  - `source/ShapesGraphs/Shape_30_closed_30.ttl` (13,183 triples)

### Generated Files

#### 1. Entailed Data Graph (from `entail_real_data_graph.py`)
- **Output**: `source/Datasets/EnDe-Lite50_RDFS_entailed.ttl`
- **Status**: RUNNING (~22 minutes)
- **Purpose**: Pre-entail the data graph with RDFS reasoning to avoid repeated 22-minute operations

#### 2. Entailed Shapes Graphs (from `entail_real_shapes_graphs.py`)
- **Output Directory**: `source/ShapesGraphs/entailed/`
- **Status**: COMPLETED ✓
- **Files Created**:
  - `Shape_30_closed_3_entailed.ttl` (13,192 triples, +36)
  - `Shape_30_closed_6_entailed.ttl` (13,179 triples, +20)
  - `Shape_30_closed_15_entailed.ttl` (13,188 triples, +20)
  - `Shape_30_closed_30_entailed.ttl` (13,273 triples, +90)
- **Timing Results**:
  - Shape_30_closed_3: 0.2644s
  - Shape_30_closed_6: 0.2598s
  - Shape_30_closed_15: 0.2678s
  - Shape_30_closed_30: 0.2628s
  - **Total entailment time**: 1.0548s

## Scripts Created

### 1. `entail_real_data_graph.py`
**Purpose**: Entail the EnDe-Lite50 data graph with RDFS reasoning once.

**What it does**:
- Loads data graph (534,696 triples)
- Loads DBpedia ontology (58,808 triples)
- Merges them together
- Applies RDFS reasoning (~22 minutes)
- Saves entailed data graph

**Status**: RUNNING in background

### 2. `entail_real_shapes_graphs.py` ✓
**Purpose**: Entail all 4 shapes graphs with DBpedia ontology.

**What it does**:
- Loads DBpedia ontology once
- For each shapes graph:
  - Loads shapes graph
  - Applies shape entailment with RDFS
  - Times the operation
  - Saves entailed shapes
- Generates timing report and JSON results

**Status**: COMPLETED
**Total time**: 1.0548 seconds

**Output**: `source/ShapesGraphs/entailed/entailment_results.json`

### 3. `ValidateRealDataset.java`
**Purpose**: Run SHACL validation using Java/Jena validator.

**What it does**:
- Loads entailed data graph (once)
- For each entailed shapes graph:
  - Loads shapes graph
  - Runs SHACL validation
  - Times the operation
  - Saves validation report
- Generates summary report and CSV results

**Status**: READY TO RUN (waiting for entailed data graph)

**Expected Output**: `Outputs/real_dataset_validation/validation_results.csv`

### 4. `run_java_validation.py`
**Purpose**: Helper script to check prerequisites and show instructions.

## Results Location

### Shape Entailment Results
- **Entailed shapes**: `source/ShapesGraphs/entailed/*.ttl`
- **Timing JSON**: `source/ShapesGraphs/entailed/entailment_results.json`

### Validation Results (after running Java)
- **Validation reports**: `Outputs/real_dataset_validation/*_validation_report.ttl`
- **Timing CSV**: `Outputs/real_dataset_validation/validation_results.csv`

## Running the Experiments

### Step 1: Entail Data Graph (RUNNING)
```bash
python entail_real_data_graph.py
```
Status: Running in background (~22 minutes)

### Step 2: Entail Shapes Graphs (COMPLETED ✓)
```bash
python entail_real_shapes_graphs.py
```
Status: COMPLETED (1.05 seconds total)

### Step 3: Run Java Validation (PENDING)
Once the entailed data graph is ready:

**Option A**: Copy to shacl-validator project
```bash
# Copy ValidateRealDataset.java to your shacl-validator project
# Compile and run from there
```

**Option B**: Run from closed-shaper (if Jena is in classpath)
```bash
javac -cp "path/to/jena/*" ValidateRealDataset.java
java -cp ".;path/to/jena/*" ValidateRealDataset
```

## Experiment Goals

1. ✓ Measure shape entailment time for real dataset shapes graphs
2. ✓ Store all entailed shapes graphs for reuse
3. ⏳ Measure SHACL validation time using entailed data + entailed shapes
4. ⏳ Compare baseline (no entailment) vs our approach (with entailment)

## Notes

- **RDFS only**: This experiment uses RDFS reasoning (not OWL-LD) as requested
- **One-time entailment**: Data graph entailment (~22 min) is done once and saved
- **Fast shape entailment**: Shape entailment is very fast (~0.26s per shapes graph)
- **Reusable artifacts**: All entailed files can be reused for multiple experiments

## Warnings Observed

During shape entailment, some incongruences were detected in the ontology:
- Missing property constraints for domain properties (e.g., `spurType`, `numberOfPassengers`, `shipCrew`, `currentRank`)
- Superclass relationships that may cause closed shape violations (e.g., `SnookerPlayer`/`SnookerChamp`)

These warnings indicate potential validation issues but do not prevent entailment.
