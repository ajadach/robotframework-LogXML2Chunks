#!/usr/bin/env python3
"""
Command-line interface for robotframework-LogXML2Chunks.
"""

import argparse
import sys
from pathlib import Path
from .LogXML2Chunks import LogXML2Chunks


def main():
    """Main entry point for the command-line interface."""
    parser = argparse.ArgumentParser(
        description='Extract individual test cases from Robot Framework output.xml',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Basic usage
  %(prog)s output.xml
  
  # Specify output directory
  %(prog)s output.xml --output-dir my_chunks
  
  # Show version
  %(prog)s --version
"""
    )
    
    parser.add_argument(
        'input_xml',
        type=str,
        help='Path to Robot Framework output.xml file'
    )
    
    parser.add_argument(
        '-o', '--output-dir',
        type=str,
        default='chunked_results',
        help='Output directory for chunked results (default: chunked_results)'
    )
    
    parser.add_argument(
        '-v', '--version',
        action='version',
        version='%(prog)s 1.0.0'
    )
    
    parser.add_argument(
        '--verbose',
        action='store_true',
        help='Enable verbose output'
    )
    
    args = parser.parse_args()
    
    # Validate input file exists
    input_path = Path(args.input_xml)
    if not input_path.exists():
        print(f"Error: Input file '{args.input_xml}' not found.", file=sys.stderr)
        sys.exit(1)
    
    if not input_path.is_file():
        print(f"Error: '{args.input_xml}' is not a file.", file=sys.stderr)
        sys.exit(1)
    
    # Initialize chunker and process
    try:
        chunker = LogXML2Chunks()
        results = chunker.split_to_chunks(
            output_xml_path=str(input_path),
            output_dir=args.output_dir
        )
        
        # Summary
        print(f"\n{'='*70}")
        print(f"Summary:")
        print(f"{'='*70}")
        print(f"Total test cases: {len(results)}")
        
        successful = sum(1 for r in results if r['success'])
        failed = len(results) - successful
        
        print(f"Successfully processed: {successful}")
        if failed > 0:
            print(f"Failed: {failed}")
        
        print(f"Output directory: {Path(args.output_dir).absolute()}")
        
        if args.verbose:
            print(f"\nDetailed Results:")
            for result in results:
                status_icon = "✓" if result['success'] else "✗"
                print(f"  {status_icon} [{result['index']}] {result['test_name']} - {result['status']}")
                if not result['success']:
                    print(f"      Error: {result.get('error', 'Unknown error')}")
        
        # Exit with error code if any failed
        sys.exit(0 if failed == 0 else 1)
        
    except Exception as e:
        print(f"Error: {str(e)}", file=sys.stderr)
        if args.verbose:
            import traceback
            traceback.print_exc()
        sys.exit(1)


if __name__ == '__main__':
    main()
