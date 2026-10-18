"author":"TGE's code adapted by Eternal Yoshi, Help and Export fix by ArcherOfLegend",
"version":(0,8),
"blender":(3,6,0),
"location": "View 3D > Tool Shelf > MT Framework",
"warning": "In progress.",
"category":"All",
}

def isDebugEnv():
    import os
    return os.path.exists( os.path.join( os.path.dirname( __file__ ), '.debug' ) )

def attachDebugger():
    try:
        import ptvsd
        print( ptvsd.enable_attach() )
    except:
        pass

import bpy
import nodeitems_utils
import os, sys, time, traceback, mathutils, re, subprocess, enum, math
import numpy as np
from mathutils import Vector, Matrix
from mathutils import Euler
from . import dependencies

def check_unsupported_blender_versions():
    if bpy.app.version < (3, 4):
        raise ImportError('Unfortunately versions earlier than 3.6 cannot be used. Please use Blender 3.6 - 4.3.')


def _force_unregister(classes):
    for cls in reversed(classes):
        try:
            bpy.utils.unregister_class(cls)
        except Exception:
            pass


def _drop_scene_props():
    try:
        del bpy.types.Scene.sub_scene_properties
    except Exception:
        pass


# True once the classes that need glm et al. are registered.
_modulesRegistered = False


def registerAddonModules():
    global _modulesRegistered
    if _modulesRegistered:
        return

    from . import modules
    from . import mtlib
    from .mtlib import properties

    from .bpy_classes import classes
    _force_unregister(classes)

    # Material.mt_entry (the editable MRL entry) before the panels that draw it
    from .modules import mt_mrl_props
    mt_mrl_props.register()

    for cls in classes:
        bpy.utils.register_class(cls)

    properties.register()
    try:
        from .modules import mt_exact
        mt_exact.register_handlers()
    except Exception as e:
        print(f'umvc3-tools: outline camera handler not registered: {e}')
    _modulesRegistered = True

    print('\nLoaded!')


def unregisterAddonModules():
    global _modulesRegistered
    if not _modulesRegistered:
        return

    try:
        from .modules import mt_exact
        mt_exact.unregister_handlers()
    except Exception:
        pass
    from .bpy_classes import classes
    for cls in reversed(classes):
        try:
            bpy.utils.unregister_class(cls)
        except RuntimeError as e:
            print(f'Failed to unregister thing; Error="{e}" ; Traceback=\n{traceback.format_exc()}')
    try:
        from .modules import mt_mrl_props
        mt_mrl_props.unregister()
    except Exception:
        pass

    _drop_scene_props()
    _modulesRegistered = False


def register():
    check_unsupported_blender_versions()
    dependencies.register()
    dependencies.ensureModulesPathOnSysPath()

    try:
        registerAddonModules()
    except ImportError as e:
        dependencies.lastImportError = e
        missing = ', '.join(name for name, _ in dependencies.getMissingDependencies())
        print(f'umvc3-tools: missing dependencies ({missing or e}).')
        print('umvc3-tools: open Edit > Preferences > Add-ons > UMVC3 Model Importer '
              'and press Install Dependencies.')


def unregister():
    unregisterAddonModules()
    dependencies.unregister()



if __name__ == "__main__":
    register()
bl_info = {
"name": "UMVC3 Model Importer",
"description":"For importing UMVC3 Models.",
"author":"TGE's code adapted by Eternal Yoshi, Help and Export fix by ArcherOfLegend",
"version":(0,7,1),
"blender":(3,4,0),
"location": "View 3D > Tool Shelf > MT Framework",
"warning": "In progress.",
"category":"All",
}

def isDebugEnv():
    import os
    return os.path.exists( os.path.join( os.path.dirname( __file__ ), '.debug' ) )

def attachDebugger():
    try:
        import ptvsd
        print( ptvsd.enable_attach() )
    except:
        pass

import bpy
import nodeitems_utils
import os, sys, time, traceback, mathutils, re, subprocess, enum, math
import numpy as np
from mathutils import Vector, Matrix
from mathutils import Euler
from . import dependencies

def check_unsupported_blender_versions():
    if bpy.app.version < (3, 4):
        raise ImportError('Unfortunately versions earlier than 3.4 cannot be used. Please use Blender 3.4 - 4.3.')


def _force_unregister(classes):
    for cls in reversed(classes):
        try:
            bpy.utils.unregister_class(cls)
        except Exception:
            pass


def _drop_scene_props():
    try:
        del bpy.types.Scene.sub_scene_properties
    except Exception:
        pass


# True once the classes that need glm et al. are registered.
_modulesRegistered = False


def registerAddonModules():
    global _modulesRegistered
    if _modulesRegistered:
        return

    from . import modules
    from . import mtlib
    from .mtlib import properties

    from .bpy_classes import classes
    _force_unregister(classes)

    for cls in classes:
        bpy.utils.register_class(cls)

    properties.register()
    _modulesRegistered = True

    print('\nLoaded!')


def unregisterAddonModules():
    global _modulesRegistered
    if not _modulesRegistered:
        return

    from .bpy_classes import classes
    for cls in reversed(classes):
        try:
            bpy.utils.unregister_class(cls)
        except RuntimeError as e:
            print(f'Failed to unregister thing; Error="{e}" ; Traceback=\n{traceback.format_exc()}')

    _drop_scene_props()
    _modulesRegistered = False


def register():
    check_unsupported_blender_versions()
    dependencies.register()
    dependencies.ensureModulesPathOnSysPath()

    try:
        registerAddonModules()
    except ImportError as e:
        dependencies.lastImportError = e
        missing = ', '.join(name for name, _ in dependencies.getMissingDependencies())
        print(f'umvc3-tools: missing dependencies ({missing or e}).')
        print('umvc3-tools: open Edit > Preferences > Add-ons > UMVC3 Model Importer '
              'and press Install Dependencies.')


def unregister():
    unregisterAddonModules()
    dependencies.unregister()



if __name__ == "__main__":
    register()
