from typing import Optional, Union
from enum import Enum
from pre_shacl import rdfs_entailment, owl_entailment
from rdflib import Graph


class InferenceLevel(Enum):
    """Enumeration of supported inference levels for RDF entailment."""
    NONE = 'none'
    RDFS = 'rdfs'
    OWL_LD = 'owl-ld'
    OWLRL = 'owlrl'


class EntailEngine:
    """Applies semantic entailment rules to RDF graphs based on specified inference level."""
    
    def __init__(self, data_graph: Graph, inference_level: Union[str, InferenceLevel]):
        """
        Initialize the entailment engine.
        
        Args:
            data_graph: An rdflib Graph to apply entailment rules to
            inference_level: The level of inference to apply ('none', 'rdfs', 'owl-ld', 'owlrl' or InferenceLevel enum)
        """
        self.data_graph = data_graph
        # Accept both string and enum values for backward compatibility
        if isinstance(inference_level, str):
            self.inference_level = inference_level
        else:
            self.inference_level = inference_level.value

    def entail(self) -> Graph:
        """
        Apply entailment rules to the data graph based on the configured inference level.
        
        Returns:
            The entailed data graph with inferred triples added
        """
        if self.inference_level == InferenceLevel.RDFS.value:
            rdfs_entailment.entail(self.data_graph)
        if self.inference_level in (InferenceLevel.OWL_LD.value, InferenceLevel.OWLRL.value):
            owl_entailment.entail(self.data_graph)

        return self.data_graph