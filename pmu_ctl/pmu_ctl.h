#ifndef PMU_CTL_H
#define PMU_CTL_H

#define PMU_ADDRESS	(0x59)
enum {
	PMU_ERR_SUCCESS	= 0,	/* ok */
	PMU_ERR_NODEV	= -1,	/* Can't open i2c-0 */
	PMU_ERR_IOERR	= -2,	/* I2C access failed */
	PMU_ERR_INVAL	= -3,	/* Invalidate parameter */
};

struct pmu_info {
	float	vin;
	float	vout;
	float	fan_speed;
	float	temp;

	int	is_vin_fault : 1,
		is_vout_fault : 1,
		is_fan_fault : 1,
		is_temp_fault : 1;
};

int pmu_get_info(struct pmu_info *info);

#endif
