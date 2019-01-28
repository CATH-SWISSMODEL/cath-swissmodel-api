#!/usr/bin/env python3

"""
CLI tool to submit/retrieve models from alignment data
"""

from apiclient.clients import SMAlignmentClient

def main():
    client = SMAlignmentClient.new_from_cli()
    client.run()

if __name__ == '__main__':
    main()