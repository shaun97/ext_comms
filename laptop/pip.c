// C program to implement one side of FIFO
// This side writes first, then reads
#include <stdio.h>
#include <string.h>
#include <fcntl.h>
#include <sys/stat.h>
#include <sys/types.h>
#include <unistd.h>



int main()
{
    int fd;

    // FIFO file path
    char *myfifo = "/tmp/myfifo";

    // Creating the named file(FIFO)
    // mkfifo(<pathname>, <permission>)
    mkfifo(myfifo, 0666);

    // Open FIFO for write only
    fd = open(myfifo, O_WRONLY);

    int counter = 0;
    while (1)
    {
        counter++;
        char arr[100] = "01 02 03 04 05 06 07 08 09 10 11 12 13 14                                                          ";

        // Write the input arr2ing on FIFO
        write(fd, arr, strlen(arr) + 1);
        if (counter % 20 == 0) {
            char arrs[100] = "R                                                                                                   ";
            write(fd, arrs, 100);
            write(fd, arrs, 100);
            write(fd, arrs, 100);
        }
        if (counter == 100) {
            break;
        }
    }

    close(fd);
    return 0;
}