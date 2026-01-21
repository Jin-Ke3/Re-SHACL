from TravSHACL import parse_heuristics, GraphTraversal, ShapeSchema


def validate(shapes_dir, data_graph, output_dir='./result/'):
    prio_target = 'TARGET'  # shapes with target definition are preferred, alternative value: ''
    prio_degree = 'IN'  # shapes with a higher in-degree are prioritized, alternative value 'OUT'
    prio_number = 'BIG'  # shapes with many constraints are evaluated first, alternative value 'SMALL'

    shape_schema = ShapeSchema(
        schema_dir=shapes_dir,  # passing an RDFlib graph containing the shapes
        endpoint=data_graph,
        schema_format='SHACL',
        graph_traversal=GraphTraversal.DFS,
        heuristics=parse_heuristics(prio_target + ' ' + prio_degree + ' ' + prio_number),
        use_selective_queries=True,
        max_split_size=256,
        output_dir=output_dir,  # directory where the output files will be stored
        order_by_in_queries=False,  # sort the results of SPARQL queries in order to ensure the same order across several runs
        save_outputs=True  # save outputs to output_dir, alternative value: False
    )

    result = shape_schema.validate()  # validate the SHACL shape schema
    print(result)
