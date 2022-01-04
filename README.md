# umvc3-tools
Ultimate Marvel vs Capcom 3 tools &amp; research

## Overview
This repository is home to various tools, including:
- Mt Framework Model (MOD) import/export plugin for 3ds Max 2021+
- Mt Framework Texture (TEX) converter
- Mt Framework Material (MTL) converter
- Binary templates for various file formats are contained in the ``templates/``. You can use these for debugging or manual editing.

## Usage
### Max Plugin ###
Run setup.bat in src/python/mtio/modules/mtmax before the first time you run the script.
From now onwards you can run plugin.py in the mtmax folder via Scripts -> Run Script.
So long as you keep the plugin window open, you don't have to reopen the plugin (unless it crashes and the UI becomes unresponsive)

### Texture converter ###
mttexconv is a script that can convert TEX files to DDS, PNG, TGA, and many other formats and vice versa.
The texture encoding type is decided based on the suffix of the texture. To ensure textures show up properly, make sure to follow the same naming convention for textures.
The tool has the option to force a specific format or specify an existing texture file to replicate via the command line. Specifying the existing texture is required for cubemaps.

For ease of use, a batch file is provided on which you can drag & drop files to convert.

### Material converter ###
mtmrlconv is a script that can convert MRL files to YML and vice versa. It allows for easy editing of material files.
For ease of use, a batch file is provided on which you can drag & drop files to convert.