This is made to work with Blender versions starting from 3.4 and ending with 4.0.

Before using this, you will want to run the following command in Blender's Console in the Scripting Tab:

import pip
pip.main(['install', 'pyyaml', 'ruamel.yaml', 'numpy', 'pyglm==2.7.0', 'ptvsd', 'Pillow', '--user'])


After that restart Blender.

- by TGE & Eternal Yoshi with thanks to Archer and others for stage material definitions.
Also thanks to Archer for his work on getting Camera features to work.