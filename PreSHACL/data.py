"""SHACL Shape Graphs and Data Graphs for Testing

This module contains predefined RDF graphs in Turtle format used for
SHACL validation testing and experiments.

Shape Graphs:
- PERSON_SHAPE_OPEN (SG_1): Person shape without closed constraint
- PERSON_SHAPE_CLOSED (SG_2): Person shape with closed constraint and ignoredProperties
- CLOSED_SHAPE_EXAMPLE (SG_3): Minimal closed shape example for testing

Data Graphs:
- PERSON_DATA_BASIC (DG_1): Basic person data without type annotations
- PERSON_DATA_WITH_TYPES (DG_2): Person data with explicit type annotations
- PERSON_DATA_WITH_EQUIVALENCES (DG_3): Person data with additional equivalences
- MINIMAL_TEST_DATA (DG_4): Minimal test case with sameAs and equivalent properties
"""

from pathlib import Path


# Helper function to load Turtle files
def _load_fixture(filename: str) -> str:
    """Load a Turtle file from the fixtures directory."""
    fixtures_dir = Path(__file__).parent / 'fixtures'
    file_path = fixtures_dir / filename
    return file_path.read_text(encoding='utf-8')


# Shape Graphs
PERSON_SHAPE_OPEN = _load_fixture('person_shape_open.ttl')
PERSON_SHAPE_CLOSED = _load_fixture('person_shape_closed.ttl')
CLOSED_SHAPE_EXAMPLE = _load_fixture('closed_shape_example.ttl')

# Data Graphs
PERSON_DATA_BASIC = _load_fixture('person_data_basic.ttl')
PERSON_DATA_WITH_TYPES = _load_fixture('person_data_with_types.ttl')
PERSON_DATA_WITH_EQUIVALENCES = _load_fixture('person_data_with_equivalences.ttl')
MINIMAL_TEST_DATA = _load_fixture('minimal_test_data.ttl')

