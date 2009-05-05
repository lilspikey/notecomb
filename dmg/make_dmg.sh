#!/bin/sh
bunzip2 -k template.dmg.bz2
hdiutil attach template.dmg -mountpoint ./dmg_dir
ditto -rsrc ../dist/NoteComb.app dmg_dir/NoteComb.app
hdiutil detach ./dmg_dir
hdiutil convert -format UDBZ -o NoteComb.dmg template.dmg
rm template.dmg