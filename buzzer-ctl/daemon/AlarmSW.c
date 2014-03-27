#include <sys/io.h>  
#include <unistd.h>  
#include <string.h>
#include <stdio.h>
#include <stdlib.h>

void play(unsigned int* freq ,unsigned int* delay);  

void Stop( )  
{ 
	static  int  flag=0;  
	if(flag==0)  
	{  
		flag=1;  
		iopl(3);  
	}  
	outb(0xfc ,0x61);  
	return;
}  



void play(unsigned int* freq ,unsigned int* time)  
{  
	int i;  
	for(i=0;freq[i]!=0;i++)  
	{  
		speaker(freq[i] ,time[i]);  
	}  
}  

int speaker(unsigned int freq,unsigned int delay)  
{ 
	static int flag=0,bit;  
	if(flag==0)  
	{  
		flag=1;  
		iopl(3);  
	}  
	outb(0xb6,0x43);  
	outb((freq & 0xff),0x42);  
	outb((freq >> 8),0x42);  
	bit=inb(0x61);  
	outb(3 | bit,0x61);  
	usleep(10000*delay);  
	outb(0xfc | bit,0x61);  
}
