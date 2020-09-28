/*
Path class for shell
Written by: Andrew Baker
Date: 3.5.20
*/

#include <iostream>
#include <vector>
#include <stdlib.h>
#include <dirent.h>
using namespace std;

class Path
{
public:
  Path();
  int find(const string &program) const;

  string getDirectory(int i) const;

  void removeLast();

private:
  vector<string> Paths;
};
