#!/usr/bin/env python3
"""
Compile and run Java SHACL validation for the real dataset.

This script:
1. Checks if the entailed data graph exists
2. Compiles the Java validator
3. Runs the validation
"""

import subprocess
import sys
import os
from pathlib import Path

# Paths
JAVA_FILE = "ValidateRealDataset.java"
DATA_GRAPH = r"C:\Users\zenon\eclipse-workspace\closed-shaper\source\Datasets\EnDe-Lite50_RDFS_entailed.ttl"
SHAPES_DIR = r"C:\Users\zenon\eclipse-workspace\closed-shaper\source\ShapesGraphs\entailed"

# Check if Jena is available via classpath or Maven
JENA_CLASSPATH = r"C:\Users\zenon\.m2\repository\org\apache\jena\*"  # Adjust this path as needed

def check_prerequisites():
    """Check if required files exist"""
    print("Checking prerequisites...")
    
    if not os.path.exists(JAVA_FILE):
        print(f"❌ Java file not found: {JAVA_FILE}")
        return False
    
    if not os.path.exists(DATA_GRAPH):
        print(f"❌ Entailed data graph not found: {DATA_GRAPH}")
        print("   Run entail_real_data_graph.py first to create the entailed data graph.")
        return False
    
    if not os.path.exists(SHAPES_DIR):
        print(f"❌ Entailed shapes directory not found: {SHAPES_DIR}")
        print("   Run entail_real_shapes_graphs.py first to create entailed shapes.")
        return False
    
    # Check for entailed shape files
    shape_files = [f for f in os.listdir(SHAPES_DIR) if f.endswith("_entailed.ttl")]
    if len(shape_files) < 4:
        print(f"❌ Expected 4 entailed shape files, found {len(shape_files)}")
        return False
    
    print("✓ All prerequisites met")
    return True

def main():
    print("=" * 80)
    print("Java SHACL Validation Runner")
    print("=" * 80)
    print()
    
    if not check_prerequisites():
        sys.exit(1)
    
    print("\n" + "=" * 80)
    print("Instructions for running Java validation:")
    print("=" * 80)
    print()
    print("Since this workspace doesn't have direct access to the Java validator")
    print("at C:\\Users\\zenon\\eclipse-workspace\\shacl-validator,")
    print("you'll need to manually run the validation.")
    print()
    print("Steps:")
    print("1. Copy ValidateRealDataset.java to your shacl-validator project")
    print("2. Compile and run it from there")
    print()
    print("Or, if you have Apache Jena in your classpath, you can compile here:")
    print()
    print("Compile:")
    print(f"  javac -cp \"{JENA_CLASSPATH}\" ValidateRealDataset.java")
    print()
    print("Run:")
    print(f"  java -cp \".;{JENA_CLASSPATH}\" ValidateRealDataset")
    print()
    print("=" * 80)
    print()
    print("Data graph location:")
    print(f"  {DATA_GRAPH}")
    print()
    print("Entailed shapes location:")
    print(f"  {SHAPES_DIR}")
    print()
    shape_files = [f for f in os.listdir(SHAPES_DIR) if f.endswith("_entailed.ttl")]
    for sf in sorted(shape_files):
        print(f"  - {sf}")

if __name__ == "__main__":
    main()
