"""Entailment Base - Common Fixpoint Loop

This module provides a common fixpoint loop pattern for semantic entailment engines.
It extracts the shared iteration logic used by both RDFS and OWL entailment.
"""

import logging
from rdflib import Graph
from typing import Set, Tuple, Callable

logger = logging.getLogger(__name__)


def run_fixpoint_entailment(
    data_graph: Graph,
    apply_rules: Callable[[Graph, Set[Tuple]], None],
    max_iterations: int = 1000,
    entailment_type: str = "semantic"
) -> None:
    """
    Run entailment rules until a fixpoint is reached.
    
    This provides a common fixpoint loop pattern for semantic entailment.
    The loop continues until no new triples can be inferred or max_iterations is reached.
    
    Args:
        data_graph: The RDF graph to apply entailment rules to (modified in place)
        apply_rules: Function that applies entailment rules. 
                    Takes (data_graph, inferred_triples) and adds to inferred_triples set
        max_iterations: Maximum number of iterations to prevent infinite loops
        entailment_type: Type of entailment for logging (e.g., "RDFS", "OWL")
    
    Returns:
        None (graph is modified in place)
    """
    changes = True
    inferred_triples: Set[Tuple] = set()
    initial_size = len(data_graph)
    iteration = 0
    
    while changes and iteration < max_iterations:
        previous_inferred_count = len(inferred_triples)
        
        # Apply the specific entailment rules
        apply_rules(data_graph, inferred_triples)
        
        # Check if new triples were inferred
        changes = len(inferred_triples) != previous_inferred_count
        
        # Add inferred triples to the graph
        for s, p, o in inferred_triples:
            data_graph.add((s, p, o))
        
        iteration += 1
    
    if iteration >= max_iterations:
        logger.warning(
            f"{entailment_type} entailment reached max_iterations ({max_iterations}). "
            f"Fixpoint may not have been reached."
        )
    
    total_inferred = len(data_graph) - initial_size
    if total_inferred > 0:
        logger.debug(
            f"{entailment_type} entailment completed in {iteration} iterations. "
            f"Inferred {total_inferred} new triples."
        )
