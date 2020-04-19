import csv
import os

def csv_iterator(filename):
    with open('tests/test.csv', 'r', newline='', encoding='utf-8') as fin:
        yield from enumerate(csv.reader(fin))

def is_line_empty(line):
    ''' Is the line a comment, or consists solely of empty cells? '''
    if not line:
        return True
    if line[0].strip().startswith("#"):
        return True
    return not any(cell.strip() for cell in line)


def parse_csv(filename, syntax_errors):
    stanzas = []
    syntax_errors = []

    parse_mode = "TABLE"

    basename = os.path.basename(filename)

    for rownum, tokens in csv_iterator(filename):
        if is_line_empty(tokens):
            continue
        assert(len(tokens) > 0)
        symbol_name = tokens[0].strip()

        if symbol_name.lower() == "table":
            parse_mode = "TABLE"

        if symbol_name:  # it's a new stanza
            new_stanza = Stanza(basename, rownum, parse_mode, tokens, syntax_errors)
            stanzas.append(new_stanza)
            continue

        # otherwise it belongs to a previous stanza
        if not stanzas:
            # oops, there's a continuation line but it's not continuing anything
            syntax_errors.append({"filename": filename,
                                    "row": rownum,
                                    "message": "This line should belong to a previous symbol, but no symbol precedes it."})
            continue

        stanzas[-1].add_line(basename, rownum, tokens, syntax_errors)

class TableCompiler:
    ''' Compiles a Stanza into a Table '''

    def __init__(self, stanza, symbol_table):



class Stanza:
    ''' A Stanza is a series of spreadsheet rows that are interpreted as a unit '''

    def __init__(self, filename, rownum, parse_mode, tokens, syntax_errors):
        self.lines = []
        self.parse_mode = parse_mode
        assert(len(tokens) > 0)
        self.symbol_name = tokens[0].strip()
        self.lines = []
        self.colheaders = {}
        for colnum, token in enumerate(tokens[1:]):
            if not token.strip():
                continue
            self.colheaders[colnum+1] = token.strip()


    def add_line(self, filename, rownum, tokens, syntax_errors):
        line = []
        assert(len(tokens) > 0)
        assert(tokens[0].strip() == '')
        for colnum, token in enumerate(tokens[1:]):
            if not token.strip():
                continue
            if colnum+1 not in self.colheaders:
                syntax_errors.append({"filename": filename, 
                                      "row": rownum,
                                      "col": colnum,
                                      "message": "Cell does not belong to a column header."})
                continue
            colheader = self.colheaders[colnum+1]
            line.append((filename, rownum, colnum+1, colheader, token.strip()))
            print((filename, rownum, colnum+1, colheader, token.strip()))
        self.lines.append(line)    

errors = []
parse_csv("tests/test.csv", errors)
print(errors)