/*
Commandline class for shell
Written by: Andrew Baker & Dawson Buist
Date: 3.5.20
*/

#include <iostream>
#include <vector>
using namespace std;

class CommandLine
{
public:
  CommandLine();
  ~CommandLine();

  void BuildInput();

  // CommandLine(istream &in);

  char* getCommand() const { if(argc > 0) { return argv[0]; }}

  int getArgCount() const { return argc; }

  char** getArgVector() const { return argv; }

  char* getArgVector(int i) { if (argc > i) { return argv[i]; }}

  bool noAmpersand() const; //{ return !hasAmpersand; };

  bool exitCon() const;

private:
  int argc = 0;
  char **argv;
  vector<string> argvec;
  vector<string> strv;
  bool hasAmpersand = false;
};
