import sys
import miscsim
import miscasm
import time

def filename(extension):
    ignore = True
    for arg in sys.argv:
        if not ignore and len(arg) > 4:
            if arg[-4:].lower() == extension.lower():
                return arg
        ignore = False
    return ""

def makemif(filename,image,length):
    try:
        file = open(filename,'wt')
    except IOError:
        print("Failed to open output file {:s}".format(filename))
        sys.exit()

    # Write header to file
    file.write("DEPTH = {:d};\n".format(length))
    file.write("WIDTH = 16;\n")
    file.write("ADDRESS_RADIX = HEX;\n")
    file.write("DATA_RADIX = HEX;\n")
    file.write("CONTENT\nBEGIN\n")

    # Write data
    for address in range(0,length):
        file.write("{:03X} : {:04X} ;\n".format(address,image[address]))

    # End and close file
    file.write("END\n")
    file.close()
    print("MIF file {:s} created".format(filename))

def makebin(filename,image,length):
    try:
        file = open(filename,'wb')
    except IOError:
        print("Failed to open output file {:s}".format(filename))
        sys.exit()
    for address in range(0,length):
        file.write(bytes([image[address]>>8,image[address]&0xff]))
    file.close()
    print("BIN file {:s} created".format(filename))

def makelist(filename,asm):
    try:
        file = open(filename,'wt')
    except IOError:
        print("Failed to open output file {:s}".format(filename))
        sys.exit()
    text = "   MISC-16 assembler V1.0 listing file {:s} {:s}   ".format(filename,time.strftime('%d/%m/%Y %H:%M:%S', time.localtime()))
    dash = '-' * len(text)
    file.write(dash+'\n')
    file.write(text+'\n')
    file.write(dash+'\n')
    for (linenumber,start,end,linetext) in asm.listing:
        linetext = linetext.rstrip()
        linenumber = "{:d}".format(linenumber)
        data = ""
        memoryindex = start
        while True:
            address = "{:04X}  ".format(memoryindex)
            if memoryindex < end:
                data = "{:04X}".format(asm.image[memoryindex])
                memoryindex += 1
            if memoryindex < end:
                data += "{:04X}".format(asm.image[memoryindex])
                memoryindex += 1
            if data == "":
                address = ""
            data = data.ljust(10)
            address = address.ljust(6)
            file.write(linenumber.ljust(6)+address+data+linetext+'\n')
            linenumber = ""
            linetext = ""
            if memoryindex >= end:
                break
    text = "   Symbol Table"
    dash = "-------------------"
    file.write(dash+'\n')
    file.write(text+'\n')
    file.write(dash+'\n')
    for label in asm.labels:
        file.write(label.ljust(15)+"{:04X}\n".format(asm.labels[label]))
    text = "   End of File"
    dash = "-------------------"
    file.write(dash+'\n')
    file.write(text+'\n')
    file.write(dash+'\n')
    file.close()
    print("LST file {:s} created".format(filename))

if __name__ == "__main__":

    # Extract filenames from command line arguments    
    sourcefile = filename(".asm")
    binfile = filename(".bin")
    miffile = filename(".mif")
    lstfile = filename(".lst")

    # Display usage if no source file specified
    if not sourcefile:
        print("Usage: python misc.py <input.asm> [out.mif][out.bin][out.lst]")
        sys.exit()

    # Open source file
    try:
        file = open(sourcefile,"rt")
    except IOError:
        print("Could not open file {:s}".format(sourcefile))
        sys.exit()

    # Assemble file
    asm = miscasm.miscasm(file)
    file.close()

    # Bail out if we have errors
    if asm.errorcount != 0:
        print("Assembly failed with {:d} errors".format(asm.errorcount))
        sys.exit()

    # Success
    print("Success: assembly completed {:d} bytes".format(asm.memoryindex<<1))

    # Generate FPGA file
    if miffile:
        makemif(miffile,asm.image,asm.memoryindex)

    # Generate BIN file
    if binfile:
        makebin(binfile,asm.image,asm.memoryindex)

    # Generate listing file
    if lstfile:
        makelist(lstfile,asm)

    # Run simulator if no output files specified
    if not (miffile or binfile or lstfile):
        miscsim.miscsim(asm.image)

# end of file
