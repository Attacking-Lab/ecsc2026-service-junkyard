import std.stdio;
import std.file : read, readText;
import std.json;
import std.exception : enforce;
import std.getopt;
import std.process : environment;
import std.path : buildPath;
import languages;
import stats;

struct Parameters {
    string mode = "detect";
    string inputFile = "";
    double minConfidence = 0.0;
    string fallbackLanguage = "eng";
}

Parameters getParameters(string[] args) {
    Parameters p;

    // Parameters from CLI
    auto helpInformation = getopt(
        args,
        "mode", "Mode (detect or generate)", &p.mode,
        "f|file", "Input file", &p.inputFile,
        "c|confidence", "Minimum confidence", &p.minConfidence,
        "l|language", "Fallback language", &p.fallbackLanguage
    );

    if (helpInformation.helpWanted)
    {
        defaultGetoptPrinter("Language detection/generation tool", helpInformation.options);
        throw new Exception("parameters missing");
    }

    // Parameters from JSON (CLI usage)
    if (p.inputFile == "") {
        auto jsonInput = readln();
        auto jsonData = parseJSON(jsonInput);
        if ("file" in jsonData) {
            auto fileDir = environment.get("FILE_DIR", "/data/files");
            p.inputFile = buildPath(fileDir, jsonData["file"].str);
        }
        if ("min_confidence" in jsonData) {
            p.minConfidence = jsonData["min_confidence"].type == JSONType.integer ? jsonData["min_confidence"].integer : jsonData["min_confidence"].floating;
        }
        if ("fallback_language" in jsonData) {
            p.fallbackLanguage = jsonData["fallback_language"].str;
        }
    }

    // Check parameters
    enforce(p.mode == "detect" || p.mode == "analyze" || p.mode == "generate", "invalid mode '" ~ p.mode ~ "': expected detect or analyze or generate");

    return p;
}

void respond(T)(T data) {
    if (environment.get("GATEWAY_INTERFACE") !is null) {
        stdout.writeln("Content-Type: application/json; charset=utf-8");
        stdout.writeln();
    }

    JSONValue response = JSONValue(data);
    stdout.writeln(response.toJSON(true));
}

void detect(Parameters p) {
    // build profile for input file
    auto stats = getDigramStats(loadFile(p.inputFile));

    // compare to all loaded languages
    string bestLanguage = p.fallbackLanguage;
    real bestConfidence = 0.0;
    foreach (language; languages.allLanguages)
    {
        auto confidence = similarity(stats, loadLanguage(language));
        if (confidence >= p.minConfidence && confidence > bestConfidence)
        {
            bestLanguage = language.name;
            bestConfidence = confidence;
        }
    }

    // check if response is valid
    enforce(isLanguage(bestLanguage), "invalid language '" ~ bestLanguage ~"' is no known language");
    enforce(bestConfidence >= 0.0, "confidence cannot be negative");

    respond(["language": JSONValue(bestLanguage), "confidence": JSONValue(bestConfidence)]);
}

void analyze(Parameters p) {
    // build profile for input file
    auto stats = getDigramStats(loadFile(p.inputFile));

    // compare to all loaded languages
    real[string] result;
    foreach (language; languages.allLanguages)
    {
        result[language.name] = similarity(stats, loadLanguage(language));
    }

    respond(result);
}

void generate(Parameters p) {
    // build a profile for input file
    auto stats = getDigramStats(readText(p.inputFile));
    // save it
    auto lang = saveLanguage(p.fallbackLanguage, stats);
    respond(["name": lang.name, "filename": lang.filename]);
}

int main(string[] args)
{
    try
    {
        auto p = getParameters(args);
        if (p.mode == "detect") {
            initLanguages();
            detect(p);
        } else if (p.mode == "analyze") {
            initLanguages();
            analyze(p);
        } else if (p.mode == "generate") {
            generate(p);
        }
    }
    catch (Exception e)
    {
        writeln("error: ", e.msg);
        return 1;
    }

    return 0;
}
