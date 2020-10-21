import random
from collections import Counter, OrderedDict


class Parser:

    def __call__(self, input, hist, max_results=-1, randomize=False):
        raise NotImplementedError()

    def __add__(self, other):
        return ConcatParser([self, other])

    def __or__(self, other):
        return AlternationParser([self, other])


class LiteralParser(Parser):
    ''' A LiteralParser recognizes a particular sequence of characters at the 
    beginning of an input. '''

    def __init__(self, tier, text):
        self.tier, self.text = tier, text

    def __call__(self, input, hist, max_results=-1, randomize=False):
        if self.tier not in input:  # generate rather than parse
            yield OrderedDict({self.tier: self.text }), input
            return
        if not input[self.tier].startswith(self.text):  # fail
            return
        result = input.copy()   # successful parse
        result[self.tier] = result[self.tier][len(self.text):]
        yield OrderedDict(), result


class ConcatParser(Parser):
    ''' A ConcatParser represents a sequence of parsers, e.g. a sequence of parsers
    to detect particular morphemes or morphemes of a given class. '''

    def __init__(self, children):
        self.children = children

    def __call__(self, input, hist, max_results=-1, randomize=False):

        results = [ (OrderedDict(), input) ]

        for child in self.children:
            new_results = []
            for o1, r1 in results:
                for o2, r2 in child(r1, hist, max_results, randomize):
                    combined_output = o1.copy()
                    for key in o2.keys():
                        if key in combined_output:
                            combined_output[key] += o2[key]
                            continue
                        combined_output[key] = o2[key]
                    new_results.append((combined_output, r2))
            results = new_results
            if max_results > 0:
                results = results[:max_results]
        yield from results

class AlternationParser(Parser):
    ''' An AlternationParser represents the choice between multiple parsers,
    e.g. between four lines of a paradigm, between 500 different roots, etc. 
    
    AlternationParser is the only parser affected by the randomize parameter,
    which causes it to (temporarily) shuffle its children before testing each
    option.  But note that the order of child parsers being random doesn't mean
    that the results as a whole are in a random order: results from the same
    child will still be next to each other.
    '''

    def __init__(self, children):
        self.children = children

    def __call__(self, input, hist, max_results=-1, randomize=False):
        results = []
        children = self.children
        if randomize:
            children = children[:]
            random.shuffle(children)
        for child in children:
            results += child(input, hist, max_results, randomize)
            if max_results > 0 and len(results) >= max_results:
               return results[:max_results]
        yield from results

class VariableParser(Parser):
    ''' A VariableParser allows us to refer to other named parsers in the grammar.
    So if we've defined a parser named "VROOT" in grammar g, the parser
    VariableParser(g, "VROOT") would refer to that parser. 

    VariableParser is the reason that all parsing functions take a paramater 
    "hist" ("history" or "histogram"), to avoid blowing the stack when the user
    has defined a left-recursive parser.  Every time VariableParser parses, it
    temporarily adds its name to a history counter.  When this history counter 
    exceeds some set threshold for an identifier, that's a sign we've recursed 
    too many times and should not recurse any further. '''

    def __init__(self, symbol_table, var, max_recursion=3):

        if var not in symbol_table:
            raise KeyError(f"Variable {var} not defined")
        self.symbol_table, self.var = symbol_table, var
        self.counter = Counter([self.var])
        self.max_recursion = max_recursion

    def __call__(self, input, hist, max_results=-1, randomize=False):
        assert(self.var in self.symbol_table)
        if hist[self.var] >= self.max_recursion:
            return []
        yield from self.symbol_table[self.var](input, hist + self.counter,
                                                   max_results, randomize)
