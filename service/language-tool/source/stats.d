import std.file : readText, getSize;
import std.algorithm;
import std.math.rounding;
import std.math;
import std.exception : enforce;

const SIZE = 124;

uint getCharPoint(dchar c) {
    // 1-15
    if (c >= 32 && c <= 46) return c - 32 + 1;
    // 16-41
    if (c >= 65 && c <= 90) return c - 65 + 16;
    if (c >= 97 && c <= 122) return c - 97 + 16;
    // 42-74
    if (c >= 223 && c <= 255) return c - 223 + 42;

    // 75-98
    if (c >= 1072 && c <= 1119) return ((c - 1072) / 2) + 75;
    // 99-112
    if (c >= 940 && c <= 993) return ((c - 940) / 4) + 99;
    // 113-123
    if (c >= 1376 && c <= 1416) return ((c - 1376) / 4) + 113;

    return 0;
}

uint[] countDigrams(const string text)
{
    auto counts = new uint[](SIZE * SIZE);

    uint lastPoint = 0;
    foreach (dchar c; text)
    {
        uint point = getCharPoint(c);
        if (point != 0 && lastPoint != 0)
        {
            counts[lastPoint * SIZE + point]++;
        }
        lastPoint = point;
    }

    return counts;
}

uint[] distribution(uint[] data)
{
    uint sum = reduce!((a, b) => a + b)(0, data);
    if (sum > 0)
    {
        real factor = int.max * 1.0 / sum;
        foreach (i, item; data)
        {
            data[i] = cast(uint)lrint(item * factor);
        }
    }
    return data;
}

real similarity(uint[] dist1, uint[] dist2) {
    double result = 1.0;
    foreach (i, v1; dist1)
    {
        auto v2 = dist2[i];
        auto d = v1 > v2 ? v1 - v2 : v2 - v1;
        result *= 1 / (d/100000000.0 + 1);
    }

    return pow(result, 0.1);
}

uint[] getDigramStats(const string text)
{
    return distribution(countDigrams(text));
}

string loadFile(const string filename)
{
    auto size = getSize(filename);
    enforce(size > 0 && size < 1024*1024, "File too large");
    return readText(filename);
}