import random
from collections import Counter, OrderedDict


MAX_RECURSION_DEPTH = 3

class LiteralParser:
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


class ConcatParser:
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
        return results

class AlternationParser:
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
        return results

class VariableParser:
    ''' A VariableParser allows us to refer to other named parsers in the grammar.
    So if we've defined a parser named "VROOT" in grammar g, the parser
    VariableParser(g, "VROOT") would refer to that parser. 

    VariableParser is the reason that all parsing functions take a paramater 
    "hist" ("history" or "histogram"), to avoid blowing the stack when the user
    has defined a left-recursive parser.  Every time VariableParser parses, it
    temporarily adds its name to a history counter.  When this history counter 
    exceeds some set threshold for an identifier, that's a sign we've recursed 
    too many times and should not recurse any further. '''

    def __init__(self, grammar, var):
        assert(var in grammar.tables)
        self.grammar, self.var = grammar, var
        self.counter = Counter([self.var])

    def __call__(self, input, hist, max_results=-1, randomize=False):
        assert(self.grammar[self.var].parser != None)
        if hist[self.var] >= MAX_RECURSION_DEPTH:
            return []
        return self.grammar[self.var].parser(input, hist + self.counter,
                                                   max_results, randomize)

