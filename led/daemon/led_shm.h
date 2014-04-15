#ifndef LED_SHM__H__
#define LED_SHM__H__

extern int disk_max_num;
int sem_init(void);
int shm_init(void);
void shm_release(void);


#endif // LED_SHM__H__
