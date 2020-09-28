/*
Shell header file
Written by: Andrew Baker & Dawson Buist
Date: 3.5.20
*/

#include <iostream>
#include <unistd.h>
#include <stdio.h>
#include <limits.h>
#include "Prompt.h"
#include "CommandLine.h"
#include "Path.h"
#include <sys/wait.h>
#include <stdio.h>

using namespace std;

class DAShell
{
public:
  DAShell();
  int run();
  int cd();
  int decision();

private:
  CommandLine cl = CommandLine();
  Prompt p = Prompt();
  Path p2 = Path();
};
