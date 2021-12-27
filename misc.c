/*

    MISC16 Simulator
    
*/
#include<conio.h>
#include<stdlib.h>
#include<stdio.h>
#include<stdint.h>
#include<string.h>

#define RAM_SIZE    (32768)
#define ESC         (27)

uint16_t ram[RAM_SIZE];
uint16_t accu;
uint16_t sf;
uint16_t zf;
uint16_t cf;
uint16_t pc;
uint16_t key;

int loadfile(char *fileName)
{
    FILE *fp;
    int index;

    fp = fopen(fileName,"rb");

    if(fp)
    {
        fread(ram,sizeof(uint16_t),RAM_SIZE,fp);
        fclose(fp);
        for(index=0;index<RAM_SIZE;index++)
        {
            ram[index] = ram[index] >> 8 | ram[index] << 8;
        }
    }

    return (fp != NULL);
}

uint16_t getkey(void)
{
    key = getch()&0xff;
    return key;
}

void writeAccu(uint16_t value)
{
    accu = value;
    sf = value&0x8000?1:0;
    zf = value?0:1;
}

uint16_t read(uint16_t address)
{
    switch(address)
    {
        case 0: return pc;
        case 1: return pc + 2;
        case 2: return pc + 4;
        case 3: return pc + 6;
        case 7: return read(accu);
        case 8: return accu;
        case 0xfffd: return 0; 
        case 0xfffe: return getkey();
        case 0xffff: return kbhit()?0:1;
        default: break;
    }

    return address<RAM_SIZE?ram[address]:0;
}

uint16_t sub(uint16_t a, uint16_t b)
{
    uint16_t s;

    b = ~b;
    s = a + b + 1;
    cf = (((a&b)|((a|b)&~s))&0x8000)?0:1;
    return s;
}

uint16_t add(uint16_t a, uint16_t b)
{
    uint16_t s;

    s = a + b;
    cf = (((a&b)|((a|b)&~s))&0x8000)?1:0;
    return s;
}

uint16_t shiftright(uint16_t a)
{
    uint16_t s;

    s = a >> 1 | cf << 15;
    cf = a & 1;
    return s;
}

void write(uint16_t address, uint16_t data)
{
    switch(address)
    {
        case 0: pc = data; return;
        case 1: pc = sf?data:pc; return;
        case 2: pc = zf?data:pc; return;
        case 4: pc = cf?data:pc; return;
        case 7: write(accu,data); return;
        case 8: writeAccu(data); return;
        case 9: writeAccu(sub(accu,data)); return;
        case 11: writeAccu(add(data,accu)); return;
        case 12: writeAccu(data ^ accu); return;
        case 13: writeAccu(data | accu); return;
        case 14: writeAccu(data & accu); return;
        case 15: writeAccu(shiftright(data)); return;
        case 0xfffc: if(data!=13)putch(data&0xff); return;
        default: break;
    }

    if(address<RAM_SIZE)
    {
        ram[address] = data;
    }
}

int main(int argc, char **argv)
{
    uint16_t src;
    uint16_t dst;
    uint16_t temp;

    if(argc != 2)
    {
        printf("Usage: misc <binfile.bin>\n");
        return 0;
    }

    if(!loadfile(argv[1]))
    {
        printf("File: %s not found\n",argv[1]);
        return 0;
    }

    key = 0;
    pc = 0x10; /* Program counter reset value */
    while(key != ESC)
    {        
        src = ram[pc];
        dst = ram[pc+1];
        temp = read(src);
        pc+=2;
        write(dst,temp);        
    }

    return 0;
}

/* End of file */

