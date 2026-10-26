import std.file : dirEntries, SpanMode, read, write;
import std.path : baseName, stripExtension;
import std.algorithm : filter, map;
import std.array : array;
import std.path : buildPath;
import std.process : environment;

string LANGUAGE_PATH;

static this() {
    LANGUAGE_PATH = environment.get("LANG_DIR", "/languages");
}

struct Language {
    string name;
    string filename;
}

Language[] allLanguages;

void initLanguages()
{
    allLanguages = dirEntries(LANGUAGE_PATH, "*.stat", SpanMode.shallow)
    .map!(entry => Language(baseName(stripExtension(entry.name)), entry.name))
    .array;
}

bool isLanguage(string name)
{
    foreach (language; allLanguages)
    {
        if (language.name == name)
        {
            return true;
        }
    }
    return false;
}

uint[] loadLanguage(Language language)
{
    return cast(uint[]) read(language.filename);
}

Language saveLanguage(string name, uint[] stats)
{
    write(buildPath(LANGUAGE_PATH, name ~ ".stat"), stats);
    return Language(name, buildPath(LANGUAGE_PATH, name ~ ".stat"));
}
