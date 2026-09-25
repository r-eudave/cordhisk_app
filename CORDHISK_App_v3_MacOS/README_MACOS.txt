CORDHISK App v3.0.5 for macOS

Installation
------------
1. Extract this complete CORDHISK_App_v3_MacOS folder.
2. Keep CORDHISK-App-v3.0.app inside this folder.
3. The public package starts with an empty memory_files folder.
4. To use existing data, copy your private memory_files folder beside the app, but do not place it inside Contents or MacOS.

First launch after downloading
------------------------------
After extracting the ZIP into Downloads, put your private memory_files folder beside the app:

Downloads/CORDHISK_App_v3_MacOS/
	CORDHISK-App-v3.0.app/
	memory_files/000_cordhisk.db

Open Terminal and paste these commands exactly:

APP_DIR="$HOME/Downloads/CORDHISK_App_v3_MacOS"
pkill -f 'CORDHISK-App-v3.0|cordhisk.py|launcher.py' 2>/dev/null || true
rm -rf "$HOME/Library/Application Support/CORDHISK"
xattr -dr com.apple.quarantine "$APP_DIR"
open -n "$APP_DIR/CORDHISK-App-v3.0.app"

If the folder is on the Desktop, replace `Downloads` with `Desktop` in `APP_DIR`.

The `rm -rf` command removes only CORDHISK's fallback data. Back it up first if it contains data you need.

If the app says it is damaged, the usual cause is quarantine or launching an older copy. Confirm that the app is being launched from `APP_DIR`, not from AppTranslocation or another old copy.

Alternatively, Control-click the app, choose Open, and confirm Open.

The app stores logs and writable data outside the signed app bundle at:

~/Library/Application Support/CORDHISK/

Do not add or modify files inside CORDHISK-App-v3.0.app after downloading, because changing the signed bundle can make macOS report that it is damaged.

Requirements
------------
This build targets Apple Silicon (arm64) Macs. A separate Intel build is required for x86_64 Macs.
