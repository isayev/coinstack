"""Quick test of parsing script - shows sample output."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

from parse_collection import DataConverter

def main():
    excel_path = Path("../collection-v1.xlsx")
    
    print("Testing data conversion...")
    print("=" * 60)
    
    converter = DataConverter()
    converted_data = converter.process_file(excel_path)
    
    print(f"\n✅ Converted {len(converted_data)} coins")
    
    # Show first coin as example
    if converted_data:
        import json
        print("\n" + "=" * 60)
        print("Sample converted coin (first one):")
        print("=" * 60)
        print(json.dumps(converted_data[0], indent=2, ensure_ascii=False, default=str))
        
        # Show statistics
        print("\n" + "=" * 60)
        print("Conversion Statistics:")
        print("=" * 60)
        report = converter.get_report()
        print(f"Total rows: {report['stats']['total_rows']}")
        print(f"Successfully converted: {report['stats']['processed']}")
        print(f"Skipped: {report['stats']['skipped']}")
        print(f"Errors: {report['stats']['errors']}")
        print(f"Warnings: {len(report['warnings'])}")
        
        # Show field coverage
        if converted_data:
            sample = converted_data[0]
            print(f"\nFields populated in sample coin: {len([k for k, v in sample.items() if v is not None])}")
            print("Fields:", ", ".join(sorted(sample.keys())))

if __name__ == "__main__":
    main()
