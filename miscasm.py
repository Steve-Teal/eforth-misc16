#
# MISC-16 Assembler
#

class miscasm(object):

    def __init__(self, file):
        self.keywords = {'org':self.org,'dw':self.dw,'db':self.db,'equ':self.equ,'mov':self.mov}
        self.linenumber = 0
        self.labels = {}
        self.references = {}
        self.memoryindex = 0
        self.memorysize = 4096
        self.image = [0] * self.memorysize
        self.errorcount = 0
        self.memoryfull = False
        self.listing = []
        for fileline in file:
            self.linenumber += 1
            line = fileline
            address = self.memoryindex
            line = self.expandstrings(line)
            line = self.stripcomments(line)
            tokens = self.lexer(line)
            if len(tokens) > 0:
                tokens = self.parser1(tokens)
            if len(tokens) > 0:
                self.parser2(tokens)
            if self.memoryfull:
                self.error("Program exceeds memory size")
                break
            self.listing.append((self.linenumber,address,self.memoryindex,fileline))
        if self.errorcount == 0:
            self.resolvereferences()

    def expandstrings(self,line):
        expand = False
        returnline = ""
        for char in line:
            if char == "'":
                expand = not expand
                continue
            if expand:
                returnline += " {:d} ".format(ord(char))
            elif char == ',':
                returnline += ' '
            else:
                returnline += "{:s}".format(char)
        return returnline

    def stripcomments(self,line):
        line = line.rstrip()
        if ";" in line:
            line = line[:line.find(";")]
        return line

    def lexer(self,line):
        tokens = []
        for token in line.split(' '):
            # For each token (zero length tokens are ignored)
            if len(token) > 0:
                # Check if token is a keyword
                if token in self.keywords:
                    tokens.append({'KEYWORD':token})
                else:
                    # Check if token is a integer (hex or decimal only)
                    try:
                        integer = int(token,0)
                        tokens.append({'INTEGER':integer})
                    except(ValueError):
                        # Default to token being a string (reference)
                        tokens.append({'STRING':token})
        return tokens

    def parser1(self,tokens):
        if 'STRING' in tokens[0]:
            label = tokens[0]['STRING']
            if label in self.labels:
                self.error("Redefined label '{:s}'".format(label))
                return []
            if len(tokens) > 1:
                if 'KEYWORD' in tokens[1]:
                    if tokens[1]['KEYWORD'] == "equ":
                        if len(tokens) == 3:
                            if 'INTEGER' in tokens[2]:
                                self.labels[label] = tokens[2]['INTEGER']
                                return []
                        self.error("Expected single integer on right side of equ")
                        return []
            self.labels[label] = self.memoryindex
            tokens.pop(0)
        return tokens

    def parser2(self,tokens):
        if not 'KEYWORD' in tokens[0]:
            for tokentype in tokens[0]: # Should only interrate once
                self.error("Expected keyword instead of '{}'".format(tokens[0][tokentype]))
            return
        self.keywords[tokens[0]['KEYWORD']](tokens[1:])

    def org(self,tokens):
        if len(tokens) == 1:
            if 'INTEGER' in tokens[0]:
                self.memoryindex = tokens[0]['INTEGER']
                if self.memoryindex >= self.memorysize:
                    self.memoryfull = True
                    self.memoryindex = 0
                return
        self.error('Expected single integer on right side of org')

    def dw(self,tokens):
        # Tokens should be integers or references
        for token in tokens:
            if 'INTEGER' in token:
                self.appendinteger(token['INTEGER'])
            elif 'STRING' in token:
                self.reference(token['STRING'])
            else:
                self.error("Expected integer or reference")

    def db(self,tokens):
        # Tokens should all be integers <= 255
        highbyte = True
        for token in tokens:
            if not 'INTEGER' in token:
                self.errorcount += 1
                self.error("Expected integer")
                continue
            value = token['INTEGER']
            if value > 255 or value < -128:
                self.error("{:d} exceeds 8-bit integer range".format(value))
                continue
            if value < 0:
                value = 0x100 + value
            if highbyte:
                self.image[self.memoryindex] = value << 8
            else:
                self.image[self.memoryindex] |= value
                self.incmemindex()
            highbyte = not highbyte
        if not highbyte:
            self.incmemindex()

    def equ(self,tokens):
        # This should not get called since equ is dealt with earlier
        self.error("Unexpected 'equ'");

    def mov(self,tokens):
        # only 2 tokens (source, destination) 
        if len(tokens) == 2:
            # Swap tokens then treat like dw
            tokens.append(tokens[0])
            tokens.pop(0)
            self.dw(tokens)
        else:
            self.error("Expected 2 operands for mov instruction")

    def appendinteger(self,value):
        if value > 65535 or value < -32768:
            self.error("{:d} exceeds 16-bit integer range".format(value))
            return
        if value < 0:
            value = 0x10000 + value
        self.image[self.memoryindex] = value
        self.incmemindex()

    def incmemindex(self):
        self.memoryindex += 1
        if self.memoryindex >= self.memorysize:
            self.memoryfull = True
            self.memoryindex = 0

    def error(self,message):
        print("ERROR: {:s} in line {:d}".format(message,self.linenumber))
        self.errorcount += 1

    def reference(self,label):
        if not label in self.references:
            self.references[label] = []
        self.references[label].append((self.memoryindex,self.linenumber))
        self.incmemindex()

    def resolvereferences(self):
        for reference in self.references:
            for (address,line) in self.references[reference]:
                if reference in self.labels:
                    self.image[address] = self.labels[reference]
                else:
                    self.linenumber = line
                    self.error("Undefined reference to {:s}".format(reference))

