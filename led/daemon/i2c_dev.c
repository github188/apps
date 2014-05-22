#include <sys/types.h>
#include <sys/stat.h>
#include <fcntl.h>
#include <unistd.h>
#include <stdint.h>
#include <stdio.h>
#include "i2c_dev.h"

#define I2C_DEV "/dev/i2c-i801"

static int i2c_is_initialized;
static int i2c_fd;


int do_write_disk_3U(int mode, uint8_t reg1, uint8_t reg2)
{
	int count = 10;
	int value;
	int ret;
	
	while(count--) {
		value = i2c_smbus_read_byte_data(i2c_fd, reg2);
		if (value == -1)
			continue;
		value &= 0xf0;
		ret = i2c_smbus_write_byte_data(i2c_fd, reg2, value);
		if (ret == -1)
			continue;
		
		ret = i2c_smbus_write_byte_data(i2c_fd ,reg1, mode);
		if (ret == 0)
			return PERR_SUCCESS;
	}
	return PERR_IOERR;

}

int i2c_write_disk_3U(int mode)
{
	
	uint8_t reg1, reg2;
	int  mode1, mode2, mode3, mode4;


	mode1 = mode & 0xf;
	mode2 = (mode >> 4) & 0xf;
	mode3 = (mode >> 8) & 0xf;
	mode4 = (mode >> 12) & 0xf;

	if (ioctl(i2c_fd, I2C_SLAVE_FORCE, I2C_ADDRESS_3U1) < 0) {
		return PERR_NODEV;
	}
	reg1 = I2C_GP1_MODE1;
	reg2 = I2C_GP1_MODE2;
	if (do_write_disk_3U(mode1, reg1, reg2) < 0) {
		return PERR_IOERR;
	}
	reg1 = I2C_GP2_MODE1;
	reg2 = I2C_GP2_MODE2;
	if (do_write_disk_3U(mode2, reg1, reg2) < 0) {
		return PERR_IOERR;
	}

	
	if (ioctl(i2c_fd, I2C_SLAVE_FORCE, I2C_ADDRESS_3U2) < 0) {
		return PERR_NODEV;
	}
	reg1 = I2C_GP1_MODE1;
	reg2 = I2C_GP1_MODE2;
	if (do_write_disk_3U(mode3, reg1, reg2) < 0) {
		return PERR_IOERR;
	}
	reg1 = I2C_GP2_MODE1;
	reg2 = I2C_GP2_MODE2;
	if (do_write_disk_3U(mode4, reg1, reg2) < 0) {
		return PERR_IOERR;
	}
	
	return PERR_SUCCESS;
}

int do_init_3U(int fd)
{
	
	int  ret;
	uint8_t g_config_reg_value;
	int value;

	g_config_reg_value = i2c_smbus_read_byte_data(fd, I2C_CONF_3U);
	if (g_config_reg_value == 255) {
		return PERR_IOERR;
	}
	g_config_reg_value |= 0x80;
	ret = i2c_smbus_write_byte_data(fd, I2C_CONF_3U, g_config_reg_value);
	if (ret == -1)
		return PERR_IOERR;

	value = i2c_smbus_read_byte_data(fd, I2C_GP1_MODE1);
	value |= 0x0f;
	ret = i2c_smbus_write_byte_data(fd, I2C_GP1_MODE1, value);
	if (ret == -1)
		return PERR_IOERR;
	value = i2c_smbus_read_byte_data(fd, I2C_GP1_MODE2);
	if (value == -1)
		return PERR_IOERR;
	value &= 0xf0;
	ret = i2c_smbus_write_byte_data(fd, I2C_GP1_MODE2, value);
	if (ret == -1)
		return PERR_IOERR;

	value = i2c_smbus_read_byte_data(fd, I2C_GP2_MODE1);
	value |= 0x0f;
	ret = i2c_smbus_write_byte_data(fd, I2C_GP2_MODE1, value);
	if (ret == -1)
		return PERR_IOERR;
	value = i2c_smbus_read_byte_data(fd, I2C_GP2_MODE2);
	if (value == -1)
		return PERR_IOERR;
	value &= 0xf0;
	ret = i2c_smbus_write_byte_data(fd, I2C_GP2_MODE2, value);
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

	if (ioctl(fd, I2C_SLAVE_FORCE, I2C_ADDRESS_3U1) < 0) {
		close(fd);
		return PERR_NODEV;
	}

	if (do_init_3U(fd) < 0) {
		close(fd);
		return PERR_IOERR;
	}

	if (ioctl(fd, I2C_SLAVE_FORCE, I2C_ADDRESS_3U2) < 0) {
		close(fd);
		return PERR_IOERR;
	}

	if (do_init_3U(fd) < 0) {
		close(fd);
		return PERR_IOERR;
	}

	i2c_is_initialized = 1;
	i2c_fd = fd;
	return 0;

}

void i2c_release_3U(void)
{
	close(i2c_fd);
	i2c_is_initialized = 0;

}

/* 2U */
int do_write_disk_2U(int mode, uint8_t reg1, uint8_t reg2)
{
	int count = 10;
	int value;
	int ret;
	
	while(count--) {
		value = i2c_smbus_read_byte_data(i2c_fd, reg2);
		if (value == -1)
			continue;
		value &= 0xf0;
		ret = i2c_smbus_write_byte_data(i2c_fd, reg2, value);
		if (ret == -1)
			continue;
		
		ret = i2c_smbus_write_byte_data(i2c_fd ,reg1, mode);
		if (ret == 0)
			return PERR_SUCCESS;
	}
	return PERR_IOERR;

}

int i2c_write_disk_2U(int mode)
{
	uint8_t reg1, reg2;
	int mode1, mode2;

	mode1 = mode & 0xf;
	mode2 = (mode>>4) & 0xf;


	reg1 = I2C_GP1_MODE1;
	reg2 = I2C_GP1_MODE2;
	if (do_write_disk_2U(mode1, reg1, reg2) < 0) {
		return PERR_IOERR;
	}
	reg1 = I2C_GP2_MODE1;
	reg2 = I2C_GP2_MODE2;
	if (do_write_disk_2U(mode2, reg1, reg2) < 0) {
		return PERR_IOERR;
	}
	return PERR_SUCCESS;
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

	value = i2c_smbus_read_byte_data(fd, I2C_GP1_MODE1);
	value |= 0x0f;
	ret = i2c_smbus_write_byte_data(fd, I2C_GP1_MODE1, value);
	if (ret == -1)
		return PERR_IOERR;
	value = i2c_smbus_read_byte_data(fd, I2C_GP1_MODE2);
	if (value == -1)
		return PERR_IOERR;
	value &= 0xf0;
	ret = i2c_smbus_write_byte_data(fd, I2C_GP1_MODE2, value);
	if (ret == -1)
		return PERR_IOERR;

	value = i2c_smbus_read_byte_data(fd, I2C_GP2_MODE1);
	value |= 0x0f;
	ret = i2c_smbus_write_byte_data(fd, I2C_GP2_MODE1, value);
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

void i2c_release_2U(void)
{
	close(i2c_fd);
	i2c_is_initialized = 0;
}
