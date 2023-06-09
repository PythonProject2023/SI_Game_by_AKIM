from .parser import parse_package
import sys

if __name__ == '__main__':
    parse_package(sys.argv[1])