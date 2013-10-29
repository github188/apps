#ifndef __JW_WATCHDOG_H__
#define __JW_WATCHDOG_H__

/*
 * Enable the watchdog with default 255s as timeout value
 * The timeout can be modified by watchdog_set_timeout() function,
 * and this value will be keep unchanged until watchdog_set_timeout() function was called again.
 * 
 * Example:
 * watchdog_set_timeout ( 100 );		//-- set timeout as 100s
 * watchdog_enable ();
 *
 * Returns 0 on suceess; otherwise returns an negtive value.
*/
int watchdog_enable ( void );

/*
 * Disable the watchdog
 * Returns 0 on suceess; otherwise returns an negtive value.
*/
int watchdog_disable ( void );

/*
 * Set the time out value for the watchdog
 * timeout specify the timeout value, in seconds, max value is 255
 * Returns 0 on suceess; otherwise returns an negtive value.
*/
int watchdog_set_timeout ( unsigned char timeout );

/*
 * Feed the watchdog to avoid the watchdog timeout
 * Returns 0 on suceess; otherwise returns an negtive value.
*/
int watchdog_feed ( void );

#endif

