#include "Prompt.h"

// Default constructor for Prompt class
// Sets out to the command output
Prompt::Prompt()
{
    updatePrompt();
}

void Prompt::updatePrompt()
{
    char cwd[PATH_MAX];
    if (getcwd(cwd, PATH_MAX) != NULL)
    {
        out = cwd;
    }
}

// returns out, the command output
string Prompt::get() const
{
    return out + "$ ";
}