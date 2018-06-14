"""
A Shakespeare Programming Language (SPL) to Java translator.
SPL is an esoteric programming language defined
[here](http://shakespearelang.sourceforge.net/report/shakespeare).
@author Ryan Dancy
"""


import argparse
import re
from splerror import SplError
from translator import translate


def translate_file(in_filename, java_classname):
    """
    Translate the SPL contents of the file with name in_filename
    to Java, outputting to out_filename. Note that the file extensions
    are appended.
    
    :param in_filename: the input SPL filename.
    :param java_classname: the name of the output Java class; the filename is {java_classname}.java.
    :raises FileNotFoundError: if in_filename does not exist
    """

    out_filename = java_classname + '.java'

    # parse in_filename and output to out_filename
    
    with open(in_filename, 'r') as spl_file:
        spl = spl_file.read()

    try:
        java = translate(spl, java_classname)
    except SplError as e:
        error = e.args[0]
        print('Compilation error:')
        print(error)
        return

    with open(out_filename, 'w') as java_file:
        java_file.write(java)

    print('Output successfully to', out_filename)


def main():
    """Get in/out files from the command-line arguments and pass to translate()."""
    parser = argparse.ArgumentParser(description='SPL to Java translator.')
    parser.add_argument('spl_file', type=str, help='The file containing SPL code to be translated to Java.')
    parser.add_argument('java_class_name', type=str, help='The name of the output Java class. Cannot contain '
                        'spaces. The output Java file will be {java_class_name}.java.')
    args = parser.parse_args()

    spl_file = args.spl_file
    java_class_name = args.java_class_name
    if not re.search(r'^[A-Za-z_][A-Za-z0-9_]*$', java_class_name):
        print('The Java class name must be a valid Java class name.')
        return

    try:
        translate_file(spl_file, java_class_name)
    except FileNotFoundError:
        print('SPL file does not exist.')


if __name__ == '__main__':
    main()
