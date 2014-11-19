#include <sys/types.h>
#include <sys/stat.h>
#include <fcntl.h>
#include <unistd.h>
#include <stdint.h>
#include <stdio.h>

#include "i2c-dev.h"
#include "pic_ctl.h"

#define I2C_DEV "/dev/i2c-i801"

static int pic_is_initialized;
static int pic_fd;

static int __pic_read_reg(uint8_t reg, uint8_t *v)
{
	int ret;

	ret = i2c_smbus_read_byte_data(pic_fd, reg);
	if (ret == -1)
		return PERR_IOERR;
	*v = ret;
	return 0;
}

static int __pic_write_reg(uint8_t reg, uint8_t v)
{
	int ret;

	ret = i2c_smbus_write_byte_data(pic_fd, reg, v);
	if (ret < 0)
		return PERR_IOERR;
	return 0;
}

int pic_init(void)
{
	int fd;

	if (pic_is_initialized)
		return 0;
	fd = open(I2C_DEV, O_RDWR);
	if (fd < 0)
		return PERR_NODEV;
	if (ioctl(fd, I2C_SLAVE_FORCE, PIC_ADDRESS) < 0) {
		close(fd);
		return PERR_NODEV;
	}

	pic_is_initialized = 1;
	pic_fd = fd;

	return 0;
}

void pic_release(void)
{
	if (pic_is_initialized) {
		close(pic_fd);
		pic_is_initialized = 0;
	}
}

#define PIC_CHECK_INIT()	do {		\
	int ret = pic_init();			\
	if (ret < 0)				\
		return ret;			\
} while (0)

int pic_get_version(uint32_t *version)
{
	uint8_t vl, vh;
	int ret;

	PIC_CHECK_INIT();
	ret = __pic_read_reg(PIC_VERH, &vh);
	if (ret < 0)
		return ret;
	ret = __pic_read_reg(PIC_VERL, &vl);
	if (ret < 0)
		return ret;

	*version = (vh << 8) | vl;

	return 0;
}

int pic_get_scm_id ( uint32_t *scm_id )
{
	uint8_t id_low, id_mid, id_high;
	int ret;

	PIC_CHECK_INIT ();

	ret = __pic_read_reg ( PIC_FM_GIT_VER_LOW, &id_low );
	if ( ret < 0 ) {
		return ret;
	}

	ret = __pic_read_reg ( PIC_FM_GIT_VER_MID, &id_mid );
	if ( ret < 0 ) {
		return ret;
	}

	ret = __pic_read_reg ( PIC_FM_GIT_VER_HIGH, &id_high );
	if ( ret < 0 ) {
		return ret;
	}

	*scm_id = ( id_high << 16 ) | ( id_mid << 8 ) | id_low;

	return 0; 
}

int pic_get_build_date ( uint32_t *build_date )
{
	uint8_t year, month, day;
	int ret;

	PIC_CHECK_INIT();
	ret = __pic_read_reg ( PIC_FM_BUILD_YEAR, &year );
	if ( ret < 0 ) {
		return ret;
	}

	ret = __pic_read_reg ( PIC_FM_BUILD_MONTH, &month );
	if ( ret < 0 ) {
		return ret;
	}

	ret = __pic_read_reg ( PIC_FM_BUILD_DAY, &day );
	if ( ret < 0 ) {
		return ret;
	}

	if ( year != 0 ) {
		*build_date = ( 20 << 24) | ( year << 16 ) | ( month << 8 ) | day;
	} else {
		*build_date = 0;
	}

	return 0;
}

int pic_set_led(uint8_t led, uint8_t sts, uint8_t freq)
{
	uint8_t v;
	uint8_t reg;

	PIC_CHECK_INIT();
	if (led >= PIC_LED_NUMBER)
		return PERR_INVAL;
	reg = PIC_LED_START + led;
	v = (freq << PIC_LED_FREQ_SHIFT) | (sts & PIC_LED_STS_MASK);

	return __pic_write_reg(reg, v);
}

int pic_start_watchdog(void)
{
	PIC_CHECK_INIT();
	return __pic_write_reg(PIC_WDT, PIC_WDT_START);
}

int pic_stop_watchdog(void)
{
	PIC_CHECK_INIT();
	return __pic_write_reg(PIC_WDT, PIC_WDT_STOP);
}

int pic_reset_timer(int sec)
{
	PIC_CHECK_INIT();
	return __pic_write_reg(PIC_HDD_RESET_TIMER, sec * HZ);
}
int pic_reset_hd(int idx)
{
	PIC_CHECK_INIT();
	return __pic_write_reg(PIC_HDD_RESET_START + idx, 1);
}
int pic_clear_reset_hd(int idx)
{
	PIC_CHECK_INIT();
	return __pic_write_reg(PIC_HDD_RESET_CLR_START + idx, 1);
}
