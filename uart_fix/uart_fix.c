/*******************************************************************************
* Author : liyunteng
* Email : li_yunteng@163.com
* Created Time : 2013-12-10 13:35
* Filename : uart_fix.c
* Description : 
* *****************************************************************************/
#include <stdio.h>
#include <sys/io.h>
#include <unistd.h>
#include <stdlib.h>
#include <string.h>

#define EFER_REG	0x2E
#define EFIR_REG	EFER_REG
#define EFDR_REG	(EFER_REG+1)

int main ( int argc, char *argv[] )
{
	unsigned short uarta_base_addr;
	unsigned char temp;

	ioperm ( 0x14, 1, 1 );
	ioperm ( 0x2e, 2, 1 );

	outb ( 0x87, EFER_REG );
	outb ( 0x87, EFER_REG );

	outb ( 0x14,  EFIR_REG );
	temp = inb ( EFDR_REG );
	temp &= ~(( 1 << 3 ) | ( 1 << 4 ) | ( 1 << 7 ));

	outb ( 0x14, EFIR_REG );
	outb ( temp, EFDR_REG );

	ioperm ( 0x2e, 2, 0 );
	ioperm ( 0x14, 1, 0 );
	
	printf ( "Uart fix success.\n" );

	return 0;

}
