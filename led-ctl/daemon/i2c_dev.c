#include <sys/types.h>
#include <sys/stat.h>
#include <fcntl.h>
#include <unistd.h>
#include <stdint.h>
#include <stdio.h>
#include "../../pic_ctl/i2c-dev.h"
#include "i2c_dev.h"

#define I2C_DEV "/dev/i2c-0"



#define I2C_CHECK_INIT_2U()	do {		\
		int ret = i2c_init_2U();	\
		if (ret  < 0)			\
			return ret;		\
	} while(0)

#define I2C_CHECK_INIT_3U()	do {		\
		int ret = i2c_init_3U();	\
		if (ret < 0)			\
			return ret;		\
	} while(0)



static int i2c_is_initialized;
static int i2c_fd;

/* 简易3U */
int i2c_init_3U2(void)
{
	int  ret;
	uint8_t g_config_reg_value;
	int value;
	
	I2C_CHECK_INIT_3U();

	if (ioctl(i2c_fd, I2C_SLAVE_FORCE, I2C_ADDRESS_3U2) < 0) {
		close(i2c_fd);
		return PERR_NODEV;
	}

	g_config_reg_value = i2c_smbus_read_byte_data(i2c_fd, I2C_CONF_3U);
	if (g_config_reg_value == 255) {
		return PERR_IOERR;
	}
	g_config_reg_value |= 0x80;
	ret = i2c_smbus_write_byte_data(i2c_fd, I2C_CONF_3U, g_config_reg_value);
	if (ret == -1)
		return PERR_IOERR;
	
	value = i2c_smbus_read_byte_data(i2c_fd, I2C_GP1_MODE2);
	if (value == -1)
		return PERR_IOERR;
	value &= 0xf0;
	ret = i2c_smbus_write_byte_data(i2c_fd, I2C_GP1_MODE2, value);
	if (ret == -1)
		return PERR_IOERR;
	value = i2c_smbus_read_byte_data(i2c_fd, I2C_GP2_MODE2);
	if (value == -1)
		return PERR_IOERR;
	value &= 0xf0;
	ret = i2c_smbus_write_byte_data(i2c_fd, I2C_GP2_MODE2, value);
	if (ret == -1)
		return PERR_IOERR;
	return 0;

}

int i2c_init_3U1(void)
{
	int  ret;
	uint8_t g_config_reg_value;
	int value;
	
	I2C_CHECK_INIT_3U();
	if (ioctl(i2c_fd, I2C_SLAVE_FORCE, I2C_ADDRESS_3U1) < 0) {
		close(i2c_fd);
		return PERR_NODEV;
	}
	
	g_config_reg_value = i2c_smbus_read_byte_data(i2c_fd, I2C_CONF_3U);
	if (g_config_reg_value == 255) {
		return PERR_IOERR;
	}
	printf("init\n");
	g_config_reg_value |= 0x80;
	ret = i2c_smbus_write_byte_data(i2c_fd, I2C_CONF_3U, g_config_reg_value);
	if (ret == -1)
		return PERR_IOERR;
	
	value = i2c_smbus_read_byte_data(i2c_fd, I2C_GP1_MODE2);
	if (value == -1)
		return PERR_IOERR;
	value &= 0xf0;
	ret = i2c_smbus_write_byte_data(i2c_fd, I2C_GP1_MODE2, value);
	if (ret == -1)
		return PERR_IOERR;
	value = i2c_smbus_read_byte_data(i2c_fd, I2C_GP2_MODE2);
	if (value == -1)
		return PERR_IOERR;
	value &= 0xf0;
	ret = i2c_smbus_write_byte_data(i2c_fd, I2C_GP2_MODE2, value);
	if (ret == -1)
		return PERR_IOERR;
	return 0;
}

int i2c_read_disk_3U(int disk_id, int *v)
{
	int ret;
	uint8_t reg1, reg2;
	int value;

	if (disk_id >= I2C_LED_NUMBER_3U)
		return PERR_INVAL;
	if (disk_id < I2C_LED_NUMBER_3U / 2) {
		i2c_init_3U1();
	}
	else {
		i2c_init_3U2();
	}
	
	if (disk_id < I2C_LED_NUMBER_3U/4 || 
	(disk_id >= I2C_LED_NUMBER_3U/2 && disk_id < (I2C_LED_NUMBER_3U - (I2C_LED_NUMBER_3U)/4)))
	{
		reg1 = I2C_GP1_MODE1;
		reg2 = I2C_GP1_MODE2;

	} else {
		reg1 = I2C_GP2_MODE1;
		reg2 = I2C_GP2_MODE2;
	}
	value = i2c_smbus_read_byte_data(i2c_fd, reg2);
	if (value == -1)
		return PERR_IOERR;
	value &= 0xf0;
	ret = i2c_smbus_read_byte_data(i2c_fd, reg2);
	if (ret == -1)
		return PERR_IOERR;
	
	ret = i2c_smbus_read_byte_data(i2c_fd, reg1);
	if (ret == -1)
		return PERR_IOERR;
	/* 获取单个灯的状态 */
	if ( ret & (1 << (disk_id & I2C_LED_DISK_MASK_3U)) )
		*v = 1;
	else 
		*v = 0;
	return 0;
}

int i2c_write_disk_3U(int disk_id, int mode)
{
	int ret;
	uint8_t reg1, reg2;
	int value;

	
	if (disk_id >= I2C_LED_NUMBER_3U)
		return PERR_INVAL;
	if (disk_id < I2C_LED_NUMBER_3U / 2) {
		i2c_init_3U1();
	}
	else {
		i2c_init_3U2();
	}
	
	if (disk_id < I2C_LED_NUMBER_3U/4 || 
	(disk_id >= I2C_LED_NUMBER_3U/2 && disk_id < (I2C_LED_NUMBER_3U - (I2C_LED_NUMBER_3U)/4)))
	{
		reg1 = I2C_GP1_MODE1;
		reg2 = I2C_GP1_MODE2;

	} else {
		reg1 = I2C_GP2_MODE1;
		reg2 = I2C_GP2_MODE2;
	}
	value = i2c_smbus_read_byte_data(i2c_fd, reg2);
	if (value == -1)
		return PERR_IOERR;
	value &= 0xf0;
	ret = i2c_smbus_write_byte_data(i2c_fd, reg2, value);
	if (ret == -1)
		return PERR_IOERR;
	
	value = i2c_smbus_read_byte_data(i2c_fd, reg1-1);
	if (value == -1)
		return PERR_IOERR;
	if (mode)
		value = value | (1 << (disk_id & I2C_LED_DISK_MASK_3U));
	else 
		value = value & ~(1 << (disk_id & I2C_LED_DISK_MASK_3U));

	ret = i2c_smbus_write_byte_data(i2c_fd ,reg1, value);
	if (ret == -1)
		return PERR_IOERR;
	return 0;
}

int i2c_init_3U(void)
{
	int fd;

	if (i2c_is_initialized)
		return 0;
	fd = open(I2C_DEV, O_RDWR);
	if (fd < 0)
		return PERR_NODEV;
	
	i2c_is_initialized = 1;
	i2c_fd = fd;
	return 0;

}
/* 2U */
int i2c_read_disk_2U(int disk_id, int *v)
{
	int ret;
	uint8_t reg1, reg2;
	int value;

	I2C_CHECK_INIT_2U();


	if (disk_id >= I2C_LED_NUMBER_2U)
		return PERR_INVAL;

	/* 判断使用GP1 还是GP2 */
	if (disk_id < I2C_LED_NUMBER_2U / 2) {
		reg1 = I2C_GP1_MODE1;
		reg2 = I2C_GP1_MODE2;
	}
	else {
		reg1 = I2C_GP2_MODE1;
		reg2 = I2C_GP2_MODE2;
	}
	value = i2c_smbus_read_byte_data(i2c_fd, reg2);
	if (value == -1)
		return PERR_IOERR;
	value &= 0xf0;
	ret = i2c_smbus_read_byte_data(i2c_fd, reg2);
	if (ret == -1)
		return PERR_IOERR;
	
	ret = i2c_smbus_read_byte_data(i2c_fd, reg1);
	if (ret == -1)
		return PERR_IOERR;
	/* 获取单个灯的状态 */
	if ( ret & (1 << (disk_id & I2C_LED_DISK_MASK_2U)) )
		*v = 1;
	else 
		*v = 0;
	return 0;
}

int i2c_write_disk_2U(int disk_id, int mode)
{
	int ret;
	uint8_t reg1, reg2;
	int value;

	I2C_CHECK_INIT_2U();
	
	
	if (disk_id >= I2C_LED_NUMBER_2U)
		return PERR_INVAL;
	if (disk_id < I2C_LED_NUMBER_2U / 2) {
		reg1 = I2C_GP1_MODE1;
		reg2 = I2C_GP1_MODE2;
	}
	else {
		reg1 = I2C_GP2_MODE1;
		reg2 = I2C_GP2_MODE2;
	}
	
	value = i2c_smbus_read_byte_data(i2c_fd, reg2);
	if (value == -1)
		return PERR_IOERR;
	value &= 0xf0;
	ret = i2c_smbus_write_byte_data(i2c_fd, reg2, value);
	if (ret == -1)
		return PERR_IOERR;
	
	value = i2c_smbus_read_byte_data(i2c_fd, reg1-1);
	if (value == -1)
		return PERR_IOERR;
	if (mode)
		value = value | (1 << (disk_id & I2C_LED_DISK_MASK_2U));
	else 
		value = value & ~(1 << (disk_id & I2C_LED_DISK_MASK_2U));

	ret = i2c_smbus_write_byte_data(i2c_fd ,reg1, value);
	if (ret == -1)
		return PERR_IOERR;
	return 0;
}

int i2c_init_2U(void)
{
	int fd, ret;
	uint8_t g_config_reg_value;
	int value;
	
	if (i2c_is_initialized)
		return 0;
	fd = open(I2C_DEV, O_RDWR);
	if (fd < 0)
		return PERR_NODEV;

	if (ioctl(fd, I2C_SLAVE_FORCE, I2C_ADDRESS_2U) < 0) {
		close(fd);
		return PERR_NODEV;
	}

	g_config_reg_value = i2c_smbus_read_byte_data(fd, I2C_CONF_2U);
	if (g_config_reg_value == 255) {
		return PERR_IOERR;
	}
	g_config_reg_value |= 0x80;
	ret = i2c_smbus_write_byte_data(fd, I2C_CONF_2U, g_config_reg_value);
	if (ret == -1)
		return PERR_IOERR;
	
	value = i2c_smbus_read_byte_data(fd, I2C_GP1_MODE2);
	if (value == -1)
		return PERR_IOERR;
	value &= 0xf0;
	ret = i2c_smbus_write_byte_data(fd, I2C_GP1_MODE2, value);
	if (ret == -1)
		return PERR_IOERR;
	value = i2c_smbus_read_byte_data(fd, I2C_GP2_MODE2);
	if (value == -1)
		return PERR_IOERR;
	value &= 0xf0;
	ret = i2c_smbus_write_byte_data(fd, I2C_GP2_MODE2, value);
	if (ret == -1)
		return PERR_IOERR;

	i2c_is_initialized = 1;
	i2c_fd = fd;
	return 0;
}
