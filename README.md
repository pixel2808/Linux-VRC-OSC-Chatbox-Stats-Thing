Made this cause there was nothing like this at the time.
Go ahead and use this code for whatever but you are probably better of writing this from scratch cause this is a mess.

<img width="300" alt="Screenshot_20250714_135522" src="https://github.com/user-attachments/assets/eddd887c-38bb-412f-85f6-2befdd2dd47b" />


🔽 Download (Precompiled Binary)

Download the latest release:
➡️ [Download VRC_OSC_ChatBox_Stats_NvidiaAndAMD](https://github.com/pixel2808/Linux-VRC-OSC-Chatbox-Stats-Thing/releases/latest/download/VRC_OSC_ChatBox_Stats_NvidiaAndAMD)

Just download and run the executable. Make sure it's marked as executable:

    chmod +x VRC_OSC_ChatBox_Stats_NvidiaAndAMD
    ./VRC_OSC_ChatBox_Stats_NvidiaAndAMD

⚙️ Run From Source

Create and activate a virtual environment:

For Bash/Zsh:

    python3 -m venv oscenv
    source oscenv/bin/activate

For Fish shell:

    python3 -m venv oscenv
    source oscenv/bin/activate.fish

Install dependencies:

    pip install -r requirements.txt

Run the script:

    python VRC_OSC_ChatBox_Stats_NvidiaAndAMD.py

📦 Build a Standalone Executable

Make sure you're in the virtual environment first (source oscenv/...), then run:

    pyinstaller --onefile --add-data "Icon.png:." VRC_OSC_ChatBox_Stats_NvidiaAndAMD.py

The resulting binary will be in the dist/ directory.

--add-data includes the icon in the executable (you can update "Icon.png:. " to your actual icon path if needed).
