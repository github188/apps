#ifndef PIC_CTL_H
#define PIC_CTL_H

#ifdef __cplusplus
extern "C" {
#endif
	
#include <stdint.h>
#include "pic_reg.h"

#define HZ	(16)

enum {
	PERR_SUCCESS	= 0,	/* ok */
	PERR_NODEV	= -1,	/* Can't open i2c-0 */
	PERR_IOERR	= -2,	/* I2C access failed */
	PERR_INVAL	= -3,	/* Invalidate parameter */
};

enum {
	PIC_LED_NUMBER	= 16,

	PIC_LED_OFF	= 0x00,
	PIC_LED_ON	= 0x01,
	PIC_LED_BLINK	= 0x02,
	PIC_LED_B2	= 0x03,

	PIC_LED_FREQ_NORMAL = PIC_HZ / 2,
	PIC_LED_FREQ_SLOW = PIC_HZ,
	PIC_LED_FREQ_FAST = PIC_HZ / 8,


	PIC_LED_STS_MASK	= 0x03,
	PIC_LED_FREQ_SHIFT	= 2,
	PIC_LED_FREQ_MASK	= 0xfc,
};

enum {
	PIC_WDT_START	= 0x55,
	PIC_WDT_STOP	= 0xaa,
};

int pic_init(void);
void pic_release(void);
int pic_get_version(uint32_t *version);
int pic_get_scm_id ( uint32_t *scm_id );
int pic_get_build_date ( uint32_t *build_date );
int pic_set_led(uint8_t led, uint8_t sts, uint8_t freq);
int pic_start_watchdog(void);
int pic_stop_watchdog(void);
int pic_reset_timer(int sec);
int pic_reset_hd(int idx);
#ifdef __cplusplus
}
#endif

#endif
