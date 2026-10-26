# The Junkyard
A file upcycler.
Takes either a bmp or a txt and does things to it.
The things it does are done via multiple smaller components, all in different languages.
General idea is that at least two vulns are required per flag store, but these vulns are not super hard.

Components:
- gateway
- inspector (actually apply changes)
- language-tool (detect language)
- spellchecker (do spellchecking depending on language)
- converter (convert between bmp and txt)
- cropper (crop out parts of an image)
- annotator (add crop/censor annotations to images)

Authors:
* mkb (Markus Bauer)
* singlechar (Simeon Hoffmann)


Categories:
* web
* misc


## Get things to run
Quick way: `cd meta && ./build.sh --keep`

### Build the Frontend
You need a somewhat recent NodeJS. 

- `cd service/frontend`
- `npm install`
- `npm run build`

### Build the languages
`cd meta && ./lang_build.sh`

### Main service
`cd service && docker compose up -d`

### Checkers
Go to `checker/`. Either:
- `docker compose up` and use the enochecker protocol
- Use `demo.py` and patch the variant you're testing


## Overview

### Flag Store 1
The gameserver uploads an image of a flag, but censors out the flag.

### Flag Store 2
The gameserver uploads a flag as private text file.

### Flag Store 3
The gameserver converts a flag, which leaves the flag file in the converter cache.


## Vulnerabilities

### Flag Store 1, Vuln 1

The cropper/censor and Julia's implementation of it are off-by-one, as julia starts counting at 1 instead of 0.
Example: censoring the full image still preserves one row of the original image.
Cropping the image shifts the leaked row, so you can leak the whole flag image row by row.
This assumes that you can crop a gameserver image, which vuln2 makes possible.

* Difficulty: medium
* Discoverability: medium
* Patchability: medium
* Categories: misc

There was a second, unintentional bug with similar effect: you could ask the cropper via vuln2 to crop the image to l=1900 t=100 r=0 b=0 (always double the width).
This led Julia to return an uncensored version of the image with negative width/height in the header.
Fixing the header by hand gave you the original image.
Internally, Julia's crop does request a chunk of memory even if both dimensions are negative but never initializes it (because all x/y are out of bounds).
If the requested image has been free'd before, you'll have the original image in this memory chunk.

The unintended vuln was found by Team UK, congrats!

### Flag Store 1, Vuln 2

The annotator checks authorization by comparing the username with `strncmp` in `tools.c`.
`strncmp` stops comparing after `n` bytes, which is the length of the owner's username.
If you register a username that starts with the owner's username plus some more characters, you can crop or censor a target's image.
This allows you to fully exploit vulnerability 1 to leak arbitrary images, even if they are private.

* Difficulty: medium
* Discoverability: medium
* Patchability: easy
* Categories: misc

### Flag Store 2, Vuln 1

Summary: Desync between HTTP / CGI / the D language tool leads to JSON injection.
JSON injection leads to path injection in the spellchecker.
Injecting into the dictionary file path leaks arbitrary txt files.

Attackers only have access to the gateway, which can connect to the spellchecker via HTTP. 
The spellchecker has a HTTP connection to the language tool, which runs as CGI binary. 

First, the attacker has to provoke an error in the language tool. 
Easiest way: setting the required confidence level over 100% and giving an invalid fallback language.
As a consequence, the language tool binary will crash and the user-provided fallback language is contained in its output (on stdout, not stderr).
Apache picks up that output but ignores the exit code. If the output includes two newlines, everything afterwards is the body of a successful HTTP response.
By controlling the fallback language, the attacker can inject arbitrary JSON (followed by some garbage) in the communication between language tool and spellchecker.
Go ignores the junk after a valid JSON body, thus the response is properly parsed.

Next, the attacker fakes a language tool response including `"language": "../../gateway/data/files/.../data"`.
As a consequence, the spellchecker uses the victim's `data.txt` file as its dictionary.
By checking a file with words like `ecsc_a_`, the attacker can provoke a correction response like `Did you mean one of: ECSC{flag}`.
The correction check is case insensitive and matches the first 7 chars only, so checking 2-3 files should retrieve any flag.

* Difficulty: medium
* Discoverability: hard
* Patchability: easy
* Categories: web

### Flag Store 3, Vuln 1

Java Hashcode collision.
The user object contains multiple fields, and the gateway does the auth. The converter itself
uses a subset of these fields to construct a string, and takes the hashcode of the string as hashcode
to index into a users map.
Java hashcode of strings is not collision-resistant, so an attacker can craft a user with different
credentials, but the same hashcode (and thus also equal user objects).

* Difficulty: medium
* Discoverability: easy 
* Patchability: easy
* Categories: misc, web, crypto

### Flag Store 3, Vuln 2

With vuln 1, one can auth as a user, but the gameserver stored the flag in an unknown file.
To know the file, one needs to trigger the "this is how a file name should look like" path.
This only happens if the path name itself is <256 characters, but the uppercase path name is
\>= 256 characters. This can be achieved for example with the `ß` character, which is 1
character in lowercase, but 2 in uppercase (`ß` -> `SS`).
With this, you leak the flag filename and can now easily retrieve it.

* Difficulty: medium
* Discoverability: medium
* Patchability: easy
* Categories: misc, web


## Patches

### Flag Store 1, Vuln 1
Fix the off-by-one.

### Flag Store 1, Vuln 2
Do not rely on `strncmp` alone, but also compare the string length with `strlen`.

### Flag Store 2, Vuln 1
Many points to patch this, pick one:
- Validate the user input in the gateway (fallback language must be a valid language)
- Print D's errors to stderr (or send proper headers before error output)
- Use the Go JSON decoder that does not ignore additional junk
- Sanitize the language tool response (checking for ../ should be enough)

### Flag Store 3, Vuln 1
Fix equality being based on String hashcode.

### Flag Store 3, Vuln 2
Make the character limit smaller.


## License

MIT License

