CORDHISK App v3.0.5 for macOS

Installation
------------
1. Extract this complete CORDHISK_App_v3_MacOS folder.
2. Keep CORDHISK-App-v3.0.app inside this folder.
3. The public package starts with an empty memory_files folder.
4. To use existing data, copy your private memory_files folder beside the app, but do not place it inside Contents or MacOS.

First launch after downloading
------------------------------
macOS may quarantine applications downloaded from the internet. If the app says it is damaged, open Terminal and run:

xattr -dr com.apple.quarantine "/path/to/CORDHISK_App_v3_MacOS"

Replace /path/to with the actual location of this folder. Alternatively, Control-click the app, choose Open, and confirm Open.

The app stores logs and writable data outside the signed app bundle at:

~/Library/Application Support/CORDHISK/

Do not add or modify files inside CORDHISK-App-v3.0.app after downloading, because changing the signed bundle can make macOS report that it is damaged.

Requirements
------------
This build targets Apple Silicon (arm64) Macs. A separate Intel build is required for x86_64 Macs.
