from rflint.common import TestRule, KeywordRule, GeneralRule, ERROR, WARNING

import re

class LineTooLong(GeneralRule):
    '''Check that a line is not too long (configurable; default=100)'''

    severity = WARNING
    maxchars = 100

    def configure(self, maxchars):
        self.maxchars = int(maxchars)

    def apply(self, robot_file):
        for linenumber, line in enumerate(robot_file.raw_text.split("\n")):
            if len(line) > self.maxchars:
                message = "Line is too long (exceeds %s characters)" % self.maxchars
                self.report(robot_file, message, linenumber+1, self.maxchars)

class TrailingBlankLines(GeneralRule):
    '''Check for multiple blank lines at the end of a file

    This is a configurable. The default value is 2. 
    '''

    severity = WARNING
    max_allowed = 2

    def configure(self, max_allowed):
        self.max_allowed=int(max_allowed)

    def apply(self, robot_file):
        # I realize I'm making two full passes over the data, but
        # python is plenty fast enough. Even processing a file with
        # over six thousand lines, this takes a couple of
        # milliseconds.  Plenty fast enough for the intended use case,
        # since most files should be about two orders of magnitude
        # smaller than that.

        match=re.search(r'(\s*)$', robot_file.raw_text)
        if match:
            count = len(re.findall(r'\n', match.group(0)))
            if count > self.max_allowed:
                numlines = len(robot_file.raw_text.split("\n"))
                message = "Too many trailing blank lines"
                linenumber = numlines-count
                self.report(robot_file, message, linenumber+self.max_allowed, 0)


class FileTooLong(GeneralRule):
    '''Verify the file has fewer lines than a given threshold.

    You can configure the maximum number of lines. The default is 300.
    '''

    severity = WARNING
    max_allowed = 300

    def configure(self, max_allowed):
        self.max_allowed = int(max_allowed)

    def apply(self, robot_file):
        lines = robot_file.raw_text.split("\n")
        if len(lines) > self.max_allowed:
            message = "File has too many lines (%s)" % len(lines)
            linenumber = self.max_allowed+1
            self.report(robot_file, message, linenumber, 0)

class GlobalVariableIsNotAllUpperCase(GeneralRule):
    '''Verify that all global variables are in capital letters.

        A variable is considered global when it is accessible on a
        global-, suite- or test level.

        See: https://github.com/robotframework/HowToWriteGoodTestCases/blob/master/HowToWriteGoodTestCases.rst#variable-naming
    '''

    severity = WARNING

    def apply(self, robot_file):
        # Iterate through 'Variable' section
        for row in robot_file.variables:
            variable = row[0]
            if (variable.isupper() is not True and 
                variable.strip().startswith('...') is not True):
                message = "Violation of lower case character(s) in global variable %s" % variable
                self.report(robot_file, message, row.linenumber) 

        # Iterate through 'Test Cases' section
        for testcase in robot_file.testcases:
            self.report_bad_variable_naming(testcase.rows, robot_file)

        # Iterate through 'Keyword' section
        for keyword in robot_file.keywords:
            self.report_bad_variable_naming(keyword.rows, robot_file)

    def report_bad_variable_naming(self, rows, robot_file):
        '''Iterates through all cells and verifies
        that global variables has all capital letters.
        '''
        global_variable_found = False

        extract_cell_gen = ((cell, row.linenumber) for row in rows for cell in row.cells)
        for cell, linenumber in extract_cell_gen:
            if cell == "..." or cell == "":
                # Jump to next cell
                continue

            if  ((cell.lower() == "set global variable") or
                (cell.lower() == "set suite variable") or
                (cell.lower() == "set test variable")):
                global_variable_found = True
                # Next iteration will grab the variable name
                continue

            if global_variable_found:
                if cell.isupper() is not True:
                    message = "Violation of lower case character(s) in global variable %s" % cell
                    self.report(robot_file, message, linenumber) 
                global_variable_found = False