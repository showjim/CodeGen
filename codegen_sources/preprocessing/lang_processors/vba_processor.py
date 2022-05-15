# Copyright (c) 2019-present, Facebook, Inc.
# All rights reserved.
#
# This source code is licensed under the license found in the
# LICENSE file in the root directory of this source tree.
#
from codegen_sources.preprocessing.lang_processors.tokenization_utils import (
    process_string,
)
from codegen_sources.preprocessing.lang_processors.lang_processor import LangProcessor
from codegen_sources.preprocessing.obfuscation.bobskater_obfuscator import (
    obfuscateString,
)
from codegen_sources.preprocessing.obfuscation.utils_deobfuscation import dico_to_string

import tokenize
from io import BytesIO
import re
import antlr4
from codegen_sources.antlr4_vba_parser.vbaLexer import vbaLexer
from codegen_sources.antlr4_vba_parser.vbaParser import vbaParser
from pathlib import Path

COMMENT_TYPES = {"comment", "line_comment", "block_comment"}

class VbaProcessor(LangProcessor):
    def __init__(self, root_folder=None):

        self.spetoken2char = {
            "STOKEN00": "#",
            "STOKEN1": "\\n",
            "STOKEN2": '"""',
            "STOKEN3": "'''",
        }
        self.char2spetoken = {
            value: " " + key + " " for key, value in self.spetoken2char.items()
        }
        self.language = "vba"
        self.ast_nodes_type_string = ["comment", "string_literal", "char_literal"]

    def get_vba_tokens_and_types(self, file_or_string:str):
        if Path(file_or_string).exists():
            input_stream = antlr4.FileStream(file_or_string)
        else:
            input_stream = antlr4.InputStream(file_or_string)

        # lexing
        lexer = vbaLexer(input_stream)
        stream = antlr4.CommonTokenStream(lexer)

        # # parsing
        # parser = vbaParser(stream)
        # tree = parser.startRule()

        # Parse all tokens until EOF
        stream.fill()

        # get token type int-->string dict
        token_names = {-1:'<EOF>'} # EOF is not in LEXER
        for name, value in vbaLexer.__dict__.items():
            if isinstance(value, int) and name == name.upper():
                token_names[value] = name

        tokenList = []
        tokenTypeList = []
        for token in stream.tokens:
            tokenList.append(token.text)
            tokenTypeList.append(token_names[token.type])

        return tokenList, tokenTypeList

    def tokenize_code(self, code, keep_comments=False, process_strings=True):
        assert isinstance(code, str)
        code = code.replace(r"\r", "")
        code = code.replace("\r", "")

        tokenized_code = []
        tokens, token_types = self.get_vba_tokens_and_types(code)
        for token, token_type in zip(tokens, token_types):
            if token_type in COMMENT_TYPES and keep_comments is False:
                continue
            if token_type in self.ast_nodes_type_string:
                token = process_string(
                    token,
                    self.char2spetoken,
                    self.spetoken2char,
                    token_type in COMMENT_TYPES,
                    process_strings,
                )
            if len(token) > 0:
                if token_type not in self.ast_nodes_type_string:
                    token = token.replace("\n", "NEW_LINE")
                    token = token.replace("NEW_LINENEW_LINE", "NEW_LINE")
                tokenized_code.append(token)
        return tokenized_code[:-1]

    def detokenize_code(self, code):
        # replace recreate lines with \n and appropriate indent / dedent
        # removing indent/ dedent tokens
        assert isinstance(code, str) or isinstance(code, list)
        if isinstance(code, list):
            code = " ".join(code)
        code = code.replace("ENDCOM", "NEW_LINE")
        code = code.replace("▁", "SPACETOKEN")
        lines = code.split("NEW_LINE")
        tabs = ""
        for i, line in enumerate(lines):
            line = line.strip()
            if line.startswith("INDENT "):
                tabs += "    "
                line = line.replace("INDENT ", tabs)
            elif line.startswith("DEDENT"):
                number_dedent = line.count("DEDENT")
                tabs = tabs[4 * number_dedent :]
                line = line.replace("DEDENT", "")
                line = line.strip()
                line = tabs + line
            elif line == "DEDENT":
                line = ""
            else:
                line = tabs + line
            lines[i] = line
        untok_s = "\n".join(lines)
        # find string and comment with parser and detokenize string correctly
        try:
            for toktype, tok, _, _, line in tokenize.tokenize(
                BytesIO(untok_s.encode("utf-8")).readline
            ):
                if toktype == tokenize.STRING or toktype == tokenize.COMMENT:
                    tok_ = (
                        tok.replace("STRNEWLINE", "\n")
                        .replace("TABSYMBOL", "\t")
                        .replace(" ", "")
                        .replace("SPACETOKEN", " ")
                    )
                    untok_s = untok_s.replace(tok, tok_)
        except KeyboardInterrupt:
            raise
        except:
            # TODO raise ValueError(f'Invalid python function \n {code}\n')
            pass
        # detokenize imports
        untok_s = (
            untok_s.replace(". ", ".")
            .replace(" .", ".")
            .replace("import.", "import .")
            .replace("from.", "from .")
        )
        # special strings
        string_modifiers = ["r", "u", "f", "rf", "fr", "b", "rb", "br"]
        for modifier in string_modifiers + [s.upper() for s in string_modifiers]:
            untok_s = untok_s.replace(f" {modifier} '", f" {modifier}'").replace(
                f' {modifier} "', f' {modifier}"'
            )
        untok_s = untok_s.replace("> >", ">>").replace("< <", "<<")
        return untok_s

    def obfuscate_code(self, code):
        res, dico = obfuscateString(code, obfuscateNames=True, removeDocstrings=False)
        return res, dico_to_string(dico)

    def extract_functions(self, tokenized_code: str):
        """Extract functions from tokenized python code"""
        if isinstance(tokenized_code, str):
            tokenized_code = tokenized_code.split()
        else:
            assert isinstance(tokenized_code, list)
            tokenized_code = tokenized_code

        def filter_functions_python_2_3(function):
            if (
                re.search("print [^(]", function) is None
                and re.search("raise \w+ ,", function) is None
                and re.search("except \w+ ,", function) is None
                and re.search("[^ ]+ = \d+ L", function) is None
                and ". iterkeys ( )" not in function
                and ". itervalues ( )" not in function
                and ". iteritems ( )" not in function
                and "xrange (" not in function
                and "imap (" not in function
            ):
                return function
            else:
                return None

        tokens = iter(tokenized_code)
        functions_standalone = []
        functions_class = []
        number_indent = 0
        try:
            token = next(tokens)
        except StopIteration:
            return [], []
        while True:
            try:
                if token == "def":
                    function = ["def"]
                    while not (token == "DEDENT" and number_indent == 0):
                        token = next(tokens)
                        if token == "INDENT":
                            number_indent += 1
                        elif token == "DEDENT":
                            number_indent -= 1
                        function.append(token)
                    try:
                        if function[function.index("(") + 1] == "self":
                            function = filter_functions_python_2_3(" ".join(function))
                            if function is not None:
                                functions_class.append(function)
                        else:
                            function = filter_functions_python_2_3(" ".join(function))
                            if function is not None:
                                functions_standalone.append(function)
                    except:
                        print(function)
                        token = next(tokens)
                else:
                    token = next(tokens)
            except StopIteration:
                break
        return functions_standalone, functions_class

    def get_function_name(self, function):
        assert isinstance(function, str) or isinstance(function, list)
        if isinstance(function, str):
            function = function.split()
        return function[function.index("def") + 1]
