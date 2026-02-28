# robotframework-LogXML2Chunks

A Python library for extracting individual test cases from Robot Framework output.xml files into separate chunks with individual HTML reports.

## Features

- 📦 Split large Robot Framework output.xml into individual test case chunks
- 📊 Generate separate HTML log reports for each test case
- 🔍 Extract test documentation, structured steps and requirements
- 🏷️ Optionally extract a custom filename prefix from test/suite setup messages using a regex pattern
- 📝 Preserve test metadata (index, test_name, test_id, status, documentation, steps, requirements, source, interface, xml_file, log_file, checksum, success)
- 🔐 Portable MD5 checksum calculated from test name, documentation and normalized source path
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

# Basic usage
chunker = LogXML2Chunks()

# With debug output disabled
chunker = LogXML2Chunks(debug=False)

# With custom filename prefix extraction (see section below)
chunker = LogXML2Chunks(filename_prefix_pattern=r"open_session\('(\w+)'")

# Split output.xml into chunks
chunker.split_to_chunks(
    output_xml_path='output.xml',
    output_dir='chunked_results'
)

# Read data from chunks XML
from pathlib import Path
chunks_folder = Path('chunked_results')
data = chunker.get_data_from_chunks(chunks_folder)

# Or read a single chunk
chunk = chunker.get_data_from_chunk('chunked_results/1_My_Test_s1-t1.xml')
```

### As a Command Line Tool

```bash
# Basic usage
logxml2chunks output.xml

# Specify output directory
logxml2chunks output.xml --output-dir my_chunks

# Enable verbose summary output
logxml2chunks output.xml --verbose

# Show help
logxml2chunks --help
```

## Output Structure

Each test case generates:
- `{index}_{test_name}_{test_id}.xml` - Individual test XML file
- `{index}_{test_name}_{test_id}_log.html` - HTML log report

When `filename_prefix_pattern` is set, filenames include the extracted prefix:
- `{index}_{PREFIX}_{test_name}_{test_id}.xml`
- `{index}_{PREFIX}_{test_name}_{test_id}_log.html`

The `split_to_chunks()` and `get_data_from_chunks()` methods return a list of dictionaries with:

```python
{
    'index': 1,                          # Test case index
    'test_name': 'My Test Case',         # Test name
    'test_id': 's1-t1',                  # Test ID
    'status': 'PASS',                    # Test status (PASS/FAIL/SKIP)
    'documentation': '...',              # Full documentation text
    'steps': {...},                      # Extracted steps dictionary
    'requirements': [...],               # Extracted requirements list
    'source': '/path/to/test.robot',     # Original absolute source file path
    'interface': 'REST',                 # Prefix extracted by filename_prefix_pattern (or None)
    'xml_file': 'chunked_results/...',   # Generated XML file path
    'log_file': 'chunked_results/...',   # Generated HTML log file path (if exists)
    'checksum': 'a1b2c3d4...',           # MD5 checksum (see Checksum section)
    'success': True,                     # Whether generation succeeded
    'error': None                        # Error message if failed
}
```

## Checksum

The `checksum` field is an MD5 hash calculated from three components:

| Component | Description |
|---|---|
| `test_name` | Name of the test case |
| `documentation` | Full documentation text of the test |
| `source` (normalized) | Source `.robot` file path, lowercased, trimmed to start from `/tests/` or `/scripts/` folder |

Source path normalization ensures the checksum is **portable across different repository locations** – two users cloning the same repository to different paths (`/home/user1/repo/` vs `/home/user2/repo/`) will produce identical checksums.

**Normalization examples:**

| Original path | Normalized |
|---|---|
| `/home/user1/my-repo/Scripts/Module/test.robot` | `scripts/module/test.robot` |
| `/home/user2/other-repo/tests/ACL/acl_test.robot` | `tests/acl/acl_test.robot` |
| `/home/user/repo/tests_team1/scripts_team2/x.robot` | no marker found → full lowercased path |

- **Format**: 32-character hexadecimal string
- **Algorithm**: MD5
- **Use cases**: detect documentation changes, track test case modifications, integration with external test management systems

## Step Extraction

Steps are automatically extracted from test documentation sections marked as `*Steps*`, `*Steps:*` or `Steps:`.

```robot
*** Test Cases ***
My Test Case
    [Documentation]    Test description
    ...
    ...                *Steps*:
    ...                1. First step / Expected result
    ...                2. Second step / Expected result
    ...                - Bulleted step
```

Extracted steps format:
```python
{
    'First step': 'Expected result',
    'Second step': 'Expected result',
    'Bulleted step': 'pass',            # 'pass' when no '/' separator provided
}
```

## Requirements Extraction

Requirements are automatically extracted from test documentation sections marked as `*Requirements*`, `*Requirements:*` or `Requirements:`.

```robot
*** Test Cases ***
My Test Case
    [Documentation]    Test description
    ...
    ...                *Requirements*:
    ...                1. REQ-001
    ...                2. REQ-002
    ...                - REQ-003
```

Extracted requirements format:
```python
['REQ-001', 'REQ-002', 'REQ-003']
```

## Filename Prefix Extraction

When `filename_prefix_pattern` is provided, the library searches test and suite setup keyword messages for a regex match and prepends the captured value (uppercased) to the chunk filenames.

Search order:
1. Current suite SETUP keywords
2. Parent suites SETUP keywords (traversing up the suite hierarchy)
3. Test case keywords

```python
# Example: extract session type from open_session('REST', '10.0.0.1')
chunker = LogXML2Chunks(filename_prefix_pattern=r"open_session\('(\w+)'")

# Produces filenames like:
# 1_REST_My_Test_Case_s1-t1.xml
# 1_REST_My_Test_Case_s1-t1_log.html
```

The extracted prefix is also available in result dictionaries as the `interface` field.

## API Reference

### `LogXML2Chunks(debug=True, filename_prefix_pattern=None)`

| Parameter | Type | Default | Description |
|---|---|---|---|
| `debug` | `bool` | `True` | Print progress and debug messages to stdout |
| `filename_prefix_pattern` | `str` or `None` | `None` | Regex pattern with one capture group to extract a filename prefix |

### `split_to_chunks(output_xml_path, output_dir='chunked_results')`

Splits a Robot Framework `output.xml` into individual per-test XML files and generates HTML log reports using `rebot`.

### `get_data_from_chunks(folder_path)`

Scans a folder for `*.xml` chunk files and returns a list of result dictionaries.

### `get_data_from_chunk(xml_filepath)`

Parses a single chunk XML file and returns a result dictionary.

## Requirements

- Python >= 3.7
- robotframework >= 4.0

## Development

### Setup Development Environment

```bash
git clone https://github.com/ajadach/robotframework-LogXML2Chunks.git
cd robotframework-LogXML2Chunks
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
