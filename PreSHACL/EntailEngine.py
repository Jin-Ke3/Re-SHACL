import rdfs_entailment
import owl_entailment


class EntailEngine:
    def __init__(self, data_graph, inference_level):
        self.data_graph = data_graph
        self.inference_level = inference_level

    def entail(self):
        if self.inference_level == 'rdfs':
            rdfs_entailment.entail(self.data_graph)
        if self.inference_level == 'owl-ld' or self.inference_level == 'owlrl':
            # error_messages = owl_entailment.check_inconsistencies(self.data_graph)
            # if error_messages:
            #     self.print_errors(error_messages)
            #     return None

            owl_entailment.entail(self.data_graph)
            # error_messages = owl_entailment.check_inconsistencies(self.data_graph)
            # if error_messages:
            #     self.print_errors(error_messages)
            #     return None

        return self.data_graph

    # def print_errors(self, error_messages):
    #     print(f"{self.inference_level} entailment found the following inconsistencies in the data graph (ERROR):")
    #     for error in error_messages:
    #         print(error)
    #     print("HALTING ...")