/*
Shell class
Written by: Andrew Baker & Dawson Buist
Date: 3.5.20
*/

#include <iostream>
#include <stdlib.h>
#include <unistd.h>
#include <string>
#include <cstring>
#include "DAShell.h"
//using namespace std;

DAShell::DAShell()
{
}

int DAShell::run()
{
    int exitval = 0;
    // n1 = fork();

    while (cl.exitCon())
    {
        cout << p.get();
        cl.BuildInput();
        decision();
        cout.flush();
    }

    return 0;
}

int DAShell::cd()
{
    if (cl.getArgCount() == 2)
    {
        chdir(cl.getArgVector(1));
        p.updatePrompt();
    }
    else
    {
        cout << "cd: too many arguments" << endl;
    }
}

int DAShell::decision()
{
    cout << "DECISION" << endl;
    cout << string(cl.getCommand()) << endl;
    if (strcmp(cl.getCommand(), "cd") == 0)
    {
        cout << "help" << endl
             << flush;
        cd();
    }
    if (strcmp(cl.getCommand(), "pwd") == 0)
    {
        cout << p.get() << endl;
    }
    else
    {
        pid_t n1;
        int status;
        n1 = fork();
        cout << "nice\n"
             << flush;
        if (n1 == 0) //Child Process
        {
            cout << "nice1\n"
                 << flush;
            cout << "nice3\n"
                 << flush;

            char *asdf2 = new char();
            string asdf1 = p2.getDirectory(p2.find(cl.getCommand())) + "/" + cl.getCommand();
            strcpy(asdf2, asdf1.c_str());

            execve(asdf2, cl.getArgVector(), NULL);

            cout << "WHY\n"
                 << flush;
        }
        else
        { //Parent Process
            waitpid(n1, &status, WUNTRACED | WCONTINUED);

            // while (w > 0)
            // {
            //     sleep(1);
            // }
        }

        // char p[] = "PATH=/bin/sh";
        // char u[] = "USER=me";

        // char * const env_args[] = {p, NULL};

        // execvp(cl.getCommand(), cl.getArgVector());
    }
}