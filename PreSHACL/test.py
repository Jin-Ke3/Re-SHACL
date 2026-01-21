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


def timed_validation(dg, sg, inference_lvl='rdfs'):
    start = time.time()
    conforms, v_graph, v_text = validate(dg, shacl_graph=sg,
                                         data_graph_format='turtle',
                                         shacl_graph_format='turtle',
                                         inference=inference_lvl)

    end = time.time()
    # for s,p,o in v_graph.triples((None, None, None)):
    #     print(s, p, o)
    print(v_text)
    print(f"{end - start} seconds")


# Calculate and return the average runtime of 100 validations and the number of violations
def average_timed_validation(dg_path, sg_path, inference_lvl='none', method='none'):
    num_repetitions = 3
    multiplier = 1
    total_time = 0
    if method == 'closed-shaper':

        for i in range(num_repetitions):
            sg = None
            dg = None
            sg_entailed = None
            dg_entailed = None
            sg = load_turtle_graph(sg_path)
            dg = load_turtle_graph(dg_path)
            start = time.time()
            dg_entailed, sg_entailed = pre_process_shacl_graph_full(dg, sg, inference_lvl)
            # dg_entailed.serialize("./data graphs/DG1_entailed.ttl", format="turtle")
            # sg_entailed.serialize("./shacl shapes/SG1_entailed.ttl", format="turtle")
            end = time.time()
            total_time += end - start
        avg_rewriting_time = round(total_time / num_repetitions * multiplier, 2)
    elif method == 're-shacl':
        for i in range(num_repetitions):
            sg = None
            dg = None
            sg_entailed = None
            dg_entailed = None
            sg = load_turtle_graph(sg_path)
            dg = load_turtle_graph(dg_path)
            start = time.time()
            dg_entailed, same_dic, sg_entailed = merged_graph(dg, shacl_graph=sg,
                                                              data_graph_format='turtle',
                                                              shacl_graph_format='turtle')
            end = time.time()
            total_time += end - start
        avg_rewriting_time = round(total_time / num_repetitions * multiplier, 2)
    elif method == 're-shacl+closed-shaper':

        for i in range(num_repetitions):
            sg = None
            dg = None
            sg_entailed = None
            dg_entailed = None
            sg = load_turtle_graph(sg_path)
            dg = load_turtle_graph(dg_path)
            start = time.time()
            dg_entailed, sg_entailed = pre_process_shacl_graph_full(dg, sg, inference_lvl)
            # dg_entailed.serialize("./dg_entailed.ttl", format="turtle")
            # sg_entailed.serialize("./sg_entailed.ttl", format="turtle")
            dg_entailed, same_dic, sg_entailed = merged_graph(dg_entailed, shacl_graph=sg_entailed,
                                                              data_graph_format='turtle',
                                                              shacl_graph_format='turtle')
            end = time.time()
            total_time += end - start

        avg_rewriting_time = round(total_time / num_repetitions * multiplier, 2)
    else:
        dg_entailed = load_turtle_graph(dg_path)
        sg_entailed = load_turtle_graph(sg_path)
        avg_rewriting_time = 0

    total_time = 0
    # separate the validation for methods including re-shacl, to remove the reasoning
    if method == 're-shacl' or method == 're-shacl+closed-shaper':
        for i in range(num_repetitions):
            start = time.time()
            conforms, v_graph, v_text = validate(dg_entailed, shacl_graph=sg_entailed,
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
            conforms, v_graph, v_text = validate(dg_entailed, shacl_graph=sg_entailed,
                                                 data_graph_format='turtle',
                                                 shacl_graph_format='turtle',
                                                 inference=inference_lvl)
            end = time.time()
            total_time += end - start

    avg_validation_time = round(total_time / num_repetitions * multiplier, 2)

    return avg_rewriting_time, avg_validation_time, len(list(v_graph.triples((None, SH.result, None))))


# Calculate and return the average runtime of 100 validations and the number of violations
def average_timed_validation_error_bars(dg_path, sg_path, inference_lvl='none', method='none'):
    num_repetitions = 3
    timed_runs = []
    if method == 'closed-shaper':
        for i in range(num_repetitions):
            sg = None
            dg = None
            sg_entailed = None
            dg_entailed = None
            sg = load_turtle_graph(sg_path)
            dg = load_turtle_graph(dg_path)
            start = time.time()
            dg_entailed, sg_entailed = pre_process_shacl_graph_full(dg, sg, inference_lvl)
            conforms, v_graph, v_text = validate(dg_entailed, shacl_graph=sg_entailed,
                                                 data_graph_format='turtle',
                                                 shacl_graph_format='turtle',
                                                 inference=inference_lvl)

            end = time.time()
            timed_runs.append((end - start))

        avg_rewriting_time = round((end - start) / num_repetitions, 2)

    else:
        avg_rewriting_time = 0
        for i in range(num_repetitions):
            sg = None
            dg = None
            sg = load_turtle_graph(sg_path)
            dg = load_turtle_graph(dg_path)
            start = time.time()
            conforms, v_graph, v_text = validate(dg, shacl_graph=sg,
                                                 data_graph_format='turtle',
                                                 shacl_graph_format='turtle',
                                                 inference=inference_lvl)
            end = time.time()
            timed_runs.append((end - start))

    avg_validation_time = round(sum(timed_runs) / num_repetitions, 2)
    interval = st.t.interval(0.95, len(timed_runs) - 1, loc=np.mean(timed_runs), scale=st.sem(timed_runs))
    print(f"results for method: {method} and regime: {inference_lvl}")
    print([avg_validation_time, interval[0], interval[1]])


def load_turtle_graph(path):
    graph = rdflib.Graph()
    graph.parse(path, format="turtle")
    return graph


def load_graph_from_str(path):
    graph = rdflib.Graph()
    graph.parse(data=path)
    return graph


def get_data_graph_stats(data_graph):
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

    # Data graph, DG1, DG2
    # #triples, num_TR1, num_TR2
    print(num_triples)
    print(num_subjects)
    print(num_predicates)
    print(num_objects)

    return num_triples, num_subjects, num_predicates, num_objects


def get_shape_graph_stats(shape_graph):
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

    print(num_shapes)
    print(num_closed_shapes)

    return num_shapes, num_closed_shapes, num_property_shapes, num_target_classes, num_target_properties


def get_all_stats(matches, match_names):
    i = 0
    # data_graph_stats = [{"Data Graph": "Triples"}, {"Data Graph": "Subjects"},
    #                     {"Data Graph": "Predicates"}, {"Data Graph": "Objects"}]
    data_graph_stats = [{"Data Graph": y} for x, y in match_names]
    shape_graph_stats = [{"Shapes Graph": x} for x, y in match_names]
    print(data_graph_stats)
    # shape_graph_stats = [{"Shapes Graph": "Node Shapes"}, {"Shapes Graph": "Closed shapes"}]

    for sg, dg in matches:
        shape_graph_name = match_names[i][0]
        data_graph_name = match_names[i][1]
        shacl_graph = load_turtle_graph(sg)
        data_graph = load_turtle_graph(dg)

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
    print(df_dg.to_latex())
    print(df_sg.to_latex())
    # return data_graph_stats, shape_graph_stats


def get_method_string(method, regime):
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
    # inference_levels = ['none', 'rdfs', 'owl-ld']
    # methods = ['none', 're-shacl', 'closed-shaper', 're-shacl+closed-shaper']
    inference_levels = ['rdfs']
    methods = ['closed-shaper']
    i = 0
    for sg, dg in matches:
        results = []
        print(f"Match {i}")

        for regime in inference_levels:
            for method in methods:
                if method == 're-shacl' or method == 're-shacl+closed-shaper':
                    continue

                temp_results = {}
                shacl_graph = sg
                data_graph = dg
                print(f"PYSHACL with {method} as pre-processing and {regime} entailment")
                avg_rewriting_time, avg_validation_time, num_violations = average_timed_validation(data_graph,
                                                                                                   shacl_graph,
                                                                                                   regime, method)

                # temp_results["Shapes graph"] = match_names[i][0]
                # temp_results["Data graph"] = match_names[i][1]
                temp_results["Method"] = get_method_string(method, regime)
                # if regime == 'owlrl':
                #     temp_results["Regime"] = 'owl-ld'.upper()
                # else:
                #     temp_results["Regime"] = regime.upper()
                temp_results["Execution time (ms)"] = avg_rewriting_time + avg_validation_time
                if method == 'none':
                    temp_results["Rewriting time (ms)"] = "--"
                else:
                    temp_results["Rewriting time (ms)"] = avg_rewriting_time
                temp_results["Validation time (ms)"] = avg_validation_time
                # temp_results["#violations"] = num_violations
                # result_element = {match_header: temp_results}
                # print(runtime)
                results.append(temp_results)

        # pd.set_option('display.precision', 2)
        # pd.options.display.precision = 2
        df = pd.DataFrame(results)
        df = df.round(decimals=2).astype(object)
        # df["Execution time (ms)"] = df["Execution time (ms)"].round(2)
        # # df["Rewriting time (ms)"] = df["Rewriting time (ms)"].round(2)
        # df["Validation time (ms)"] = df["Validation time (ms)"].round(2)
        # df = df.round(2)

        # pd.set_option('float_format', '{:.2f}'.format)
        print(df)
        print(df.to_latex())
        i += 1

    df = pd.DataFrame(results)
    print(df)


def load_owl_graph(path):
    graph = rdflib.Graph()
    graph.parse(path, format='application/rdf+xml')
    return graph


def rdfs_entailment(graph):
    DeductiveClosure(RDFS_Semantics).expand(graph)
    return graph


def create_random_closed_graph(numbers):
    index = 0
    shapes30 = load_turtle_graph("../source/ShapesGraphs/Shapes30/Shape_30.ttl")

    for s, _, _ in shapes30.triples((None, RDF.type, SH.NodeShape)):
        if index in numbers:
            shapes30.add((s, SH.closed, rdflib.Literal(True)))
        index += 1

    shapes30.serialize(f"./../source/ShapesGraphs/Shape_30_closed_{len(numbers)}.ttl", format="turtle")


if __name__ == '__main__':
    logging.getLogger('rdflib').setLevel(logging.ERROR)
    # data_graph = load_turtle_graph("./data graphs/DG2.ttl")
    # shacl_graph = load_turtle_graph("./shacl shapes/SG2.ttl")

    # dg_entailed, same_dic, sg_entailed = merged_graph(data_graph, shacl_graph=shacl_graph)
    # data_graph, shacl_graph = pre_process_shacl_graph_full(data_graph, shacl_graph, 'owl-ld')
    #

    # endelite50 = load_turtle_graph("./../source/Datasets/EnDe-Lite50(without_Ontology).ttl")
    # shapes30 = load_turtle_graph("./../source/ShapesGraphs/Shape_30.ttl")

    #30 node shapes
    # 10% closed shapes -> 3
    # numbers = list(range(30))
    # random.shuffle(numbers)
    # indices3 = numbers[0:3]
    # print(indices3)
    # 20% closed shapes -> 6
    # random.shuffle(numbers)
    # indices6 = numbers[0:6]
    # print(indices6)
    # 50% closed shapes -> 15
    # random.shuffle(numbers)
    # indices15 = numbers[0:15]
    # print(indices15)
    # 100% closed shapes -> 30
    # random.shuffle(numbers)
    # indices30 = numbers
    # print(indices30)
    #
    # create_random_closed_graph(indices3)
    # create_random_closed_graph(indices6)
    # create_random_closed_graph(indices15)
    # create_random_closed_graph(indices30)
    # index = 0
    # for s, _, _ in shapes30.triples((None, RDF.type, SH.NodeShape)):
    #     shapes30.add((s, SH.closed, rdflib.Literal(True)))

    # shapes30.serialize("./../source/ShapesGraphs/Shape_30_closed.ttl", format="turtle")

    # matches = [("./shacl shapes/SG1.ttl", "./data graphs/DG1.ttl"),
    #            ("./shacl shapes/SG2.ttl", "./data graphs/DG2.ttl"),
    #            ("./shacl shapes/SG3.ttl", "./data graphs/DG3.ttl"),
    #            ("./shacl shapes/SG4.ttl", "./data graphs/DG4.ttl")]
    #
    # match_names = [("SG_1", "DG_1"),
    #                ("SG_2", "DG_2"),
    #                ("SG_3", "DG_3"),
    #                ("SG_4", "DG_4")]

    # matches = [("./../source/ShapesGraphs/Shape_30_closed_30.ttl",
    #             "./../source/Datasets/EnDe-Lite50(without_Ontology).ttl")]

    matches = [("./../source/ShapesGraphs/Shape_30_closed_3.ttl",
                "./../source/Datasets/EnDe-Lite50(without_Ontology).ttl"),
               ("./../source/ShapesGraphs/Shape_30_closed_6.ttl",
                "./../source/Datasets/EnDe-Lite50(without_Ontology).ttl"),
               ("./../source/ShapesGraphs/Shape_30_closed_15.ttl",
                "./../source/Datasets/EnDe-Lite50(without_Ontology).ttl"),
               ("./../source/ShapesGraphs/Shape_30_closed_30.ttl",
                "./../source/Datasets/EnDe-Lite50(without_Ontology).ttl")]

    get_results(matches)
    # matches = [
    #            ("./../source/ShapesGraphs/Shape_30_closed_3.ttl",
    #             "./../source/Datasets/EnDe-Lite50(without_Ontology).ttl")]

    # match_names = [("Shape30_3", "Ende-Lite50"),
    #                ("Shape30_6", "Ende-Lite50"),
    #                ("Shape30_15", "Ende-Lite50"),
    #                ("Shape30_30", "Ende-Lite50")]

    # inference_levels = ['none', 'rdfs', 'owlrl']
    # inference_levels = ['none', 'rdfs']
    # methods = ['none', 'closer-shaper']
    # for sg, dg in matches:
    #     print("NEW DATASET")
    #     for inference_lvl in inference_levels:
    #         for method in methods:
    #             if method == 'closer-shaper' and inference_lvl == 'none':
    #                 continue
    #             shacl_graph = load_turtle_graph(sg)
    #             data_graph = load_turtle_graph(dg)
    #             average_timed_validation_error_bars(dg, sg, inference_lvl=inference_lvl, method=method)
    # i = 0
    # (6, 3, 3, 2)
    # num_violations = {
    #     'PySHACL': ([2.54, 0.00247, 0.00260], [2.53, 0.00185, 0.00320], [0.89, 0.000863, 0.00090], [1.2, 0.0011668, 0.001223]),
    #     'PySHACL-RDFS': ([7.87, 0.00723, 0.00849], [5.76, 0.00569, 0.00583], [11.83, 0.01172, 0.011934], [3.85, 0.00315,  0.004546]),
    #     'Closed-Shaper-RDFS': ([7.56, 0.00748, 0.00763], [5.66, 0.00560, 0.005724], [12.7, 0.01262, 0.01277], [3.7, 0.003669, 0.0037384]),
    #     'PySHACL-OWL-LD': ([44.58, 0.04358, 0.04556], [40.61, 0.0396, 0.04157], [78.15, 0.07480, 0.081493], [38.36, 0.03826, 0.038450]),
    #     'Closed-Shaper-OWL-LD': ([49.85, 0.04909, 0.05059], [45.21, 0.04448, 0.04594], [74.15, 0.069857, 0.078444], [32.35, 0.03081, 0.033877]),
    #
    # }
    # get_all_stats(matches, match_names)
    # get_results([("./shacl shapes/SG1.ttl", "./data graphs/DG1.ttl")])
    #
    # print("-----BEFORE------")
    # timed_validation(data_graph, shacl_graph, 'none')
    # data_graph = rdfs_entailment(data_graph)
    # data_graph, shacl_graph = pre_process_shacl_graph_full(data_graph, shacl_graph, 'rdfs')
    # data_graph.serialize("./data/graphs/example_entailed.ttl", format="turtle")
    # shacl_graph.serialize("./sg_entailed.ttl", format="turtle")
    # print("-----AFTER------")
    # timed_validation(data_graph, shacl_graph, 'rdfs')
    # timed_validation(data_graph, shacl_graph, 'none')
    # data_graph = load_owl_graph("/Users/togangsta/Downloads/uba1.7/University0_0.owl")
    # num_triples, num_subjects = get_data_graph_stats(data_graph)
    # print(num_triples)
    # print(num_subjects)

    # data_graph, shacl_graph = pre_process_shacl_graph_full(data_graph, shacl_graph, 'owlrl')
    # # shacl_graph.serialize("./data/shacl shapes/closed_graph_ign.ttl", format="turtle")
    # # print("Stored entailed SHACL graph under ./data/shacl shapes/closed_graph_ign.ttl")
    # inference_levels = ['none', 'rdfs', 'owlrl']
    # methods = ['none', 'pre-shacl']
    # timed_validation(data_graph, shacl_graph, 'owlrl')

    # shape_graph_name = match_names[i][0]
    # num_shapes, num_closed_shapes = get_shape_graph_stats(sg)
    # data_graph_stats[0][shape_graph_name] = num_shapes
    # data_graph_stats[1][shape_graph_name] = num_closed_shapes
    #
    # data_graph_name = match_names[i][1]
    # num_triples, num_subjects = get_data_graph_stats(dg)
    # data_graph_stats[0][data_graph_name] = num_triples
    # data_graph_stats[1][data_graph_name] = num_subjects

    # print(results)
    # print(data_graph_stats)
    # df = pd.DataFrame.from_dict(results, orient="index").stack().to_frame()
    # index = pd.MultiIndex.from_tuples(match_names, names=["Shapes graph", "Data graph"])
    # print(index)
    # s = pd.Series(np.random.randn(2), index=index)
    # df = pd.DataFrame(results, columns=["Shapes graph", "Data graph",
    #                                     "Method", "Regime", "Runtime (s)", "Number of violations"])
    # df = pd.DataFrame(results)
    # df.set_index("Shapes graph")
    # # df1 = pd.DataFrame(data_graph_stats)
    # print(df1)
    # print(df1.to_latex())

    # get_data_graph_stats(data_graph)

    # average_timed_validation(data_graph, shacl_graph, 'rdfs')
    # matches = [(data.SG_2, data.DG_3), (data.SG_3, data.DG_4)]
    # inference_levels = ['none', 'rdfs', 'owlrl']
    # for (sg, dg) in matches:
    #     for inference in inference_levels:
    #         print(f"RUNNING WITH {inference} INFERENCE")
    #         shacl_graph = load_graph_from_str(sg)
    #         data_graph = load_graph_from_str(dg)
    #         # inference = 'owlrl'
    #
    #         # for s, p, o in data_graph.triples((None, None, None)):
    #         #     print(s, p, o)
    #         #
    #         # engine = EntailEngine(data_graph, inference)
    #         # engine.entail()
    #         # data_graph = engine.data_graph
    #         #
    #         # print("------AFTER------")
    #         # for s, p, o in data_graph.triples((None, None, None)):
    #         #     print(s, p, o)
    #         print("------WITHOUT PRE-SHACL------")
    #         timed_validation(data_graph, shacl_graph, inference)
    #
    #         data_graph, shacl_graph = pre_process_shacl_graph_full(data_graph, shacl_graph, inference)
    #         # print("DG")
    #         # for s, p, o in data_graph.triples((None, None, None)):
    #         #     print(s.n3(data_graph.namespace_manager), p.n3(data_graph.namespace_manager), o.n3(data_graph.namespace_manager))
    #         #
    #         # print("SHACL")
    #         # for s, p, o in shacl_graph.triples((None, None, None)):
    #         #     print(s.n3(shacl_graph.namespace_manager), p.n3(shacl_graph.namespace_manager), o.n3(shacl_graph.namespace_manager))
    #
    #
    #         print("------WITH PRE-SHACL------")
    #         timed_validation(data_graph, shacl_graph, inference)
    #
    #         print("")
    #         print("")
    #         print("")
