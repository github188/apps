#ifndef I2C_DEV_H__
#define I2C_DEV_H__

#include <stdbool.h>
#include <stdint.h>
#include "../../pic_ctl/pic_ctl.h"

#define I2C_CONF_2U	(0x22)
#define I2C_CONF_3U	(0x22)

enum {
	I2C_ADDRESS_2U= (0x30 >> 1),
	I2C_ADDRESS_3U1 = (0x3c >> 1),
	I2C_ADDRESS_3U2= (0x3E >> 1),
};

enum {
	I2C_LED_NUMBER_3U = 16,
	I2C_LED_NUMBER_2U = 8,


	I2C_GP1_MODE1	= 0x01,
	I2C_GP1_MODE2	= 0x03,
	I2C_GP2_MODE1	= 0x11,
	I2C_GP2_MODE2	= 0x13,

	I2C_LED_OFF	= 0x1,
	I2C_LED_ON	= 0x0,


	I2C_LED_DISK_MASK_2U	= 0x3,
	I2C_LED_DISK_MASK_3U	= 0x3,
};

int i2c_write_disk_2U(int disk_id, int v);
int i2c_write_disk_3U(int disk_id, int v);
int i2c_init_3U(void);
int i2c_init_2U(void);
bool sb_gpio28_set(bool);

#endif
