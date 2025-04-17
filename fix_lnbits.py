#!/usr/bin/env python3
"""
This script fixes the syntax error in the lnbits.py file.
"""

import os

def fix_lnbits_file():
    """Fix the syntax error in the lnbits.py file."""
    # Path to the lnbits.py file
    file_path = os.path.join('api', 'lnbits.py')
    
    # Read the file content
    with open(file_path, 'r') as f:
        content = f.read()
    
    # Check if there's a duplicate method at the end
    if '# End of class' in content:
        # Find the position of the duplicate method
        pos = content.find('# End of class')
        
        # Truncate the file at that position
        content = content[:pos]
        
        # Write the fixed content back to the file
        with open(file_path, 'w') as f:
            f.write(content)
        
        print(f"Fixed {file_path}")
    else:
        print(f"No issues found in {file_path}")

if __name__ == '__main__':
    fix_lnbits_file()
