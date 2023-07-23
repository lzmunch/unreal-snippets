"""
Functions for batch importing Alembic and FBX assets into Unreal Engine

Generally, dragging multiple assets into Unreal results in needing to manually
step through a UI dialog for each asset. These batch import functions help
avoid that. This is also useful for making sure the same import settings 
are applied to all imported files. 

I've also included ways to make an exception to bring up a UI dialog for
certain files that require special adjustment.

== Overview ==
Unreal's Python API allows you to script imports like this:
1. Create an Import Options object. Unreal has different functions to do
   this for each filetype.
2. Create an ImportTask and add your Import Options to it.
3. Create an instance of the Asset Tools helper
4. Pass a list of ImportTasks to the instance

---
UE Version: 5.0.2
Author: Lauren Zhang
Date: 07/22/2023
"""

import unreal
import os

# creating an instance here for convenience
ASSET_TOOLS = unreal.AssetToolsHelpers.get_asset_tools()

def buildStaticMeshImportTask(srcPath, dstDir, automated, replaceExisting):
    """
    Build import task for FBX file

    Params:
        srcDir (str) : directory of the asset to import, e.g. C:/Users/foo/dev
        dstDir (str) : game directory to import into, e.g. /Game/Characters/
        automated (bool) : import setting. If true, skip UI dialog
        replaceExisting (bool): import setting. If true, old assets will be overwritten

    Returns:
        unreal.AssetImportTask
    """
    # build options
    importOptions = unreal.FbxImportUI()
    importOptions.set_editor_properties({
        'import_mesh': True,
        'import_textures': False,
        'import_materials': False,
        'import_as_skeletal': False
    })

    # build import task
    importTask = unreal.AssetImportTask()
    importTask.set_editor_properties({
        'destination_path': dstDir,
        'automated': automated,
        'options': importOptions,
        'filename': srcPath,
        'replace_existing': replaceExisting
    })

    return importTask

def buildAlembicImportTask(srcPath, dstDir, automated, replaceExisting):
    """
    Build import task for Alembic file

    Params:
        srcDir (str) : directory of the asset to import, e.g. C:/Users/foo/dev
        dstDir (str) : game directory to import into, e.g. /Game/Characters/
        automated (bool) : import setting. If true, skip UI dialog
        replaceExisting (bool): import setting. If true, old assets will be overwritten

    Returns:
        unreal.AssetImportTask
    """
    importOptions = unreal.AbcImportSettings()
    importOptionProps = {
        "import_type": unreal.AlembicImportType.GEOMETRY_CACHE,
        "conversion_settings": unreal.AbcConversionSettings(
                                                preset=unreal.AbcConversionPreset.MAX,
                                                rotation=[90.0, 0.0, 0.0]),
        "geometry_cache_settings": unreal.AbcGeometryCacheSettings(flatten_tracks=True),
        "sampling_settings": unreal.AbcSamplingSettings(skip_empty=True)
    }
    importOptions.set_editor_properties(importOptionProps)
     

    importTask = unreal.AssetImportTask()
    importTaskProps = {
        'destination_path': dstDir,
        'automated': automated,
        'options': importOptions,
        'filename': srcPath,
        'replace_existing': replaceExisting,
        'save': True
    }
    importTask.set_editor_properties(importTaskProps)

    return importTask

def shouldManuallyImportABC(file):
    """ 
    Stub function.
    Returns True if file should be manually imported (based on filename)
    For example, manually import any file with the word "eye"

    Params:
        file (str)
    Returns:
        bool
    """
    return 'eye' in file.lower()

def shouldManuallyImportFBX(file):
    """ 
    Stub function.
    Returns True if file should be manually imported (based on filename)
    For example, manually import any file with the word "character"

    Params:
        file (str)
    Returns:
        bool
    """
    return 'character' in file.lower()

def buildImportTaskList(filetype, srcPath, gameDir, replaceExisting=False):
    """
    Build list of import tasks for importing all files from srcPath to gameDir
    Params:
        fileytpe (str) : abc | fbx
        srcDir (str) : directory of the asset to import, e.g. C:/Users/foo/dev
        gameDir (str) : game directory to import into, e.g. /Game/Characters/
        replaceExisting (bool): will be passed to import settings. If true, 
                                old assets will be overwritten
    Returns:
        tuple(list(unreal.AssetImportTask), list(unreal.AssetImportTask))
    """
    if filetype.lower() == 'abc':
        buildImportTask = buildAlembicImportTask
        shouldManuallyImport = shouldManuallyImportABC
    elif filetype.lower() == 'fbx':
        buildImportTask = buildStaticMeshImportTask
        shouldManuallyImport = shouldManuallyImportFBX
    else:
        print(f'invalid filetype: {filetype}')
        return

    # using unreal.Array rather than [] because Unreal doesn't let you append
    # to a normal list, for some reason 
    autoTasks = unreal.Array(unreal.AssetImportTask)
    manualTasks = unreal.Array(unreal.AssetImportTask)
    for file in os.listdir(srcDir):

        print(f'Importing {srcPath} to {gameDir}')

        if shouldManuallyImport(file):
            task = buildImportTask(srcPath, gameDir, automated=False,
                                            replaceExisting=replaceExisting)
            manualTasks.append(task)
        else:
            task = buildImportTask(srcPath, gameDir, automated=True,
                                            replaceExisting=replaceExisting)
            autoTasks.append(task)

    return manualTasks, autoTasks

def batchImportAlembic(srcPath, gameDir, replaceExisting=False):
    """
    Import all ABC files from srcDir to gameDir, without bring up UI dialogs,
    making exceptions for certain files.

    Params:
        srcDir (str) : directory of the asset to import, e.g. C:/Users/foo/dev
        gameDir (str) : game directory to import into, e.g. /Game/Characters/
        replaceExisting (bool): will be passed to import settings. If true, 
                                old assets will be overwritten
    Returns:
        None
    """
    manualTasks, autoTasks = buildImportTaskList('abc', srcPath, gameDir, replaceExisting=False)

    # do the actual imports, import manual ones first
    ASSET_TOOLS.import_asset_tasks(manualTasks)
    ASSET_TOOLS.import_asset_tasks(autoTasks)

    return None


def batchImportVerbose(filetype, srcPath, gameDir, replaceExisting=False):
    """ 
    Verbose version of batchImportAlembic with a progress bar
    (see batchImportAlembic)

    Leaving as separate function because the code needs to be structured 
    differently
    """
    manualTasks, autoTasks = buildImportTaskList('abc', srcPath, gameDir, replaceExisting=False)
 
    # manual import first
    ASSET_TOOLS.import_asset_tasks(manualTasks)

    # show progress for auto imports
    total_frames = len(autoTasks) + 1
    text_label = f"(Auto) Importing {filetype} files for {character}_{anim}..."
    with unreal.ScopedSlowTask(total_frames, text_label) as slow_task:

        # Makes the dialog visible, if it isn't already
        slow_task.make_dialog(True) 

        for task in autoTasks:
            # logging purposes only
            src = task.get_editor_property('filename')
            dst = task.get_editor_property('destination_path')
            print(f'Importing {src} to {dst}')

            # cannot use the inherent batching ability of asset tools because
            # we want the progress bar to receive updates
            ASSET_TOOLS.import_asset_tasks([task])

            # Advance progress by one frame.
            slow_task.enter_progress_frame(1) 


def main():
    # example
    batchImportVerbose('abc', r'C:\Users\foo\my_project\assets\anim_caches', '/Game/Characters/Anim/')
    batchImportVerbose('fbx', r'C:\Users\foo\my_project\assets\static_mesh', '/Game/Environment/Props/', replaceExisting=True)