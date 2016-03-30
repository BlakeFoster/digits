import operator
from itertools import chain


class Stick(object):
    """
    A single matchstick.
    """
    def __init__(self, row, column, orientation):
        self.row = row
        self.column = column
        self.orientation = orientation

    def __eq__(self, other):
        return self.row == other.row and self.column == other.column and self.orientation == other.orientation

    def __ne__(self, other):
        return self.row != other.row or self.column != other.column or self.orientation != other.orientation

    def __hash__(self):
        return hash((self.row, self.column, self.orientation))

    def __repr__(self):
        return "%s(%s, %s, %s.%s)" % (
            self.__class__.__name__,
            self.row,
            self.column,
            self.__class__.__name__,
            "VERTICAL" if self.is_vertical else "HORIZONTAL"
        )

    @property
    def is_vertical(self):
        return self.orientation == self.VERTICAL

    @property
    def is_horizontal(self):
        return self.orientation == self.HORIZONTAL

    VERTICAL = "|"
    HORIZONTAL = "_"


class StickCollection(object):
    """
    An arbitrary collection of sticks.  Supports position-invariant equality-testing.
    """
    def __init__(self, sticks):
        self.sticks = sticks if isinstance(sticks, frozenset) else frozenset(sticks)

        min_row = min(stick.row for stick in self.sticks) if self.sticks else 0
        min_col = min(stick.column for stick in self.sticks) if self.sticks else 0

        self.normalized_sticks = frozenset(
            Stick(
                stick.row - min_row,
                stick.column - min_col,
                stick.orientation
            )
            for stick in self.sticks
        )
        self._removal_set = None

    @property
    def removal_set(self):
        """
        The set of all StickCollections that we can create by removing exactly one stick.
        """
        if self._removal_set is None:
            self._removal_set = {
                self - stick
                for stick in self.sticks
            }
        return self._removal_set

    def __add__(self, stick):
        """
        Return a copy of self with the given stick added.
        """
        return StickCollection(
            frozenset(chain(self.sticks, [stick]))
        )

    def __sub__(self, stick):
        """
        Return a copy of self with the given stick removed.
        """
        if stick not in self.sticks:
            return self
        return StickCollection(
            sticks=self.sticks - {stick}
        )

    def __iter__(self):
        return iter(self.sticks)

    def __eq__(self, other):
        return self.normalized_sticks == other.normalized_sticks

    def __ne__(self, other):
        return self.normalized_sticks != other.normalized_sticks

    def __hash__(self):
        return hash(self.normalized_sticks)

    def __len__(self):
        return len(self.sticks)

    @classmethod
    def _sticks_from_dict(self, stick_dict):
        for row_id in sorted(stick_dict.keys()):
            row_sticks = stick_dict[row_id]
            for col_id in sorted(row_sticks.keys()):
                col_sticks = row_sticks[col_id]
                for orientation in col_sticks:
                    yield Stick(row_id, col_id, orientation)

    @classmethod
    def from_dict(cls, stick_dict):
        """
        Create a StickCollection from a dict of the form {row: {column: [orientations]}}
        """
        return cls(cls._sticks_from_dict(stick_dict))


_DIGIT_STICKS = StickCollection.from_dict(
    {
        0: {1: [Stick.HORIZONTAL]},
        4: {0: [Stick.VERTICAL], 1: [Stick.HORIZONTAL], 2: [Stick.VERTICAL]},
        8: {0: [Stick.VERTICAL], 1: [Stick.HORIZONTAL], 2: [Stick.VERTICAL]}
    }   
)


_OPERATOR_STICKS = StickCollection.from_dict(
    {
        1: {1: [Stick.HORIZONTAL]},
        2: {1: [Stick.HORIZONTAL]},
        3: {1: [Stick.HORIZONTAL]},
        4: {1: [Stick.VERTICAL]},
    }
)


class Symbol(object):
    """
    A digit or arithmetic operator.
    """

    def __init__(self, sticks, code, name, display_code=None):
        self.name = name
        self.sticks = sticks
        self.code = code
        self.display_code = unicode(code) if display_code is None else display_code

    def __eq__(self, other):
        return self.sticks == other.sticks

    def __ne__(self, other):
        return self.sticks != other.sticks__

    def __hash__(self):
        return hash(self.sticks)

    def is_reachable_from(self, other):
        """
        Returns True if and only if we can make the given Symbol instance identical to this instance by adding exactly
        one stick.
        """
        if len(self.sticks) != len(other.sticks) + 1:
            return False
        for stick in self.sticks:
            if other.sticks == self.sticks - stick:
                return True
        return False

    @property
    def removal_set(self):
        """
        The set of symbols that we can obtain by removing a single stick.  May not be valid digits or operators.
        """
        return {
            Symbol(sticks, None, None)
            for sticks in self.sticks.removal_set
        }

    @classmethod
    def with_pattern(cls, pattern, *args, **kwargs):
        """
        Hackery to make constructing the possible digits/operators less painful.
        """
        all_sticks = set(cls._get_all_sticks())
        all_cols = sorted({stick.column for stick in all_sticks})
        all_rows = sorted({stick.row for stick in all_sticks})
        sticks = set()
        for row_id, row_pattern in zip(all_rows, pattern):
            for col_id, pattern_value in zip(all_cols, row_pattern):
                if pattern_value == "|":
                    pattern_value_sticks = [Stick(row_id, col_id, Stick.VERTICAL)]
                elif pattern_value == "_":
                    pattern_value_sticks = [Stick(row_id, col_id, Stick.HORIZONTAL)]
                elif pattern_value == "+":
                    pattern_value_sticks = [Stick(row_id, col_id, Stick.VERTICAL), Stick(row_id, col_id, Stick.HORIZONTAL)]
                elif pattern_value == " ":
                    pattern_value_sticks = []
                else:
                    raise ValueError(pattern)
                sticks.update(pattern_value_sticks)
        if sticks - all_sticks:
            raise ValueError(pattern)
        return cls(StickCollection(sticks), *args, **kwargs)


class Digit(Symbol):
    """
    A single digit.
    """
    def __init__(self, sticks, value, name, display_code=None):
        super(Digit, self).__init__(sticks, str(value), name, display_code)
        self.value = value

    @classmethod
    def _get_all_sticks(cls):
        """
        Hackery to make constructing the operators digits less painful.
        """
        return _DIGIT_STICKS


class Operator(Symbol):
    """
    An arithmetic operator.
    """

    @classmethod
    def _get_all_sticks(cls):
        """
        Hackery to make constructing the operators operators less painful.
        """
        return _OPERATOR_STICKS


class EqualityOperator(Operator):
    """
    The = or != sign.
    """


class SymbolCollection(object):
    def __init__(self, symbols):
        """
        A collection of available symbols.  Caches the possible substitutions.
        """
        self.symbols = symbols
        self.reachable_with_addition_by_symbol = {}
        self.reachable_with_removal_by_symbol = {}
        self.reachable_with_move_by_symbol = {}
        for symbol_in in symbols:
            self.reachable_with_removal_by_symbol.setdefault(symbol_in, set())
            self.reachable_with_addition_by_symbol.setdefault(symbol_in, set())
            self.reachable_with_move_by_symbol.setdefault(symbol_in, set())
            for symbol_out in symbols:
                if symbol_out.is_reachable_from(symbol_in):
                    self.reachable_with_addition_by_symbol[symbol_in].add(symbol_out)
                if symbol_in.is_reachable_from(symbol_out):
                    self.reachable_with_removal_by_symbol[symbol_in].add(symbol_out)
            for intermediate in symbol_in.removal_set:
                for symbol_out in symbols:
                    if symbol_out.is_reachable_from(intermediate):
                        self.reachable_with_move_by_symbol[symbol_in].add(symbol_out)

    def __iter__(self):
        return iter(self.symbols)


class Expression(object):
    """
    A sequence of symbols that can be evaluated.
    """
    def __init__(self, symbols):
        self.symbols = symbols

    def substitute_symbol(self, new_symbol, index):
        """
        Replace the symbol at the given index with a new symbol.
        """
        new_symbols = [s for s in self.symbols]
        new_symbols[index] = new_symbol
        return Expression(new_symbols)

    @property
    def code(self):
        """
        A string of Python code equivalent to this expression.
        """
        return "".join(s.code for s in self.symbols)

    @property
    def display_code(self):
        """
        For display only, to make the console output more readable.
        """
        return u"".join(s.display_code for s in self.symbols)

    def __iter__(self):
        return iter(self.symbols)

    def __getitem__(self, index):
        return self.symbols[index]

    def evaluate(self):
        """
        Execute the expression and return the result. Raises a ValueError if the expression is not valid.
        """
        equality_operators = [i for i, s in enumerate(self.symbols) if isinstance(s, EqualityOperator)]
        if len(equality_operators) > 1:
            boundaries = zip(
                [-1] + equality_operators[:-1], equality_operators[1:] + [len(self.symbols)])
            equality_subexpressions = [
                Expression(
                    self.symbols[
                        (low + 1):high
                    ]
                )
                for (low, high) in boundaries
            ]
            result = True
            for exp in equality_subexpressions:
                result = result and exp.evaluate()
            return result
        else:
            try:
                # Got lazy here, sorry.
                return eval(self.code)
            except SyntaxError:
                raise ValueError(self.code)


blank = Digit.with_pattern(
    [
        "   ",
        "   ",
        "   "
    ],
    value="",
    name="blank"
)

zero = Digit.with_pattern(
    [
        " _ ",
        "| |",
        "|_|"
    ],
    value=0,
    name="zero"
)

one_a = Digit.with_pattern(
    [
        "   ",
        "|  ",
        "|  "
    ],
    value=1,
    name="one_double"
)

one_b = Digit.with_pattern(
    [
        "   ",
        "|  ",
        "   "
    ],
    value=1,
    name="one_single"
)

two = Digit.with_pattern(
    [
        " _ ",
        " _|",
        "|_ "
    ],
    value=2,
    name="two"
)

three = Digit.with_pattern(
    [
        " _ ",
        " _|",
        " _|"
    ],
    value=3,
    name="three"
)

four = Digit.with_pattern(
    [
        "   ",
        "|_|",
        "  |"
    ],
    value=4,
    name="four"
)

five = Digit.with_pattern(
    [
        " _ ",
        "|_ ",
        " _|"
    ],
    value=5,
    name="five"
)

six_a = Digit.with_pattern(
    [
        " _ ",
        "|_ ",
        "|_|"
    ],
    value=6,
    name="six"
)

six_b = Digit.with_pattern(
    [
        "   ",
        "|_ ",
        "|_|"
    ],
    value=6,
    name="six_alt"
)

seven_a = Digit.with_pattern(
    [
        " _ ",
        "  |",
        "  |"
    ],
    value=7,
    name="seven"
)

seven_b = Digit.with_pattern(
    [
        " _ ",
        "| |",
        "  |"
    ],
    value=7,
    name="seven_alt"
)

eight = Digit.with_pattern(
    [
        " _ ",
        "|_|",
        "|_|"
    ],
    value=8,
    name="eight"
)

nine_a = Digit.with_pattern(
    [
        " _ ",
        "|_|",
        "  |"
    ],
    value=9,
    name="nine"
)

nine_b = Digit.with_pattern(
    [
        " _ ",
        "|_|",
        " _|"
    ],
    value=9,
    name="nine_alt"
)


plus_a = Operator.with_pattern(
    [
        "_",
        " ",
        " ",
        "|"
    ],
    name="plus_high",
    code="+"
)

plus_b = Operator.with_pattern(
    [
        " ",
        "_",
        " ",
        "|"
    ],
    name="plus",
    code="+"
)

plus_c = Operator.with_pattern(
    [
        " ",
        " ",
        "_",
        "|"
    ],
    name="plus_low",
    code="+"
)

minus = Operator.with_pattern(
    [
        "_",
        " ",
        " ",
        " "
    ],
    name="minus",
    code="-"
)

eq_a = EqualityOperator.with_pattern(
    [
        "_",
        "_",
        " ",
        " "
    ],
    name="eq",
    code="==",
    display_code=u"="
)

eq_b = EqualityOperator.with_pattern(
    [
        "_",
        " ",
        "_",
        " "
    ],
    name="eq_alt",
    code="==",
    display_code=u"="
)

neq_a = EqualityOperator.with_pattern(
    [
        "_",
        "_",
        " ",
        "|"
    ],
    name="neq_high",
    code="!=",
    display_code=u"\u2260"
)

neq_b = EqualityOperator.with_pattern(
    [
        "_",
        " ",
        "_",
        "|"
    ],
    name="neq",
    code="!=",
    display_code=u"\u2260"
)
neq_c = EqualityOperator.with_pattern(
    [
        " ",
        "_",
        "_",
        "|"
    ],
    name="neq_low",
    code="!=",
    display_code=u"\u2260"
)

DIGITS = [
    blank,
    zero,
    one_a,
    one_b,
    two,
    three,
    four,
    five,
    six_a,
    six_b,
    seven_a,
    seven_b,
    eight,
    nine_a,
    nine_b
]

OPERATORS = [
    plus_a,
    plus_b,
    plus_c,
    minus,
    eq_a,
    eq_b,
    neq_a,
    neq_b,
    neq_c
]

symbols = SymbolCollection(DIGITS + OPERATORS)

expression = Expression(
    [blank, six_a, blank, plus_b, blank, four, blank, eq_b, blank, four, blank]
)

print plus_a.removal_set


def _test_substitution(source_index, dest_index, new_source_symbol, new_dest_symbol):
    """
    Check if the given substitution produces a True expression.  If so, add it to the dict.
    """
    new_expression = expression.substitute_symbol(
        new_source_symbol,
        source_index
    ).substitute_symbol(
        new_dest_symbol,
        dest_index
    )
    try:
        result = new_expression.evaluate()
    except ValueError:
        return
    else:
        if result is True:
            valid_substitutions.setdefault(
                source_index,
                {}
            ).setdefault(
                dest_index,
                {}
            ).setdefault(
                new_source_symbol.code,
                {}
            )[new_dest_symbol.code] = new_expression


valid_substitutions = {}
for source_index, source_symbol in enumerate(expression):
    for dest_index, dest_symbol in enumerate(expression):
        if source_index == dest_index:
            pass
            for new_symbol in symbols.reachable_with_move_by_symbol[source_symbol]:
                _test_substitution(source_index, dest_index, new_symbol, new_symbol)
        else:
            for new_source_symbol in symbols.reachable_with_removal_by_symbol[source_symbol]:
                for new_dest_symbol in symbols.reachable_with_addition_by_symbol[dest_symbol]:
                    _test_substitution(source_index, dest_index, new_source_symbol, new_dest_symbol)

for source_id, subs_by_dest in valid_substitutions.iteritems():
    for dest_id, subs_by_source_code in subs_by_dest.iteritems():
        for subs_by_dest_code in subs_by_source_code.itervalues():
            for sub in subs_by_dest_code.itervalues():
                print u"%s/%s: %s" % (
                    expression[source_id].display_code,
                    expression[dest_id].display_code,
                    sub.display_code
                )
