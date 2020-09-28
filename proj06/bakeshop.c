#include <stdio.h>
#include <stdlib.h>
#include <pthread.h>
#include <time.h>
#include <semaphore.h>
#include <fcntl.h>
#include <unistd.h>

#define N_THREADS 12

sem_t shopSem;
sem_t mutexSem;
sem_t bakerSem;
sem_t custSem;
sem_t cashierSem;
sem_t paySem;
sem_t loafSem;
int count = 0;

void *shop(void *arg)
{
	int id = (int)arg;

    if (sem_wait (&shopSem) == -1) {
	    perror ("sem_wait: shopSem"); exit (1);
    }

    fprintf(stderr, "Customer #%d has entered the store\n", id);

    if (sem_wait (&mutexSem) == -1) {
	    perror ("sem_wait: mutexSem"); exit (1);
    }

    //wait for cashier to be available

    //shopping code

    if (sem_wait (&loafSem) == -1) {
    	perror ("sem_wait: loafSem"); exit (1);
  	}
    fprintf(stderr, "Customer #%d has taken a loaf of bread.\n", id);
    usleep(1000000); //unneeded for program to run smoothly

    if (sem_wait (&custSem) == -1) {
    	perror ("sem_wait: custSem"); exit (1);
  	}


    fprintf(stderr, "Customer #%d has paid for the loaf of bread.\n", id);
    fprintf(stderr, "Customer #%d has been handed their receipt.\n", id);
	fprintf(stderr, "Customer #%d has gotten their receipt.\n", id);



    if (sem_post (&paySem) == -1) {
	    perror ("sem_post: paySem"); exit (1);
   	}

    if (sem_post (&mutexSem) == -1) {
	    perror ("sem_post: mutexSem"); exit (1);
    }

    if (sem_post (&shopSem) == -1) {
	    perror ("sem_post: shopSem"); exit (1);
    }

    fprintf(stderr, "Customer #%d has left the store.\n", id);
}

void *baker(void *arg)
{		
	while(count < 10) {
		if (sem_wait (&cashierSem) == -1) {
	    	perror ("sem_wait: cashierSem"); exit (1);
   		}
    	usleep(1000000); //unneeded for program to run smoothly
        if (sem_post (&loafSem) == -1) {
	    	perror ("sem_post: loafSem"); exit (1);
    	}
    	count++;
    	fprintf(stderr, "A loaf of bread has been baked!\n");
    	usleep(1000000); //unneeded for program to run smoothly
    	if (sem_post (&bakerSem) == -1) {
	    	perror ("sem_post: bakerSem"); exit (1);
    	}
	}
	fprintf(stderr, "Baking is completed!\n");
}

void *cashier(void *arg)
{
    while(count < 10) {
		if (sem_wait (&bakerSem) == -1) {
	    	perror ("sem_wait: bakerSem"); exit (1);
   		}

        if (sem_post (&custSem) == -1) {
	    	perror ("sem_post: custSem"); exit (1);
    	}

    	if (sem_wait (&paySem) == -1) {
    		perror ("sem_wait: paySem"); exit (1);
  		}

        if (sem_post (&cashierSem) == -1) {
	    	perror ("sem_post: cashierSem"); exit (1);
    	}

    }
}


int main(int argc, char *argv[])
{
    fprintf(stderr, "Bakery is starting up...\n");

    sem_init(&shopSem, 0, 5);
    sem_init(&mutexSem, 0, 1);
    sem_init(&bakerSem, 0, 0);
    sem_init(&custSem, 0, 0);
    sem_init(&cashierSem, 0, 1);
    sem_init(&paySem, 0, 0);
    sem_init(&loafSem, 0, 0);

    pthread_t ts[N_THREADS];
    size_t i;

    pthread_create(&ts[0], NULL, &baker, NULL);
    pthread_create(&ts[1], NULL, &cashier, NULL);

    for (i = 2; i < N_THREADS; i++) {
        pthread_create(&ts[i], NULL, &shop, (void*)(i - 1));
        // fprintf(stderr, "Thread #%ld has been created\n", i);
    }

    pthread_exit(NULL);
}