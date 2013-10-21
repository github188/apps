#include <sys/types.h>
#include <sys/stat.h>
#include <sys/mman.h>
#include <unistd.h>
#include <fcntl.h> 
#include <stdlib.h>
#include <stdio.h>
#include <string.h>

#define USE_LIB	0

#if ( USE_LIB == 1 )
#include "sio_watchdog_lib.h"
#endif

#define SIO_WDT_ENABLE				0x56
#define SIO_WDT_DISABLE			0x57
#define SIO_WDT_SET_TIME			0x58
#define SIO_WDT_FEED				0x59

#define SIO_WDT_2_ENABLE			0x5A
#define SIO_WDT_2_DISABLE			0x5B

#if ( USE_LIB == 0 )
#define SIO_WDT_DEV_NAME			"/dev/sio_wdt"
#endif

int main ( int argc, char *argv[] )
{
#if ( USE_LIB == 0 )
	int fd;
#endif
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
#if ( USE_LIB == 0 )
	fd = open ( SIO_WDT_DEV_NAME, O_RDWR );
	if ( fd < 0 )
	{
		printf ( "open file error.\n" );
		return -1;
	}
#endif

	if ( strcmp ( argv[1], "WDT_ENABLE" ) == 0 )
	{
		printf ( "You want to enable the wdt.\n" );
#if ( USE_LIB == 0 )
		ioctl ( fd, SIO_WDT_ENABLE, 0 );
#else
		sio_watchdog_enable ();		
#endif
	}
	else if ( strcmp ( argv[1], "WDT_DISABLE" ) == 0 )
	{
		printf ( "You want to disbale the WDT.\n" );
#if ( USE_LIB == 0 )
		ioctl ( fd, SIO_WDT_DISABLE, 0 );
#else
		sio_watchdog_disable ();
#endif
	}
	else if ( strcmp ( argv[1], "WDT_FEED" ) == 0 )
	{
		printf ( "You are feeding the watch dog, Thanks.\n" );
#if ( USE_LIB == 0 )		
		ioctl ( fd, SIO_WDT_FEED, 0);
#else
		sio_watchdog_feed ();
#endif
	}
	else if ( strcmp ( argv[1], "WDT_SET_TIME" ) == 0 )
	{
		printf ( "You are set the time count for wdt.\n" );
		wdt_time = atoi( argv[2] );
		if (( wdt_time > 0 ) && ( wdt_time < 255 ))
		{
#if ( USE_LIB == 0 )		
			ioctl ( fd, SIO_WDT_SET_TIME, wdt_time );
#else
			sio_watchdog_set_time (( unsigned char ) wdt_time );
#endif
		}
	}
	else
	{
		printf ( "Wrong parameter.\n" );
	}
	return 0;

#if ( USE_LIB == 0 )	
	close ( fd );
#endif	
	return 0;
}



