# robotframework-LogXML2Chunks

A Python library for extracting individual test cases from Robot Framework output.xml files into separate chunks with individual HTML reports.

## Features

- 📦 Split large Robot Framework output.xml into individual test case chunks
- 📊 Generate separate HTML log reports for each test case
- 🔍 Extract test documentation and structured steps
- 📝 Preserve test metadata (index, test_name, test_id, status, documentation, steps, source, xml_file, success)
- 🎯 Data collected from XML files can be made available to reporting systems such as Polarion, qTest, Jira, etc. 


## Installation

### From PyPI (when published)

```bash
pip install robotframework-logxml2chunks
```

### From source

```bash
git clone https://github.com/ajadach/robotframework-LogXML2Chunks.git
cd robotframework-LogXML2Chunks
pip install -e .
```

## Usage

### As a Python Library

```python
from LogXML2Chunks import LogXML2Chunks

# Initialize the chunker
chunker = LogXML2Chunks()

# Split output.xml into chunks
chunker.split_to_chunks(
    output_xml_path='output.xml',
    output_dir='chunked_results'
)

# Read data from chunks XML
from pathlib import Path
chunks_folder = Path(__file__).parent / 'chunks'
data = chunker.get_data_from_chunks(chunks_folder)
```

### As a Command Line Tool

```bash
# Basic usage
logxml2chunks output.xml

# Specify output directory
logxml2chunks output.xml --output-dir my_chunks

# Show help
logxml2chunks --help
```

## Output Structure

Each test case generates:
- `{index}_{test_name}_{test_id}.xml` - Individual test XML file
- `{index}_{test_name}_{test_id}_log.html` - HTML log report

The `split_to_chunks()` method returns a list of dictionaries with:
```python
{
    'index': 1,                          # Test case index
    'test_name': 'My Test Case',        # Test name
    'test_id': 's1-t1',                 # Test ID
    'status': 'PASS',                   # Test status (PASS/FAIL/SKIP)
    'documentation': '...',             # Full documentation text
    'steps': {...},                     # Extracted steps dictionary
    'source': '/path/to/test.robot',    # Source file path
    'xml_file': Path('...'),            # Generated XML file path
    'log_file': Path('...'),            # Generated log file path
    'checksum': 'a1b2c3d4...',          # MD5 checksum of test_name + documentation
    'success': True,                    # Whether generation succeeded
    'error': None                       # Error message if failed
}
```

### Checksum Field

The `checksum` field is automatically calculated for each test case using MD5 hash of the concatenated `test_name` and `documentation`. This provides a unique identifier for tracking test case changes:

- **Format**: 32-character hexadecimal string
- **Algorithm**: MD5
- **Input**: `test_name + documentation`
- **Use cases**: 
  - Detect documentation changes
  - Track test case modifications
  - Integration with external test management systems
  - Version control of test cases

## Step Extraction

The library automatically extracts steps from test documentation that follow this format:

```robot
*** Test Cases ***
My Test Case
    [Documentation]    Test description
    ...
    ...                *Steps*:
    ...                1. First step / Expected result
    ...                2. Second step / Expected result
    ...
    ...                Summary Documentation    
    Log    Test execution
```

Extracted steps format:
```python
{
    'First step': 'Expected result',
    'Second step': 'Expected result',    
}
```

## Requirements

- Python >= 3.7
- robotframework >= 4.0

## Development

### Setup Development Environment

```bash
# Clone repository
git clone https://github.com/ajadach/robotframework-LogXML2Chunks.git
cd robotframework-LogXML2Chunks

# Install in development mode with dev dependencies
pip install -e ".[dev]"
```

### Run Tests

```bash
pytest tests/
```

## License

MIT License - see LICENSE file for details

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## Author

Artur Jadach

## Links

- GitHub: https://github.com/ajadach/robotframework-LogXML2Chunks
- Issues: https://github.com/ajadach/robotframework-LogXML2Chunks/issues
