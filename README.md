## Blender Plugin for the SheepIt! Renderfarm
### Installation
1. Download this plugin under [releases](https://github.com/maximmaxim345/sheepit-plugin/releases)
2. Install the zip in Blender under Edit > preferences > Install
### Usage
1. Login under Render > SheepIt! in the Properties Editor
2. Change all settings as desired
3. Press Send to SheepIt!
    * The blend file will be saved in a temporary directory
    * On this copy folowing operations will be done:
    * All external Librarys will be appended
    * All textures will be packed
    * The blend file will be compressed
### Notes
* This addon should work on Windows, MacOS and Linux (Testers needed)
* Fluid simulation are not supported
### Planned features
* Cancel button for an ongoing upload
---
### Links
* [SheepIt!](https://www.sheepit-renderfarm.com/)
* [Blender](https://www.blender.org/)
* The used [Requests Toolbelt](https://github.com/requests/toolbelt) library
