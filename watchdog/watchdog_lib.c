#include <sys/types.h>
#include <sys/stat.h>
#include <sys/mman.h>
#include <sys/ioctl.h>
#include <unistd.h>
#include <fcntl.h> 
#include <stdlib.h>
#include <stdio.h>
#include <string.h>
#include "watchdog_lib.h"

//#include "sio_watchdog.h"

#define SIO_WDT_ENABLE				0x56
#define SIO_WDT_DISABLE			0x57
#define SIO_WDT_SET_TIME			0x58
#define SIO_WDT_FEED				0x59

#define SIO_WDT_2_ENABLE			0x5A
#define SIO_WDT_2_DISABLE			0x5B

#define SIO_WDT_DEV_NAME			"/dev/sio_wdt"


int watchdog_enable ( void )
{
	int ret;
	int fd;
	
	fd = open ( SIO_WDT_DEV_NAME, O_RDWR );
	if ( fd < 0 )
	{
		printf ( "open file error.\n" );
		return  -1;
	}

	ret = ioctl ( fd, SIO_WDT_ENABLE, 0 );

	close ( fd );
	
	return ret;
}

int watchdog_disable ( void )
{
	int ret;
	int fd;
	
	fd = open ( SIO_WDT_DEV_NAME, O_RDWR );
	if ( fd < 0 )
	{
		printf ( "open file error.\n" );
		return  -1;
	}

	ret = ioctl ( fd, SIO_WDT_DISABLE, 0 );

	close ( fd );
	
	return ret;
}

int watchdog_set_timeout ( unsigned char timeout )
{
	int ret;
	int fd;
	
	fd = open ( SIO_WDT_DEV_NAME, O_RDWR );
	if ( fd < 0 )
	{
		printf ( "open file error.\n" );
		return  -1;
	}

	ret = ioctl ( fd, SIO_WDT_SET_TIME, timeout );

	close ( fd );
	
	return ret;
}

int watchdog_feed ( void )
{
	int ret;
	int fd;
	
	fd = open ( SIO_WDT_DEV_NAME, O_RDWR );
	if ( fd < 0 )
	{
		printf ( "open file error.\n" );
		return  -1;
	}

	ret = ioctl ( fd, SIO_WDT_FEED, 0 );

	close ( fd );
	
	return ret;
}


#if 0

int main ( int argc, char *argv[] )
{
	int fd;
	int wdt_time;

	if ( argc < 2 )
	{
		printf ( "Please use the one of the paramenters list below.\n" );
		printf ( "WDT_ENABLE\n" );
		printf ( "WDT_DISABLE\n" );
		printf ( "WDT_FEED\n" );
		printf ( "WDT_SET_TIME xx\n" );
		return 0;
	}

	fd = open ( SIO_WDT_DEV_NAME, O_RDWR );
	if ( fd < 0 )
	{
		printf ( "open file error.\n" );
		return -1;
	}

	if ( strcmp ( argv[1], "WDT_ENABLE" ) == 0 )
	{
		printf ( "You want to enable the wdt.\n" );
		ioctl ( fd, SIO_WDT_ENABLE, 0 );
	}
	else if ( strcmp ( argv[1], "WDT_DISABLE" ) == 0 )
	{
		printf ( "You want to disbale the WDT.\n" );
		ioctl ( fd, SIO_WDT_DISABLE, 0 );
	}
	else if ( strcmp ( argv[1], "WDT_FEED" ) == 0 )
	{
		printf ( "You are feeding the watch dog, Thanks.\n" );
		ioctl ( fd, SIO_WDT_FEED, 0);
	}
	else if ( strcmp ( argv[1], "WDT_SET_TIME" ) == 0 )
	{
		printf ( "You are set the time count for wdt.\n" );
		wdt_time = atoi( argv[2] );
		if (( wdt_time > 0 ) && ( wdt_time < 255 ))
		{
			ioctl ( fd, SIO_WDT_SET_TIME, wdt_time );
		}
	}
	else
	{
		printf ( "Wrong parameter.\n" );
	}
	return 0;
	
	close ( fd );
	return 0;
}
#endif
