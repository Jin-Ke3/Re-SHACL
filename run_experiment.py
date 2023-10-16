from importlib import reload
from rdflib import Graph, Namespace
from pyshacl import validate
import time
import sys
from prettytable import PrettyTable
import numpy as np
from ReSHACL.re_shacl import merged_graph
import os
import logging

DBO = Namespace("http://dbpedia.org/ontology/")
sys.path.insert(0, sys.path[0] + "/../")

if sys.version[0] == '2':
    reload(sys)
    sys.setdefaultencoding("utf-8")


def check_directory_exists_otherwise_create(directory):
    if not os.path.isdir(directory):
        # Recursively make the folders
        folder_names = directory.split("/")
        folder_name = ""
        for name in folder_names:
            folder_name += name + "/"
            if not os.path.isdir(folder_name):
                os.mkdir(folder_name)
                print(f"Created folder: {folder_name}")


def run_pyshacl(dataset_name, g, sg, inference_method):
    if inference_method == 'both':
        method = 'pyshacl-owl'
    else:
        method = 'pyshacl'

    table = PrettyTable(['Method', 'Average validation time (s)', 'Standard deviation', 'Conform', '#Violation'])

    result_query = """
    SELECT ?v
    WHERE {
        ?s sh:result ?v
    }"""

    inter_time = []
    for n1 in range(0, 3):
        t1 = time.time()
        conform, v_g, v_t = validate(g, shacl_graph=sg, inference=inference_method)
        t2 = time.time()

        inter_time.append(t2 - t1)

    mean_time = np.mean(inter_time)
    std = np.std(inter_time)

    result = v_g.query(result_query)

    print(f'[{method}]=============================')

    print(' Average validation time: ', mean_time, 's')
    print(' Standard deviation: ', std, 's')
    print(' #Violation: ', len(result))

    # Saving the validation report graph
    check_directory_exists_otherwise_create(f"Outputs/{dataset_name}/violationGraph/")
    v_g.serialize(destination=f"Outputs/{dataset_name}/violationGraph/{method}_results.ttl")

    # Saving the validation report in txt
    check_directory_exists_otherwise_create(f"Outputs/{dataset_name}/validationReports/")
    file = open(f"Outputs/{dataset_name}/validationReports/{method}_results.txt", "w")
    file.write(v_t)
    file.close()

    table.add_row([method, mean_time, std, conform, len(result)])

    check_directory_exists_otherwise_create(f"Outputs/{dataset_name}/")
    file_table = open(f"Outputs/{dataset_name}/RunTimeResults.txt", "a+")
    file_table.write(str(table))
    file_table.close()

    print(table)


def run_reshacl(dataset_name, g, sg, inference_method):
    table = PrettyTable(['Method', 'Average validation time (s)', 'Standard deviation', 'Conform', '#Violation'])

    result_query = """
    SELECT ?v
    WHERE {
        ?s sh:result ?v
    }"""

    inter_time = []
    for n2 in range(0, 3):
        t3 = time.time()
        fused_graph1, same_dic1, shapes = merged_graph(g, shacl_graph=sg, data_graph_format='turtle',
                                                       shacl_graph_format='turtle')
        shapes.bind("dbo", DBO)
        conform, v_g, v_t = validate(fused_graph1, shacl_graph=shapes, inference=inference_method)
        t4 = time.time()

        inter_time.append(t4 - t3)

    mean_time = np.mean(inter_time)
    std = np.std(inter_time)

    result = v_g.query(result_query)

    print(f'[ReSHACL]=============================')

    print(' Average validation time: ', mean_time, 's')
    print(' Standard deviation: ', std, 's')
    print(' #Violation: ', len(result))

    # Saving the validation report graph
    check_directory_exists_otherwise_create(f"Outputs/{dataset_name}/violationGraph/")
    v_g.serialize(destination=f"Outputs/{dataset_name}/violationGraph/re-shacl_results.ttl")

    # Saving the validation report in txt
    check_directory_exists_otherwise_create(f"Outputs/{dataset_name}/validationReports/")
    file = open(f"Outputs/{dataset_name}/validationReports/re-shacl_results.txt", "w")
    file.write(v_t)
    file.close()

    table.add_row(["ReSHACL", mean_time, std, conform, len(result)])

    check_directory_exists_otherwise_create(f"Outputs/{dataset_name}/")
    file_table = open(f"Outputs/{dataset_name}/RunTimeResults.txt", "a+")
    file_table.write(str(table))
    file_table.close()

    print(table)


def run_experiment(dataset_name, dataset_uri, shapes_graph_uri, method='pyshacl', ontology=''):
    g = Graph()
    # Loading the data graph
    logging.getLogger('rdflib').setLevel(logging.ERROR)
    g.parse(dataset_uri)

    if ontology != '':
        # Importing Ontology into the data graph
        g.parse(ontology, format="xml")

    sg = Graph()
    # Loading the shapes graph
    sg.parse(shapes_graph_uri)
    sg.bind("dbo", DBO)

    # Preheating with 10 rounds
    i = 0
    for i in range(5):
        conform, v_g, v_t = validate(g, shacl_graph=sg, inference='none')

    print(f"***** START VALIDATION ON [{dataset_name}] *****")

    if method == 'pyshacl':
        run_pyshacl(dataset_name, g, sg, 'none')
    elif method == "pyshacl-rdfs":
        run_pyshacl(dataset_name, g, sg, 'rdfs')
    elif method == "pyshacl-owl":
        run_pyshacl(dataset_name, g, sg, 'both')
    elif method == 'reshacl':
        run_reshacl(dataset_name, g, sg, 'none')


if __name__ == "__main__":
    # Experiment EnDe-Lite50
    # Experiment data stored in Outputs/<dataset_name>/
    # In the example below it's stored in Outputs/EnDe-Lite50/
    run_experiment(dataset_name="EnDe-Lite50",
                   dataset_uri="source/Datasets/EnDe-Lite50(without_Ontology).ttl",
                   shapes_graph_uri="source/ShapesGraphs/Shape_30.ttl",
                   method='pyshacl',
                   ontology="source/dbpedia_ontology.owl")
    run_experiment("EnDe-Lite50",
                   "source/Datasets/EnDe-Lite50(without_Ontology).ttl",
                   "source/ShapesGraphs/Shape_30.ttl",
                   method='pyshacl-rdfs',
                   ontology="source/dbpedia_ontology.owl")
    run_experiment("EnDe-Lite50",
                   "source/Datasets/EnDe-Lite50(without_Ontology).ttl",
                   "source/ShapesGraphs/Shape_30.ttl",
                   method='reshacl',
                   ontology="source/dbpedia_ontology.owl")

    # Experiment EnDe-Lite100
    run_experiment("EnDe-Lite100",
                   "source/Datasets/EnDe-Lite100(without_Ontology).ttl",
                   "source/ShapesGraphs/Shape_30.ttl",
                   method='pyshacl',
                   ontology="source/dbpedia_ontology.owl")
    run_experiment("EnDe-Lite100",
                   "source/Datasets/EnDe-Lite100(without_Ontology).ttl",
                   "source/ShapesGraphs/Shape_30.ttl",
                   method='pyshacl-rdfs',
                   ontology="source/dbpedia_ontology.owl")
    run_experiment("EnDe-Lite100",
                   "source/Datasets/EnDe-Lite100(without_Ontology).ttl",
                   "source/ShapesGraphs/Shape_30.ttl",
                   method='reshacl',
                   ontology="source/dbpedia_ontology.owl")

    # Experiment EnDe-Lite1000
    run_experiment("EnDe-Lite1000",
                   "source/Datasets/EnDe-Lite1000(without_Ontology).ttl",
                   "source/ShapesGraphs/Shape_30.ttl",
                   method='pyshacl',
                   ontology="source/dbpedia_ontology.owl")
    run_experiment("EnDe-Lite1000",
                   "source/Datasets/EnDe-Lite1000(without_Ontology).ttl",
                   "source/ShapesGraphs/Shape_30.ttl",
                   method='pyshacl-rdfs',
                   ontology="source/dbpedia_ontology.owl")
    run_experiment("EnDe-Lite1000",
                   "source/Datasets/EnDe-Lite1000(without_Ontology).ttl",
                   "source/ShapesGraphs/Shape_30.ttl",
                   method='reshacl',
                   ontology="source/dbpedia_ontology.owl")
