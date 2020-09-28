/*
* Name: Dawson Buist
* Course: CS-232-B
* Date: 02/15/20
* 
* Copy.c copies the contents of one file into another file.
*
* Usage: ./copy <source-filename> <destination-filename>
*/


#include <stdio.h>
#include <string.h>
#include <unistd.h>
#include <sys/stat.h>

int main(int argc, char* argv[]) {
    FILE *fp = NULL;
    FILE *fp2 = NULL;
    char* src = argv[1];
    char* dest = argv[2];
    char c;
    struct stat buffer;
    stat(src, &buffer);

    //Makes sure the user provides a correct number of arguments
    if(argc != 3){
        fprintf( stderr, "Incorrect number of arguments!\n" );
        return -1;
    }

    //https://cboard.cprogramming.com/c-programming/133346-determine-file-type-linux.html
    //Makes sure the file is a regular file which can be read and copied
    if(S_ISREG(buffer.st_mode) == 0){
    	fprintf( stderr, "Bad file type for file %s!\n",src );
    	return -1;
    }

    //https://www.zentut.com/c-tutorial/c-read-text-file/
    //Verifies that the file does not have read protection stopping the file from being read
    if(access(src,R_OK) != 0) {
        fprintf( stderr, "Can't read from file %s\n",src);
        return -1;
    }

    //Opens a readable file
    fp = fopen(src, "r");
    if (fp == NULL){
        fprintf(stderr, "Unable to open file %s\n",src);
        return -1;
    }

    //Sets fp2 to be a readable file with the source location
    fp2 = fopen(dest, "r");
    if (fp2 != NULL){
        fprintf(stderr, "The file %s already exists\n",dest);
        return -1;
    }

    //Creates a writeable file at the destination location
    fp2 = fopen(dest, "w");
    if (fp2 == NULL){
        fprintf(stderr, "Unable to open file %s\n",dest);
        return -1;
    }

    //https://www.geeksforgeeks.org/c-program-copy-contents-one-file-another-file/

    c = fgetc(fp); 

    //Checks to see if the character is at the end of the file
    while (c != EOF) 
    { 
        fputc(c, fp2); 
        c = fgetc(fp); 
    } 

    fclose(fp);
    fclose(fp2);

    return 0;
}