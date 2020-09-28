/*
Commandline header file for shell
Written by: Andrew Baker & Dawson Buist
Date: 3.7.20
*/

#include <iostream>
#include <sstream>
#include <iterator>
#include <string>
#include <cstring>
#include <algorithm>
#include <stdlib.h>
#include <unistd.h>
#include "CommandLine.h"

CommandLine::CommandLine()
{
  argv = nullptr;
}

void CommandLine::BuildInput()
{
  for (int i = 0; i < argc; ++i)
  {
    delete argv[i];
  }

  string val;

  getline(cin, val);

  argc = 0;
  hasAmpersand = false;

  if (val.length() != 0 || val.find_first_not_of(' ') != std::string::npos)
  {
    stringstream ss(val);
    istream_iterator<string> begin(ss);
    istream_iterator<string> end;
    argvec = vector<string>(begin, end);
    //argvec.push_back(NULL);

    // if (std::find(argvec.begin(), argvec.end(), "&") != argvec.end())
    // {
    //   hasAmpersand = true;
    //   argvec.erase(find(argvec.begin(), argvec.end(), "&"));
    // }

    argc = argvec.size();

    argv = (char **)calloc(argc, sizeof(char *));

    for (int i = 0; i < argc; i++)
    {
      char *s2 = new char[argvec[i].size() + 1];
      strcpy(s2, argvec[i].c_str());
    }
    //argv[argc] = nullptr;
  }
}

CommandLine::~CommandLine()
{
  for (int i = 0; i < argc; ++i)
  {
    delete argv[i];
  }
  free(argv);
}

bool CommandLine::noAmpersand() const
{
  for (int i = 0; i < getArgCount(); i++)
  {
    if (argv[i] == "&")
    {
      return true;
    }
  }

  return false;
}

bool CommandLine::exitCon() const
{
  if (argc > 0 && std::string(getCommand()) == "exit")
  {
    return false;
  }
  return true;
}
