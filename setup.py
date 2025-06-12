from setuptools import setup

APP = ['image_converter_gui.py']
DATA_FILES = []
OPTIONS = {
    'argv_emulation': True,
    'packages': ['PIL'],
    'iconfile': 'icon.icns',  # If you have a macOS icon file
    'plist': {
        'CFBundleName': "JARVIS Image Converter",
        'CFBundleDisplayName': "JARVIS Image Converter",
        'CFBundleGetInfoString': "Convert images between different formats",
        'CFBundleIdentifier': "com.jarvis.imageconverter",
        'CFBundleVersion': "1.0.0",
        'CFBundleShortVersionString': "1.0.0",
        'NSHumanReadableCopyright': "© 2025"
    }
}

setup(
    app=APP,
    data_files=DATA_FILES,
    options={'py2app': OPTIONS},
    setup_requires=['py2app'],
    name="JARVIS Image Converter"
)
