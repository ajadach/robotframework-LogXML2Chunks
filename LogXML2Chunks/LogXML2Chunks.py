# !/usr/bin/env python3
"""
Extract individual test cases from Robot Framework output.xml
and generate separate HTML reports for each test case.

Usage:
    python extract_test_cases.py <output.xml> [output_directory]
"""

import xml.etree.ElementTree as ET
import subprocess
import os
import sys
import copy
import re
import hashlib
from pathlib import Path

class LogXML2Chunks:

    def __init__(self, debug=True, filename_prefix_pattern=None):
        """
        Initialize LogXML2Chunks instance.
        
        Args:
            debug: Enable debug output (default: True)
            filename_prefix_pattern: Regex pattern to extract a custom prefix for chunk filenames.
                                    Must contain one capture group that captures the prefix value.
                                    The captured value will be added to the beginning of XML and HTML filenames.
                                    Example: r"open_session\('(\w+)'" would extract 'DB' from 
                                            "open_session('DB', '10.0.0.1')" and create files like:
                                            "1_DB_TestName_s1-t1.xml"
                                    Default: None (no prefix extraction)
        """
        self.debug = debug
        self.filename_prefix_pattern = re.compile(filename_prefix_pattern) if filename_prefix_pattern else None

    def _debug_print(self, *args, **kwargs):
        """Print only if debug mode is enabled."""
        if self.debug:
            print(*args, **kwargs)

    def _extract_steps_from_documentation(self, doc_text):
        """
        Extract steps from test documentation.

        Looks for sections marked as *Steps*, *Steps:*, or Steps: and extracts
        the list items that follow (numbered or bulleted).

        Steps can contain expected behavior after a '/' separator.

        Args:
            doc_text: The documentation text to parse

        Returns:
            Dictionary where keys are step names and values are expected behaviors.
            If no expected behavior is specified (no '/'), the value will be 'pass'.
            Returns empty dict if no steps found.
        """
        if not doc_text:
            return {}

        steps = {}

        # Pattern to find the Steps section (case-insensitive, with or without asterisks/colon)
        # Match *Steps*, *Steps:*, *Steps / Expected*, etc.
        steps_pattern = r'(?:\*)?Steps(?:\s*/\s*\w+)?(?:\*)?:?'

        # Find the Steps section
        match = re.search(steps_pattern, doc_text, re.IGNORECASE | re.MULTILINE)
        if not match:
            return {}

        # Get text after the Steps marker
        text_after_steps = doc_text[match.end():]

        # Split into lines and process
        lines = text_after_steps.split('\n')

        for line in lines:
            line = line.strip()

            # Stop if we hit another section (starts with * and ends with *, or starts with * and contains :)
            # This catches sections like *Expected*, *Results:*, etc.
            if line.startswith('*'):
                # Check if it's a section header (e.g., *Expected*, *Results:*, etc.)
                if line.endswith('*') or ':' in line:
                    break

            # Skip empty lines
            if not line or line == '...':
                continue

            # Remove leading "..." from Robot Framework documentation
            if line.startswith('...'):
                line = line[3:].strip()

            step_text = None

            # Check for numbered list items (1. , 2. , etc.)
            numbered_match = re.match(r'^\d+\.\s+(.+)$', line)
            if numbered_match:
                step_text = numbered_match.group(1).strip()

            # Check for bulleted list items (- , * , etc.)
            if not step_text:
                bullet_match = re.match(r'^[-*]\s+(.+)$', line)
                if bullet_match:
                    step_text = bullet_match.group(1).strip()

            if step_text:
                # Split by '/' to separate step name and expected behavior
                if '/' in step_text:
                    parts = step_text.split('/', 1)
                    step_name = parts[0].strip()
                    expected_behavior = parts[1].strip() if len(parts) > 1 else 'pass'
                else:
                    step_name = step_text
                    expected_behavior = 'pass'

                steps[step_name] = expected_behavior
                continue

            # If we already have steps and this line doesn't match any pattern,
            # it might be the end of the steps section
            if steps and not line.startswith(('1', '2', '3', '4', '5', '6', '7', '8', '9', '-', '*')):
                break

        return steps

    def _extract_requirements_from_documentation(self, doc_text):
        """
        Extract requirements from test documentation.

        Looks for sections marked as *Requirements*, *Requirements:* or Requirements:
        and extracts the list items that follow (numbered or bulleted).

        Args:
            doc_text: The documentation text to parse

        Returns:
            List of requirement strings extracted from the documentation.
            Returns empty list if no requirements found.
        """
        if not doc_text:
            return []

        requirements = []

        # Pattern to find the Requirements section (case-insensitive, with or without asterisks/colon)
        requirements_pattern = r'(?:\*)?Requirements(?:\*)?:?'

        # Find the Requirements section
        match = re.search(requirements_pattern, doc_text, re.IGNORECASE | re.MULTILINE)
        if not match:
            return []

        # Get text after the Requirements marker
        text_after_requirements = doc_text[match.end():]

        # Split into lines and process
        lines = text_after_requirements.split('\n')

        for line in lines:
            line = line.strip()

            # Stop if we hit another section (starts with * and ends with *, or starts with * and contains :)
            if line.startswith('*'):
                if line.endswith('*') or ':' in line:
                    break

            # Skip empty lines
            if not line or line == '...':
                continue

            # Remove leading "..." from Robot Framework documentation
            if line.startswith('...'):
                line = line[3:].strip()

            req_text = None

            # Check for numbered list items (1. , 2. , etc.)
            numbered_match = re.match(r'^\d+\.\s+(.+)$', line)
            if numbered_match:
                req_text = numbered_match.group(1).strip()

            # Check for bulleted list items (- , * , etc.)
            if not req_text:
                bullet_match = re.match(r'^[-*]\s+(.+)$', line)
                if bullet_match:
                    req_text = bullet_match.group(1).strip()

            # If no list marker, treat as plain text requirement
            if not req_text and line:
                req_text = line

            if req_text:
                requirements.append(req_text)
                continue

            # If we already have requirements and this line doesn't match any pattern,
            # it might be the end of the requirements section
            if requirements and not line.startswith(('1', '2', '3', '4', '5', '6', '7', '8', '9', '-', '*')):
                break

        return requirements

    def get_data_from_chunk(self, xml_filepath):
        """
        Extract and structure data from a test chunk XML file.
        
        Args:
            xml_filepath: Path to the XML file containing a single test case
            
        Returns:
            Dictionary with test case data, or None if parsing fails
        """
        try:

            # Parse the XML file
            tree = ET.parse(xml_filepath)
            root = tree.getroot()
            
            # Find the suite element
            suite = root.find('.//suite')
            if suite is None:
                return {
                    'xml_file': xml_filepath,
                    'success': False,
                    'error': 'No suite element found in XML'
                }
            
            # Find the test element
            test = suite.find('test')
            if test is None:
                return {
                    'xml_file': xml_filepath,
                    'success': False,
                    'error': 'No test element found in XML'
                }
            
            # Extract test attributes
            test_name = test.get('name', '')
            test_id = test.get('id', '')
            
            # Extract test documentation if it exists
            test_doc_element = test.find('doc')
            test_doc = test_doc_element.text if test_doc_element is not None and test_doc_element.text else ''
            
            # Extract source path from suite if it exists
            test_source = suite.get('source', '')
            
            # Extract steps from documentation
            test_steps = self._extract_steps_from_documentation(test_doc)
            
            # Extract requirements from documentation
            test_requirements = self._extract_requirements_from_documentation(test_doc)
            
            # Get test status
            status_element = test.find('status')
            test_status = status_element.get('status', 'UNKNOWN') if status_element is not None else 'UNKNOWN'
            
            # Extract index from filename (format: idx_name_id.xml)
            filename = Path(xml_filepath).name
            idx_match = re.match(r'^(\d+)_', filename)
            idx = int(idx_match.group(1)) if idx_match else 0
            
            # Check if corresponding log file exists
            log_filepath = None
            xml_path = Path(xml_filepath)
            log_filename = xml_path.stem + '_log.html'
            potential_log = xml_path.parent / log_filename
            if potential_log.exists():
                log_filepath = str(potential_log)
            
            # Normalize test_source: lowercase and strip absolute path prefix
            # to make checksum portable across different repository locations.
            # Split on 'tests' or 'scripts' folder (whichever comes first) and keep from there.
            test_source_normalized = test_source.lower()
            for marker in ('/tests/', '/scripts/'):
                idx = test_source_normalized.find(marker)
                if idx != -1:
                    test_source_normalized = test_source_normalized[idx + 1:]
                    break

            # Calculate checksum based on test_name, documentation and normalized suite source path
            checksum_data = f"{test_name}{test_doc}{test_source_normalized}".encode('utf-8')
            checksum = hashlib.md5(checksum_data).hexdigest()

            # Extract interface prefix from XML content (if pattern configured)
            interface_prefix = self._extract_filename_prefix(test, suite, root) if self.filename_prefix_pattern else None

            # Build result dictionary
            result = {
                'index': idx,
                'test_name': test_name,
                'test_id': test_id,
                'status': test_status,
                'documentation': test_doc,
                'steps': test_steps,
                'requirements': test_requirements,
                'source': test_source,
                'xml_file': str(xml_filepath),
                'checksum': checksum,
                'success': True,
                'interface': interface_prefix,
            }

            # Add log file if it exists
            if log_filepath:
                result['log_file'] = log_filepath
            
            return result
            
        except ET.ParseError as e:
            return {
                'xml_file': str(xml_filepath),
                'success': False,
                'error': f'XML parsing error: {str(e)}'
            }
        except Exception as e:
            return {
                'xml_file': str(xml_filepath),
                'success': False,
                'error': f'Error reading chunk: {str(e)}'
            }

    def get_data_from_chunks(self, folder_path):
        """
        Collect data from all XML chunk files in a folder.
        
        This function scans a folder for XML files, calls get_data_from_chunk 
        for each file, and returns a list of all results.
        
        Args:
            folder_path: Path to the folder containing XML chunk files
            
        Returns:
            List of dictionaries, each containing data from one chunk XML file.
            Returns empty list if folder doesn't exist or contains no XML files.
        """
        results = []
        
        # Convert to Path object
        folder = Path(folder_path)
        
        # Check if folder exists
        if not folder.exists():
            self._debug_print(f"Error: Folder does not exist: {folder_path}")
            return results
        
        if not folder.is_dir():
            self._debug_print(f"Error: Path is not a directory: {folder_path}")
            return results
        
        # Find all XML files in the folder
        xml_files = sorted(folder.glob('*.xml'))
        
        if not xml_files:
            self._debug_print(f"Warning: No XML files found in {folder_path}")
            return results
        
        self._debug_print(f"Found {len(xml_files)} XML files in {folder_path}")
        
        # Process each XML file
        for xml_file in xml_files:
            self._debug_print(f"  Processing: {xml_file.name}")
            chunk_data = self.get_data_from_chunk(str(xml_file))
            results.append(chunk_data)
            
            # Print status
            if chunk_data.get('success', False):
                self._debug_print(f"    ✓ {chunk_data.get('test_name', 'Unknown')} - {chunk_data.get('status', 'Unknown')}")
            else:
                self._debug_print(f"    ✗ Error: {chunk_data.get('error', 'Unknown error')}")
        
        return results

    def _extract_filename_prefix(self, test, suite, root=None):
        """
        Extract a custom prefix for filenames from test case or suite setup messages.
        
        Uses the regex pattern provided in constructor to search XML messages
        and extract a prefix value for chunk filenames.
        
        Searches in this order:
        1. Current suite's SETUP keywords
        2. All parent suites' SETUP keywords (if root is provided)
        3. Test case keywords

        Args:
            test: Test case XML element
            suite: Suite XML element containing the test
            root: Root XML element (optional, for searching parent suites)

        Returns:
            Extracted prefix string (uppercase) or None if not found or pattern not set
        """
        if not self.filename_prefix_pattern:
            return None
        
        # Search in suite setup keywords first (current suite)
        for msg in suite.findall('.//kw[@type="SETUP"]//msg'):
            if msg.text:
                match = self.filename_prefix_pattern.search(msg.text)
                if match:
                    return match.group(1).upper()

        # Search in parent suites' SETUP keywords (if root is provided)
        if root is not None:
            suite_id = suite.get('id', '')
            # Build list of parent suite IDs: s1-s1-s1-s1 -> [s1-s1-s1, s1-s1, s1]
            parent_ids = []
            parts = suite_id.split('-')
            for i in range(len(parts) - 1, 0, -1):
                parent_ids.append('-'.join(parts[:i]))

            # Search in each parent suite
            for parent_id in parent_ids:
                parent_suite = root.find(f".//suite[@id='{parent_id}']")
                if parent_suite is not None:
                    for msg in parent_suite.findall('.//kw[@type="SETUP"]//msg'):
                        if msg.text:
                            match = self.filename_prefix_pattern.search(msg.text)
                            if match:
                                return match.group(1).upper()

        # Search in test case keywords
        for msg in test.findall('.//msg'):
            if msg.text:
                match = self.filename_prefix_pattern.search(msg.text)
                if match:
                    return match.group(1).upper()
        
        return None

    def split_to_chunks(self, output_xml_path, output_dir="chunked_results"):
        """
        Extract each test case from output.xml into separate XML files
        and generate HTML reports using rebot.

        Args:
            output_xml_path: Path to the output.xml file
            output_dir: Directory to store extracted test results
        """
        # Create output directory if it doesn't exist
        output_path = Path(output_dir)
        output_path.mkdir(exist_ok=True)

        # Parse the XML file
        tree = ET.parse(output_xml_path)
        root = tree.getroot()

        # Find all test cases
        test_cases = []
        for suite in root.findall('.//suite'):
            for test in suite.findall('test'):
                test_cases.append((suite, test))

        self._debug_print(f"Found {len(test_cases)} test cases")

        # Extract each test case
        for idx, (suite, test) in enumerate(test_cases, 1):
            test_name = test.get('name')
            test_id = test.get('id')
            
            # Extract filename prefix (if pattern is configured)
            prefix = self._extract_filename_prefix(test, suite, root)

            # Create a safe filename (with prefix if available)
            safe_name = test_name.replace(' ', '_').replace('/', '_').replace('\\', '_')
            if prefix:
                xml_filename = f"{idx}_{prefix}_{safe_name}_{test_id}.xml"
            else:
                xml_filename = f"{idx}_{safe_name}_{test_id}.xml"
            xml_filepath = output_path / xml_filename

            if prefix:
                self._debug_print(f"\n[{idx}/{len(test_cases)}] Processing: {test_name} (Prefix: {prefix})")
            else:
                self._debug_print(f"\n[{idx}/{len(test_cases)}] Processing: {test_name}")

            # Create a new XML document with only this test case
            new_root = ET.Element('robot', root.attrib)

            # Create a new suite element with the test case
            new_suite = ET.SubElement(new_root, 'suite')
            new_suite.attrib = suite.attrib.copy()

            # Copy suite source if it exists
            for source in suite.findall('source'):
                new_suite.append(copy.deepcopy(source))

            # Copy suite setup if exists (use deepcopy to avoid moving elements)
            for setup in suite.findall('kw[@type="SETUP"]'):
                new_suite.append(copy.deepcopy(setup))

            # Add the test case (use deepcopy to avoid moving the element)
            new_suite.append(copy.deepcopy(test))

            # Copy suite teardown if exists (use deepcopy to avoid moving elements)
            for teardown in suite.findall('kw[@type="TEARDOWN"]'):
                new_suite.append(copy.deepcopy(teardown))

            # Copy suite documentation if exists
            for doc in suite.findall('doc'):
                new_suite.append(copy.deepcopy(doc))

            # Don't copy suite status - it will be recalculated by rebot based on test status

            # Add statistics
            stats = ET.SubElement(new_root, 'statistics')

            # Total statistics
            total = ET.SubElement(stats, 'total')
            test_status = test.find('status').get('status')
            pass_count = '1' if test_status == 'PASS' else '0'
            fail_count = '1' if test_status == 'FAIL' else '0'
            skip_count = '1' if test_status == 'SKIP' else '0'

            ET.SubElement(total, 'stat', {
                'pass': pass_count,
                'fail': fail_count,
                'skip': skip_count
            }).text = 'All Tests'

            # Tag statistics
            tag_stats = ET.SubElement(stats, 'tag')
            for tag in test.findall('tag'):
                ET.SubElement(tag_stats, 'stat', {
                    'pass': pass_count,
                    'fail': fail_count,
                    'skip': skip_count
                }).text = tag.text

            # Suite statistics
            suite_stats = ET.SubElement(stats, 'suite')
            ET.SubElement(suite_stats, 'stat', {
                'name': suite.get('name'),
                'id': suite.get('id'),
                'pass': pass_count,
                'fail': fail_count,
                'skip': skip_count
            })

            # Add errors element (empty)
            ET.SubElement(new_root, 'errors')

            # Write the XML file
            new_tree = ET.ElementTree(new_root)
            ET.indent(new_tree, space='  ')
            new_tree.write(xml_filepath, encoding='UTF-8', xml_declaration=True)

            self._debug_print(f"  ✓ Created XML: {xml_filepath}")

            # Generate HTML report using rebot
            if prefix:
                log_filename = f"{idx}_{prefix}_{safe_name}_{test_id}_log.html"
            else:
                log_filename = f"{idx}_{safe_name}_{test_id}_log.html"
            log_filepath = output_path / log_filename

            try:
                cmd = [
                    'rebot',
                    '--output', 'NONE',
                    '--log', str(log_filepath),
                    '--name', test_name,
                    '--NoStatusRC',  # Don't set return code based on test status
                    str(xml_filepath)
                ]

                result = subprocess.run(
                    cmd,
                    capture_output=True,
                    text=True,
                    check=False
                )

                # With --NoStatusRC, rebot returns 0 on success regardless of test results
                # Only non-zero codes indicate actual errors (invalid data, missing files, etc.)
                if result.returncode == 0:
                    self._debug_print(f"  ✓ Generated log: {log_filepath}")
                else:
                    self._debug_print(f"  ✗ Failed to generate report (exit code: {result.returncode})")
                    if result.stderr:
                        self._debug_print(f"     Error: {result.stderr}")

            except FileNotFoundError:
                self._debug_print(f"  ✗ Error: rebot command not found. Please install robotframework.")
            except Exception as e:
                self._debug_print(f"  ✗ Error generating report: {str(e)}, index number = {idx}")
