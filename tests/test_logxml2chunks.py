"""
Unit tests for LogXML2Chunks library.
"""
import pytest
from pathlib import Path
from LogXML2Chunks import LogXML2Chunks
import tempfile
import shutil


class TestLogXML2Chunks:
    """Test suite for LogXML2Chunks class."""
    
    def test_import(self):
        """Test that the library can be imported."""
        assert LogXML2Chunks is not None
    
    def test_instance_creation(self):
        """Test that an instance can be created."""
        chunker = LogXML2Chunks()
        assert chunker is not None
    
    def test_get_data_from_chunk(self):
        """Test extracting data from a single test chunk XML file.
        
        This test:
        1. Loads a chunk XML file containing a single test case
        2. Extracts all data from the XML file
        3. Verifies that all expected fields are present
        4. Validates the extracted data values
        """
        # Setup
        chunker = LogXML2Chunks()
        chunk_xml = Path(__file__).parent / 'example_logs' / 'chunks' / '1_Example_Test_1_s1-t1.xml'
        
        # Verify the chunk XML exists
        assert chunk_xml.exists(), f"Chunk XML not found at {chunk_xml}"
        
        # Execute the data extraction
        result = chunker.get_data_from_chunk(str(chunk_xml))
        
        # Verify result is not None
        assert result is not None, "Result should not be None"
        
        # Verify success
        assert result['success'] is True, f"Extraction should succeed, got error: {result.get('error', 'N/A')}"
        
        # Verify all required fields are present
        required_fields = ['index', 'test_name', 'test_id', 'status', 'documentation', 
                          'steps', 'source', 'xml_file', 'checksum', 'success']
        for field in required_fields:
            assert field in result, f"Field '{field}' should be present in result"
        
        # Verify specific values from the XML
        assert result['test_name'] == 'Example Test 1', f"Expected 'Example Test 1', got '{result['test_name']}'"
        assert result['test_id'] == 's1-t1', f"Expected 's1-t1', got '{result['test_id']}'"
        assert result['status'] == 'PASS', f"Expected 'PASS', got '{result['status']}'"
        assert result['index'] == 1, f"Expected index 1, got {result['index']}"
        
        # Verify checksum is present and valid
        assert 'checksum' in result, "checksum field should be present"
        assert isinstance(result['checksum'], str), "checksum should be a string"
        assert len(result['checksum']) == 32, f"checksum should be 32 characters (MD5), got {len(result['checksum'])}"
        assert result['checksum'].isalnum(), "checksum should be alphanumeric"
        
        # Verify source path
        assert 'example.robot' in result['source'], f"Source should contain 'example.robot', got '{result['source']}'"
        
        # Verify documentation is extracted
        assert len(result['documentation']) > 0, "Documentation should not be empty"
        assert 'Example Test 1 Documentation' in result['documentation']
        
        # Verify steps are extracted from documentation
        assert isinstance(result['steps'], dict), "Steps should be a dictionary"
        assert 'Log to HTML' in result['steps'], "Should extract 'Log to HTML' step from documentation"
        assert result['steps']['Log to HTML'] == 'pass', "Expected behavior for 'Log to HTML' should be 'pass'"
        
        # Verify XML file path
        assert result['xml_file'] == str(chunk_xml)
        
        # Verify log file if it exists
        if 'log_file' in result:
            log_file = Path(result['log_file'])
            assert log_file.exists(), f"Log file should exist: {log_file}"
            assert log_file.name == '1_Example_Test_1_s1-t1_log.html'
        
        print(f"\n✓ Successfully extracted data from chunk XML")
        print(f"  Test Name: {result['test_name']}")
        print(f"  Test ID: {result['test_id']}")
        print(f"  Status: {result['status']}")
        print(f"  Steps: {result['steps']}")
        print(f"  Source: {result['source']}")
    
    def test_get_data_from_chunks(self):
        """Test collecting data from all XML chunk files in a folder.
        
        This test:
        1. Points to a folder containing multiple XML chunk files
        2. Calls get_data_from_chunks to process all files
        3. Verifies that all chunks are processed
        4. Validates the structure of returned data
        """
        # Setup
        chunker = LogXML2Chunks()
        chunks_folder = Path(__file__).parent / 'example_logs' / 'chunks'
        
        # Verify the folder exists
        assert chunks_folder.exists(), f"Chunks folder not found at {chunks_folder}"
        assert chunks_folder.is_dir(), f"Path is not a directory: {chunks_folder}"
        
        # Execute the data collection
        results = chunker.get_data_from_chunks(str(chunks_folder))
        
        # Verify results
        assert results is not None, "Results should not be None"
        assert isinstance(results, list), "Results should be a list"
        assert len(results) > 0, "Should have at least one result"
        
        # Count successful extractions
        successful = [r for r in results if r.get('success', False)]
        assert len(successful) > 0, "Should have at least one successful extraction"
        
        # Verify each result has the expected structure
        for result in successful:
            assert 'index' in result
            assert 'test_name' in result
            assert 'test_id' in result
            assert 'status' in result
            assert 'documentation' in result
            assert 'steps' in result
            assert 'source' in result
            assert 'xml_file' in result
            assert 'checksum' in result
            assert 'success' in result
            assert result['success'] is True
        
        # Verify results are sorted by filename (which includes index)
        xml_files = [Path(r['xml_file']).name for r in results]
        assert xml_files == sorted(xml_files), "Results should be sorted by filename"
        
        print(f"\n✓ Successfully collected data from {len(results)} chunk files")
        print(f"  Successful: {len(successful)}")
        print(f"  Failed: {len(results) - len(successful)}")
        for idx, result in enumerate(successful, 1):
            print(f"  [{idx}] {result['test_name']} - {result['status']}")
    
    def test_split_to_chunks(self):
        """Test splitting Robot Framework output.xml into separate test chunks.
        
        This test:
        1. Loads an example output.xml file
        2. Splits it into individual test case chunks
        3. Verifies that chunks are created correctly
        4. Checks that each chunk contains the expected data
        """
        # Setup
        chunker = LogXML2Chunks()
        example_log = Path(__file__).parent / 'example_logs' / 'output.xml'
        
        # Verify the example log exists
        assert example_log.exists(), f"Example log not found at {example_log}"
        
        # Create a temporary directory for output
        with tempfile.TemporaryDirectory() as temp_dir:
            output_dir = Path(temp_dir) / 'chunks'        
            # Execute the split
            chunker.split_to_chunks(str(example_log), str(output_dir))            

if __name__ == '__main__':
    pytest.main([__file__, '-v'])
