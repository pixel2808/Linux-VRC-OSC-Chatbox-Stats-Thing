Made this cause there was nothing like this at the time.
Go ahead and use this code for whatever but you are probably better of writing this from scratch cause this is a mess.

DownloadLatest:https://github.com/pixel2808/Linux-VRC-OSC-Chatbox-Stats-Thing/releases/download/tes/VRC_OSC_ChatBox_Stats_NvidiaAndAMD

From Source:

python -m venv oscenv

source oscenv/bin/activate.fish or source oscenv/bin/activate

pip install -r requirements.txt

pyinstaller --onefile --add-data "Icon.png:." VRC_OSC_ChatBox_Stats_NvidiaAndAMD.py
