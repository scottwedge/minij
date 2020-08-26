import re
import sys

from .token import Token

class Lexer:
    def __init__(self):
        self.__symbols__ = [
            "+",
            "-",
            "*",
            "/",
            "%",
            "<",
            "=",
            ">",
            "!",
            "&",
            "|",
            ";",
            ",",
            ".",
            "[",
            "]",
            "(",
            ")",
            "{",
            "}",
        ]
        self.__single_operator__ = [
            "+",
            "-",
            "*",
            "/",
            "%",
            "<",
            ">",
            "=",
            "!",
            ";",
            ",",
            ".",
            "[",
            "]",
            "(",
            ")",
            "{",
            "}",
        ]
        self.__double_operator__ = [
            "<=",
            ">=",
            "==",
            "!=",
            "&&",
            "||",
            "[]",
            "()",
            "{}",
        ]
        self.__reserved_words__ = [
            "void",
            "int",
            "double",
            "boolean",
            "string",
            "class",
            "const",
            "interface",
            "null",
            "this",
            "extends",
            "implements",
            "for",
            "while",
            "if",
            "else",
            "return",
            "break",
            "New",
            "System",
            "out",
            "println",
        ]
        self.__analysis__ = []

    def get_lexeme(self, lines):
        word = ""
        symbol = False
        string = False
        single = False
        single_number = 0
        multiline = False

        for line, text in lines.items():
            # Verify that no string is open
            if string:
                self.__add_error__(word, line - 1, col, "Unfinished string")
                word = ""
                string = False

            for col in range(len(text)):
                char = text[col]

                # Character is a whitespace
                if char.isspace():
                    # Ignore everything if it's a comment
                    if single and single_number < line:
                        single = False
                    elif single:
                        continue

                    if multiline:
                        word = ""
                        continue

                    # Append the character if it's a string
                    if string:
                        word += char
                        continue

                    # A word was found
                    if len(word) > 0:
                        self.__categorize__(word, line, col)
                        word = ""
                        symbol = False

                # Character is a know symbol
                elif char in self.__symbols__:
                    # Ignore everything if it's a comment
                    if single and single_number < line:
                        single = False
                    elif single:
                        continue

                    # Append the character if it's a string
                    if string:
                        word += char
                        continue

                    # If it's the first ocurrence of a symbol
                    if len(word) > 0 and not symbol:
                        # Check if it's the firts point of the number
                        if word.isdigit() and char == ".":
                            word += char
                            continue

                        # Check for exponential part of a number
                        if len(word) > 2 and char == "+" or char == "-":
                            if word[-1] == "E" or word[-1] == "e" and word[-2].isdigit():
                                word += char
                                continue

                        self.__categorize__(word, line, col)
                        word = ""

                    # If it's the second ocurrence of a symbol
                    if symbol:
                        # Recognize double operator
                        if word + char in self.__double_operator__:
                            if multiline:
                                continue

                            self.__categorize__(word + char, line, col + 1)
                            symbol = False
                            word = ""

                        # Single comment starts
                        elif word + char == "//":
                            if multiline:
                                continue

                            symbol = False
                            single = True
                            single_number = line
                            word = ""

                        # Multiline comment starts
                        elif word + char == "/*":
                            if multiline:
                                continue

                            symbol = False
                            multiline = True
                            word = ""

                        # Multiline comment ends
                        elif word + char == "*/":
                            if not multiline:
                                self.__add_error__(word, line, col, "Comment without match")

                            symbol = False
                            multiline = False
                            word = ""

                        # Two differentes symbols
                        else:
                            if not multiline:
                                self.__categorize__(word, line, col)

                            symbol = True
                            word = char

                    # First ocurrence of a symbol
                    else:
                        symbol = True
                        word += char

                # Character is anything else
                else:
                    # Ignore everything if it's a comment
                    if single and single_number < line:
                        single = False
                    elif single:
                        continue

                    if multiline:
                        word = ""
                        continue

                    # If it's double number
                    if symbol and word == "." and char.isdigit():
                        word += char
                        symbol = False
                        continue

                    # Check if there is a symbol in the lexeme
                    elif symbol:
                        self.__categorize__(word, line, col)
                        word = ""
                        symbol = False

                    # Check for start or end of a string
                    if char == '"':
                        # Word before string start
                        if len(word) > 0 and not string:
                            self.__categorize__(word, line, col)
                            word = ""

                        # String end
                        if string:
                            string = False
                            self.__categorize__(word + char, line, col + 1)
                            word = ""

                        # String start
                        else:
                            string = True
                            word = char

                        continue

                    word += char

        # EOF errors
        if string:
            self.__add_error__(None, len(lines), None, "EOF in string")

        if multiline:
            self.__add_error__(None, len(lines), None, "EOF in comment")

    # Match the word with their category
    def __categorize__(self, word, line, col):
        # Recognize reserverd words
        if word in self.__reserved_words__:
            self.__add_token__(word, line, col, word.lower().capitalize())

        # Recognize int base 10 number
        elif re.search(r"^[0-9]+$", word):
            self.__add_token__(word, line, col, "IntConstant_Decimal")

        # Recognize int base 16 number
        elif re.search(r"^0[x|X][0-9a-fA-F]+$", word):
            self.__add_token__(word, line, col, "IntConstant_Hexadecimal")

        # Recognize double number
        elif re.search(r"^[0-9]\.[0-9]*([e|E][+|-]?[0-9]+)?$", word):
            self.__add_token__(word, line, col, "DoubleConstant")

        # Recognize string
        elif re.search(r"^\".*\"$", word):
            self.__add_token__(word, line, col, "StringConstant")

        # Recognize boolean
        elif word == "true" or word == "boolean":
            self.__add_token__(word, line, col, "BooleanConstant")

        # Recognize double operator
        elif word in self.__double_operator__:
            self.__add_token__(word, line, col, "DoubleOperator")

        # Recognize single operator
        elif word in self.__single_operator__:
            self.__add_token__(word, line, col, "SingleOperator")

        # Recognize identifier
        elif re.search(r"^[a-zA-Z\$][0-9a-zA-Z\$]*$", word):
            # The identifier can't be greater than 31 chars length
            if len(word) > 31:
                self.__add_error__(word, line, col, "Identifier to long")
            else:
                self.__add_token__(word, line, col, "Identifier")

        # Recognize error
        else:
            self.__handle_error__(word, line, col)

    # Handle all the errors in the categorization
    def __handle_error__(self, word, line, col):
        if len(word) > 1:
            self.__add_error__(word, line, col, "Not a recognized character")
        elif re.search(r"^\.[0-9]+([e|E][+|-]?[0-9]+)?$", word):
            self.__add_error__(word, line, col, "Not a valid double number")
        else:
            self.__add_error__(word, line, col, "Not a valid identifier")

    # Add a new token to the list of analysis
    def __add_token__(self, word, line, col, category):
        if len(word) > 1:
            token = Token(word, line, col - len(word) + 1, col, category)
        else:
            token = Token(word, line, col, None, category)

        self.__analysis__.append(token)

    # Add a new error to the list of analysis
    def __add_error__(self, word, line, col, reason):
        if len(word) > 1:
            error = Token(word, line, col -len(word) + 1, col, "Error", reason)
        else:
            error = Token(word, line, col, None, "Error", reason)

        self.__analysis__.append(error)
