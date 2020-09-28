/*
Prompt class header for shell
Written by: Andrew Baker & Dawson Buist
Date: 3.5.20
*/

#include <iostream>
#include <unistd.h>
#include <stdio.h>
#include <limits.h>
using namespace std;

class Prompt {
public:
  Prompt();
  string get() const;
  void updatePrompt();
  
private:
  string out;

};
