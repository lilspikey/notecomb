from distutils.core import setup

def setup_py2app():
    import py2app
    
    plist = {
        'CFBundleName':               "Observertron",
        'CFBundleShortVersionString': "0.2.0",
        'CFBundleGetInfoString':      "Observertron 0.2.0 alpha",
        'CFBundleExecutable':         "Observertron",
        'CFBundleIdentifier':         "com.psychicorigami.observertron",
        'CFBundleDocumentTypes': [ { 'CFBundleTypeExtensions': ["*"], 'CFBundleTypeName': "kUTTypeText", 'CFBundleTypeRole': "Editor" } ],
    }
    
    # Build the .app file
    setup(
        options=dict(
            py2app=dict(
                argv_emulation=1,
                #iconfile='resources/myapp-icon.icns',
                #packages='wx',
                #site_packages=True,
                plist=plist
            ),
        ),
        app=[ 'main.py' ]
    )


def setup_py2exe():
    import py2exe
    setup(
        windows=[dict(
            script="main.py",
            name="Observertron",
            dest_base="Observertron",
            version="0.2.0")],
        options = {'py2exe': {'bundle_files': 1}},
        zipfile = None,
    )

for fn in [setup_py2app, setup_py2exe]:
    try:
        fn()
    except ImportError:
        pass