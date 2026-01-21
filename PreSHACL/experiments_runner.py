"""Experiments Runner for SHACL Validation Performance Analysis

This module runs validation experiments to measure and compare the performance
of different SHACL validation approaches including:
- Standard PySHACL validation
- Closed-Shaper preprocessing
- Re-SHACL preprocessing
- Combined approaches with different reasoning levels (RDFS, OWL-LD)
"""

import time
from pyshacl import validate
import data
from pre_processor import *
from rdflib import SH, XSD
import pandas as pd
from ReSHACL.re_shacl import merged_graph
from data import *
import numpy as np
from owlrl import *
import scipy.stats as st
import random
import logging

logger = logging.getLogger(__name__)

# Experiment configuration constants
DEFAULT_NUM_REPETITIONS = 3
DEFAULT_TIME_MULTIPLIER = 1
CONFIDENCE_LEVEL = 0.95


def timed_validation(data_graph, shapes_graph, inference_lvl='rdfs'):
    """Run a single timed SHACL validation."""
    start = time.time()
    conforms, validation_graph, validation_text = validate(data_graph, shacl_graph=shapes_graph,
                                         data_graph_format='turtle',
                                         shacl_graph_format='turtle',
                                         inference=inference_lvl)

    end = time.time()
    logger.info(validation_text)
    logger.info(f"{end - start} seconds")


def average_timed_validation(data_graph_path, shapes_graph_path, inference_lvl='none', method='none'):
    """Calculate and return the average runtime of validations and the number of violations."""
    num_repetitions = DEFAULT_NUM_REPETITIONS
    multiplier = DEFAULT_TIME_MULTIPLIER
    total_time = 0
    if method == 'closed-shaper':

        for i in range(num_repetitions):
            shapes_graph = None
            data_graph = None
            shapes_graph_entailed = None
            data_graph_entailed = None
            shapes_graph = load_turtle_graph(shapes_graph_path)
            data_graph = load_turtle_graph(data_graph_path)
            start = time.time()
            data_graph_entailed, shapes_graph_entailed = pre_process_shacl_graph_full(data_graph, shapes_graph, inference_lvl)
            end = time.time()
            total_time += end - start
        avg_rewriting_time = round(total_time / num_repetitions * multiplier, 2)
    elif method == 're-shacl':
        for i in range(num_repetitions):
            shapes_graph = None
            data_graph = None
            shapes_graph_entailed = None
            data_graph_entailed = None
            shapes_graph = load_turtle_graph(shapes_graph_path)
            data_graph = load_turtle_graph(data_graph_path)
            start = time.time()
            data_graph_entailed, same_dic, shapes_graph_entailed = merged_graph(data_graph, shacl_graph=shapes_graph,
                                                              data_graph_format='turtle',
                                                              shacl_graph_format='turtle')
            end = time.time()
            total_time += end - start
        avg_rewriting_time = round(total_time / num_repetitions * multiplier, 2)
    elif method == 're-shacl+closed-shaper':

        for i in range(num_repetitions):
            shapes_graph = None
            data_graph = None
            shapes_graph_entailed = None
            data_graph_entailed = None
            shapes_graph = load_turtle_graph(shapes_graph_path)
            data_graph = load_turtle_graph(data_graph_path)
            start = time.time()
            data_graph_entailed, shapes_graph_entailed = pre_process_shacl_graph_full(data_graph, shapes_graph, inference_lvl)
            data_graph_entailed, same_dic, shapes_graph_entailed = merged_graph(data_graph_entailed, shacl_graph=shapes_graph_entailed,
                                                              data_graph_format='turtle',
                                                              shacl_graph_format='turtle')
            end = time.time()
            total_time += end - start

        avg_rewriting_time = round(total_time / num_repetitions * multiplier, 2)
    else:
        data_graph_entailed = load_turtle_graph(data_graph_path)
        shapes_graph_entailed = load_turtle_graph(shapes_graph_path)
        avg_rewriting_time = 0

    total_time = 0
    if method == 're-shacl' or method == 're-shacl+closed-shaper':
        for i in range(num_repetitions):
            start = time.time()
            conforms, validation_graph, validation_text = validate(data_graph_entailed, shacl_graph=shapes_graph_entailed,
                                                 data_graph_format='turtle',
                                                 shacl_graph_format='turtle',
                                                 inference='none')
            end = time.time()
            total_time += end - start
    else:
        if inference_lvl == 'owl-ld':
            inference_lvl = 'owlrl'
        for i in range(num_repetitions):
            start = time.time()
            conforms, validation_graph, validation_text = validate(data_graph_entailed, shacl_graph=shapes_graph_entailed,
                                                 data_graph_format='turtle',
                                                 shacl_graph_format='turtle',
                                                 inference=inference_lvl)
            end = time.time()
            total_time += end - start

    avg_validation_time = round(total_time / num_repetitions * multiplier, 2)

    return avg_rewriting_time, avg_validation_time, len(list(validation_graph.triples((None, SH.result, None))))


def average_timed_validation_error_bars(data_graph_path, shapes_graph_path, inference_lvl='none', method='none'):
    """Calculate average validation runtime with confidence intervals."""
    num_repetitions = DEFAULT_NUM_REPETITIONS
    timed_runs = []
    if method == 'closed-shaper':
        for i in range(num_repetitions):
            shapes_graph = None
            data_graph = None
            shapes_graph_entailed = None
            data_graph_entailed = None
            shapes_graph = load_turtle_graph(shapes_graph_path)
            data_graph = load_turtle_graph(data_graph_path)
            start = time.time()
            data_graph_entailed, shapes_graph_entailed = pre_process_shacl_graph_full(data_graph, shapes_graph, inference_lvl)
            conforms, validation_graph, validation_text = validate(data_graph_entailed, shacl_graph=shapes_graph_entailed,
                                                 data_graph_format='turtle',
                                                 shacl_graph_format='turtle',
                                                 inference=inference_lvl)

            end = time.time()
            timed_runs.append((end - start))

        avg_rewriting_time = round((end - start) / num_repetitions, 2)

    else:
        avg_rewriting_time = 0
        for i in range(num_repetitions):
            shapes_graph = None
            data_graph = None
            shapes_graph = load_turtle_graph(shapes_graph_path)
            data_graph = load_turtle_graph(data_graph_path)
            start = time.time()
            conforms, validation_graph, validation_text = validate(data_graph, shacl_graph=shapes_graph,
                                                 data_graph_format='turtle',
                                                 shacl_graph_format='turtle',
                                                 inference=inference_lvl)
            end = time.time()
            timed_runs.append((end - start))

    avg_validation_time = round(sum(timed_runs) / num_repetitions, 2)
    interval = st.t.interval(CONFIDENCE_LEVEL, len(timed_runs) - 1, loc=np.mean(timed_runs), scale=st.sem(timed_runs))
    logger.info(f"results for method: {method} and regime: {inference_lvl}")
    logger.info([avg_validation_time, interval[0], interval[1]])


def load_turtle_graph(path):
    """Load an RDF graph from a Turtle file."""
    graph = rdflib.Graph()
    graph.parse(path, format="turtle")
    return graph


def load_graph_from_str(path):
    """Load an RDF graph from a string."""
    graph = rdflib.Graph()
    graph.parse(data=path)
    return graph


def get_data_graph_stats(data_graph):
    """Calculate statistics for a data graph."""
    subjects = set()
    predicates = set()
    objects = set()

    for s, p, o in data_graph.triples((None, None, None)):
        subjects.add(s)
        predicates.add(p)
        objects.add(o)

    num_triples = len(data_graph)
    num_subjects = len(subjects)
    num_predicates = len(predicates)
    num_objects = len(objects)

    logger.info(f"Triples: {num_triples}")
    logger.info(f"Subjects: {num_subjects}")
    logger.info(f"Predicates: {num_predicates}")
    logger.info(f"Objects: {num_objects}")

    return num_triples, num_subjects, num_predicates, num_objects


def get_shape_graph_stats(shape_graph):
    """Calculate statistics for a SHACL shapes graph."""
    num_shapes = len(list(shape_graph.triples((None, None, SH.NodeShape))))
    num_closed_shapes = len(list(shape_graph.triples((None, SH.closed, rdflib.Literal("true", datatype=XSD.boolean)))))
    num_property_shapes = len(list(shape_graph.triples((None, SH.property, None))))
    property_paths = set()
    target_classes = set()
    for _, _, o in shape_graph.triples((None, SH.path, None)):
        property_paths.add(o)

    for _, _, o in shape_graph.triples((None, SH.targetClass, None)):
        target_classes.add(o)

    num_target_properties = len(property_paths)
    num_target_classes = len(target_classes)

    logger.info(f"Shapes: {num_shapes}")
    logger.info(f"Closed shapes: {num_closed_shapes}")

    return num_shapes, num_closed_shapes, num_property_shapes, num_target_classes, num_target_properties


def get_all_stats(matches, match_names):
    """Calculate and display statistics for all graph pairs."""
    i = 0
    data_graph_stats = [{"Data Graph": y} for x, y in match_names]
    shape_graph_stats = [{"Shapes Graph": x} for x, y in match_names]
    logger.info(data_graph_stats)

    for shapes_graph_path, data_graph_path in matches:
        shape_graph_name = match_names[i][0]
        data_graph_name = match_names[i][1]
        shacl_graph = load_turtle_graph(shapes_graph_path)
        data_graph = load_turtle_graph(data_graph_path)

        num_shapes, num_closed_shapes, num_property_shapes, num_target_classes, num_target_properties = get_shape_graph_stats(shacl_graph)
        shape_graph_stats[i]["Node Shapes"] = num_shapes
        shape_graph_stats[i]["Property Shapes"] = num_property_shapes
        shape_graph_stats[i]["Targeted Classes"] = num_target_classes
        shape_graph_stats[i]["Targeted Properties"] = num_target_properties
        shape_graph_stats[i]["Closed Shapes"] = num_closed_shapes

        num_triples, num_subjects, num_predicates, num_objects = get_data_graph_stats(data_graph)
        data_graph_stats[i]["Triples"] = num_triples
        data_graph_stats[i]["Subjects"] = num_subjects
        data_graph_stats[i]["Predicates"] = num_predicates
        data_graph_stats[i]["Objects"] = num_objects

        i += 1

    df_dg = pd.DataFrame(data_graph_stats)
    df_sg = pd.DataFrame(shape_graph_stats)
    logger.info(df_dg.to_latex())
    logger.info(df_sg.to_latex())


def get_method_string(method, regime):
    """Generate a human-readable method description string."""
    if method == "none":
        method = "PySHACL"
    if regime == "none":
        method += " (without reasoning)"
    elif regime == "rdfs":
        method += " (RDFS reasoning)"
    elif regime == "owl-ld":
        method += " (OWL-LD reasoning)"

    return method


def get_results(matches):
    """Run validation experiments and collect results."""
    inference_levels = ['rdfs']
    methods = ['closed-shaper']
    i = 0
    for shapes_graph_path, data_graph_path in matches:
        results = []
        logger.info(f"Match {i}")

        for regime in inference_levels:
            for method in methods:
                if method == 're-shacl' or method == 're-shacl+closed-shaper':
                    continue

                temp_results = {}
                shacl_graph = shapes_graph_path
                data_graph = data_graph_path
                logger.info(f"PYSHACL with {method} as pre-processing and {regime} entailment")
                avg_rewriting_time, avg_validation_time, num_violations = average_timed_validation(data_graph,
                                                                                                   shacl_graph,
                                                                                                   regime, method)

                temp_results["Method"] = get_method_string(method, regime)
                temp_results["Execution time (ms)"] = avg_rewriting_time + avg_validation_time
                if method == 'none':
                    temp_results["Rewriting time (ms)"] = "--"
                else:
                    temp_results["Rewriting time (ms)"] = avg_rewriting_time
                temp_results["Validation time (ms)"] = avg_validation_time
                results.append(temp_results)

        df = pd.DataFrame(results)
        df = df.round(decimals=2).astype(object)
        logger.info(df)
        logger.info(df.to_latex())
        i += 1

    df = pd.DataFrame(results)
    logger.info(df)


def load_owl_graph(path):
    """Load an OWL ontology from an RDF/XML file."""
    graph = rdflib.Graph()
    graph.parse(path, format='application/rdf+xml')
    return graph


def rdfs_entailment(graph):
    """Apply RDFS entailment to a graph using OWL-RL."""
    DeductiveClosure(RDFS_Semantics).expand(graph)
    return graph


def create_random_closed_graph(numbers):
    """Create a shapes graph with randomly selected closed shapes."""
    index = 0
    shapes30 = load_turtle_graph("../source/ShapesGraphs/Shapes30/Shape_30.ttl")

    for s, _, _ in shapes30.triples((None, RDF.type, SH.NodeShape)):
        if index in numbers:
            shapes30.add((s, SH.closed, rdflib.Literal(True)))
        index += 1

    shapes30.serialize(f"./../source/ShapesGraphs/Shape_30_closed_{len(numbers)}.ttl", format="turtle")


if __name__ == '__main__':
    logging.getLogger('rdflib').setLevel(logging.ERROR)

    matches = [("./../source/ShapesGraphs/Shape_30_closed_3.ttl",
                "./../source/Datasets/EnDe-Lite50(without_Ontology).ttl"),
               ("./../source/ShapesGraphs/Shape_30_closed_6.ttl",
                "./../source/Datasets/EnDe-Lite50(without_Ontology).ttl"),
               ("./../source/ShapesGraphs/Shape_30_closed_15.ttl",
                "./../source/Datasets/EnDe-Lite50(without_Ontology).ttl"),
               ("./../source/ShapesGraphs/Shape_30_closed_30.ttl",
                "./../source/Datasets/EnDe-Lite50(without_Ontology).ttl")]

    get_results(matches)
