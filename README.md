# grable
A simple tabular language for making rule-based linguistic parser/generators

## Motivation

The primary goal of Grable is to allow subject-matter experts (e.g. teachers, non-computational linguists) to make rule-based parsers and generators more easily.

When making rule-based linguistic artifacts (e.g., morphological parsers or generators), there is often a disconnect between the expression of linguistic knowledge by a subject-matter expert (who in our experience is often working in a spreadsheet) and the linguist-programmer (who translates that domain knowledge into a linguistic programming language like XFST).  Even when the linguist-programmer is working directly in a text programming language, we notice that they often use tabs/spaces to try to turn the code into a spreadsheet itself.  Tabular organization of some sort is inherent in this domain (or how humans conceptually organize that domain into programs).

Grable is a formalism for the *direct* interpretation of spreadsheets as grammars, so that the specification of a grammar in tabular form is also the interpreted code that parses/generates this grammar.  

| VSTEM | surf | gloss |
|:----:|:----:|:----:|
| | hamx'id | eat |
| | qotl | know |
| | galulhx'id | steal |


| VERB | var | surface | gloss |
|:----:|:----:|:----:|:----:|
| | VSTEM | an | -1SG |
| | VSTEM | s | -2SG |
| | VSTEM | ux | -3SG.MED |
| | VSTEM | i | -3SG.DIST |

The above tables are both the description of the grammar and the code that, properly interpreted, converts "hamx'idux" to "eat-3SGMED" or vice-versa.

## Grable in comparison to other linguistic programming languages

Grable is not exactly a *replacement* for other linguistic programming languages like XFST.  Although it can do string-to-string transduction, it is more broadly a way to *combine* string-to-string transductions into dictionary-to-dictionary transductions.  (The name of the parsing paradigm, ``parser combinators", is illustrative: it describes a way of *combining* parsers.)  These string-to-string transductions might be written in another language, or learned from data.  (We haven't implemented cross-language integration yet, though.  You can get quite a lot of mileage out of the very basic transduction primitives here.)
