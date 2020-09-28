#include "Path.h"
#include <cstring>

//Default constructor for path class, creating a vector of strings of directories
Path::Path()
{
    unsigned i = 0;
    string temp;
    if (const char *env_p = std::getenv("PATH"))
    {
        while (i < strlen(env_p))
        {
            while (env_p[i] != ':')
            {
                temp += env_p[i];
                i++;
            }
            Paths.push_back(temp);
            i++;
            temp = "";
        }
    }
}

// finds if a directory is within the vector and returns the index within the vector if it is in it
int Path::find(const string &program) const
{
    for (unsigned i = 0; i < Paths.size(); i++)
    {
        DIR *dir_(opendir(Paths[i].c_str()));
        struct dirent *read;
        while (dir_)
        {
            if ((read = readdir(dir_)) != NULL)
            {
                if (strcmp(read->d_name, program.c_str()) == 0)
                {
                    closedir(dir_);
                    return i;
                }
            }
            else
            {
                closedir(dir_);
                break;
            }
            
        }

    }

    return -1;
}
// returns the directory at index i within the vector
string Path::getDirectory(int i) const
{
    return Paths[i];
}

void Path::removeLast()
{
    Paths.pop_back();
}
