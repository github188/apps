#ifndef BUZZER_SHM__H__
#define BUZZER_SHM__H__

extern shm_t *addr;
int sem_init(void);
int shm_init(void);
void shm_release(void);


#endif // LED_SHM__H__
