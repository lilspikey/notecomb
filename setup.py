from distutils.core import setup


def py2app_options(setup_args):
    try:
        import py2app
        # create py2app options
        py2app_plist = {
            'CFBundleName':               "NoteComb",
            'CFBundleShortVersionString': "0.2.0",
            'CFBundleGetInfoString':      "NoteComb 0.2.0 alpha",
            'CFBundleExecutable':         "NoteComb",
            'CFBundleIdentifier':         "com.psychicorigami.notecomb",
            'CFBundleDocumentTypes': [ { 'CFBundleTypeExtensions': ["*"], 'CFBundleTypeName': "kUTTypeText", 'CFBundleTypeRole': "Editor", "CFBundleTypeIconFile": "combdoc.icns" } ],
        }

        setup_args['options']['py2app']={
            'argv_emulation': 1,
            'iconfile': 'resources/comb.icns',
            'resources': ['resources/combdoc.icns'],
            'plist': py2app_plist,
        }

        setup_args['app']=[ 'main.py' ]
        # end py2app options
        
    except ImportError:
        pass

def py2exe_options(setup_args):
    try:
        import py2exe
        # create py2exe options
        py2exe_manifest = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
        <assembly xmlns="urn:schemas-microsoft-com:asm.v1"
        manifestVersion="1.0">
        <assemblyIdentity
            version="0.64.1.0"
            processorArchitecture="x86"
            name="Controls"
            type="win32"
        />
        <description>Observertron</description>
        <dependency>
            <dependentAssembly>
                <assemblyIdentity
                    type="win32"
                    name="Microsoft.Windows.Common-Controls"
                    version="6.0.0.0"
                    processorArchitecture="X86"
                    publicKeyToken="6595b64144ccf1df"
                    language="*"
                />
            </dependentAssembly>
        </dependency>
        </assembly>
        """

        setup_args['windows']=[{
            'script': "main.py",
            'name': "NoteComb",
            'dest_base': "NoteComb",
            'version': "0.2.0",
            "other_resources": [(24,1,py2exe_manifest)]
        }]

        setup_args['options']['py2exe']={'bundle_files': 1}
        setup_args['zipfile'] = None
        # end of py2exe options
    except ImportError:
        pass

setup_args={'options':{}}
py2app_options(setup_args)
py2exe_options(setup_args)

# now run setup
setup(**setup_args)