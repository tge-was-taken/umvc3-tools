import importlib
import os
import subprocess
import sys

import bpy

DEPENDENCIES = [
    ('glm',      'pyglm==2.7.0'),
    ('yaml',     'pyyaml'),
    ('ruamel.yaml', 'ruamel.yaml'),
    ('PIL',      'Pillow'),
]

lastImportError = None


def getAddonId():
    return __package__.rpartition('.')[0] or __package__


def getModulesPath():
    return bpy.utils.user_resource('SCRIPTS', path='modules', create=True)


def ensureModulesPathOnSysPath():
    path = getModulesPath()
    if path and path not in sys.path:
        sys.path.append(path)
    return path


def getMissingDependencies():
    # Names of the dependencies that cannot currently be imported.
    ensureModulesPathOnSysPath()
    missing = []
    for importName, pipName in DEPENDENCIES:
        try:
            importlib.import_module(importName)
        except ImportError:
            missing.append((importName, pipName))
    return missing


def _subprocessFlags():
    # Stops a console window flashing up on Windows.
    return getattr(subprocess, 'CREATE_NO_WINDOW', 0)


def _runPip(args):
    cmd = [sys.executable, '-m', 'pip', *args]
    print('umvc3-tools: ' + ' '.join(cmd))
    result = subprocess.run(
        cmd,
        capture_output=True,
        text=True,
        creationflags=_subprocessFlags() if os.name == 'nt' else 0,
    )
    if result.stdout:
        print(result.stdout)
    if result.stderr:
        print(result.stderr)
    return result


def installDependencies():
    target = ensureModulesPathOnSysPath()
    if not target:
        return False, 'could not locate a writable Blender scripts directory'

    # Blender usually ships pip, but some Linux builds do not.
    try:
        _runPip(['--version'])
    except Exception:
        try:
            subprocess.run([sys.executable, '-m', 'ensurepip'],
                           capture_output=True, text=True)
        except Exception as e:
            return False, f'pip is not available in this Blender install ({e})'

    missing = getMissingDependencies()
    if not missing:
        return True, 'nothing to install'

    failed = []
    for importName, pipName in missing:
        result = _runPip(['install', '--no-cache-dir', '--target', target, pipName])

        # The pinned version may have no wheel for this Blender's Python.
        if result.returncode != 0 and '==' in pipName:
            print(f'umvc3-tools: {pipName} failed, retrying unpinned')
            result = _runPip(['install', '--no-cache-dir', '--target', target,
                              pipName.split('==')[0]])

        if result.returncode != 0:
            failed.append(pipName)

    if failed:
        return False, 'failed to install: ' + ', '.join(failed)

    importlib.invalidate_caches()
    stillMissing = [name for name, _ in getMissingDependencies()]
    if stillMissing:
        return False, 'installed, but still cannot import: ' + ', '.join(stillMissing)

    return True, 'installed into ' + target


class SUB_OT_install_dependencies(bpy.types.Operator):
    bl_idname = 'umvc3.install_dependencies'
    bl_label = 'Install Dependencies'
    bl_description = ('Downloads and installs the Python packages this addon '
                      'needs into Blender.')
    bl_options = {'REGISTER', 'INTERNAL'}

    def execute(self, context):
        wm = context.window_manager
        wm.progress_begin(0, 1)
        try:
            ok, message = installDependencies()
        finally:
            wm.progress_end()

        if not ok:
            self.report({'ERROR'},
                        f'Dependency install failed: {message}. '
                        'See the system console for the full pip output.')
            return {'CANCELLED'}
        addon = importlib.import_module(getAddonId())
        try:
            addon.registerAddonModules()
        except Exception as e:
            print(f'umvc3-tools: deferred register failed: {e}')
            self.report({'WARNING'},
                        'Dependencies installed. Restart Blender to finish installation.')
            return {'FINISHED'}

        self.report({'INFO'}, 'Dependencies installed. Addon is ready.')
        return {'FINISHED'}


class UMVC3AddonPreferences(bpy.types.AddonPreferences):
    bl_idname = getAddonId()

    def draw(self, context):
        layout = self.layout
        missing = getMissingDependencies()

        if not missing:
            layout.label(text='All dependencies are installed.', icon='CHECKMARK')
            return

        box = layout.box()
        box.label(text='This addon cannot load until these are installed:',
                  icon='ERROR')
        for importName, pipName in missing:
            box.label(text=f'    {pipName}')

        if lastImportError is not None:
            box.label(text=str(lastImportError), icon='INFO')

        box.operator(SUB_OT_install_dependencies.bl_idname, icon='IMPORT')
        box.label(text='If this fails, run Blender as administrator and try again.')


classes = [
    SUB_OT_install_dependencies,
    UMVC3AddonPreferences,
]


def register():
    for cls in classes:
        try:
            bpy.utils.unregister_class(cls)
        except Exception:
            pass
        bpy.utils.register_class(cls)


def unregister():
    for cls in reversed(classes):
        try:
            bpy.utils.unregister_class(cls)
        except Exception:
            pass
