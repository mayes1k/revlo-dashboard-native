# REVLO Dash

REVLO Dash is a Windows desktop application that opens the REVLO dashboard (https://dash-revlo.ct.ws/) in its own window, like a normal program instead of a browser tab.

It is built with Python, PySide6 and QtWebEngine (the Chromium engine used by Qt). You do not need to know any of these to use this guide: every step below is written for someone who has never used Python.

---

## Table of contents

1. [What the app does](#what-the-app-does)
2. [What you need](#what-you-need)
3. [Step 1: Install Python](#step-1-install-python)
4. [Step 2: Install the project](#step-2-install-the-project)
5. [Step 3: Run the app to test it](#step-3-run-the-app-to-test-it)
6. [Step 4: Build the EXE](#step-4-build-the-exe)
7. [Where your data is stored](#where-your-data-is-stored)
8. [Cache and website updates](#cache-and-website-updates)
9. [Keyboard shortcuts](#keyboard-shortcuts)
10. [Customizing the app](#customizing-the-app)
11. [Troubleshooting](#troubleshooting)
12. [Project files](#project-files)
13. [Glossary](#glossary)

---

## What the app does

- Loads the REVLO dashboard in a clean window with no address bar and no browser buttons.
- Keeps you logged in: cookies, sessions and Local Storage are saved on your computer and survive closing and reopening the app.
- Never blocks pop-ups. Links that open a new window (`window.open()`, `target="_blank"`, Telegram login windows) open in their own independent window and share the same login session.
- Opens `tg://` links in Telegram Desktop if it is installed.
- Hides the scrollbars while keeping mouse wheel and touch scrolling working.
- Does not keep old versions of your website: the HTTP cache is disabled, so website updates appear as soon as you refresh. You never need to rebuild the EXE when your website changes.
- Shows a friendly error page with a Retry button if the website cannot be reached.

## What you need

- A computer running Windows 10 or Windows 11 (64-bit).
- An internet connection (for installing and for using the app).
- About 1.5 GB of free disk space during the build. The final EXE is around 150 to 250 MB.
- Python 3.9, 3.10, 3.11, 3.12 or 3.13, 64-bit. Python 3.14 is not supported yet. Version 3.12 is recommended.

## Step 1: Install Python

Skip this step if Python is already installed. To check, press the Windows key, type `cmd`, press Enter, then type:

```
python --version
```

If it prints something like `Python 3.12.x`, you are ready. If it says the command is not recognized, install Python:

1. Go to https://www.python.org/downloads/ and download Python 3.12 for Windows (64-bit installer).
2. Run the installer.
3. On the very first screen, tick the box **Add python.exe to PATH**. This is the step people most often forget.
4. Click **Install Now** and wait until it finishes.
5. Close any open Command Prompt windows, open a new one, and run `python --version` again to confirm.

## Step 2: Install the project

1. Download the project ZIP file and save it somewhere simple, for example your Desktop.
2. Right-click the ZIP file and choose **Extract All**. Avoid running the project from inside the ZIP.
3. Open the extracted `REVLO_Dash` folder.
4. Double-click **`install.bat`**.

A black window opens and shows progress. It will:

- find a compatible Python version,
- create a private environment in a folder called `.venv` (so nothing is installed globally on your PC),
- install PySide6 and PyInstaller.

This takes a few minutes and downloads several hundred megabytes. When you see "Installation terminee", press any key to close the window. You only need to do this step once.

## Step 3: Run the app to test it

Double-click **`run.bat`**. The REVLO Dash window opens and loads the website.

To test that pop-ups and scrolling work correctly, double-click **`test.bat`** instead. It opens a local test page with buttons that try different ways of opening new windows:

1. `window.open` from a click
2. A `target="_blank"` link
3. A pop-up opened by JavaScript without a click (after 2 seconds)
4. A local pop-up that talks back to the main window (this is what Telegram login relies on)
5. A Telegram web link
6. A `tg://` link (opens Telegram Desktop)

Every test should open a separate window, and the result log on the page should show lines starting with "OK". The page also contains a long area to confirm that scrolling works without visible scrollbars.

## Step 4: Build the EXE

Building (also called compiling) turns the Python project into a single program, `REVLO Dash.exe`, that runs on any Windows 10 or 11 PC without Python installed.

1. Make sure Step 2 was completed.
2. Double-click **`build.bat`**.
3. Wait. This usually takes 3 to 10 minutes and can look frozen for a while. That is normal.
4. When it finishes, a folder opens containing your program:

```
REVLO_Dash\dist\REVLO Dash.exe
```

You can copy this single file anywhere or send it to another PC. No console window appears when it starts.

Notes about the EXE:

- **First launch is slower.** The EXE is a single self-extracting file, so it unpacks itself each time it starts. Expect a few seconds before the window appears.
- **Windows SmartScreen warning.** Because the EXE is not digitally signed, Windows may show "Windows protected your PC". Click **More info**, then **Run anyway**.
- **Antivirus false alarms.** Some antivirus tools flag programs made with PyInstaller. If this happens, add an exception for the file.
- **Rebuilding.** Run `build.bat` again any time you change the code. The old `dist` and `build` folders are replaced.

## Where your data is stored

Everything the app saves is kept outside the EXE, in:

```
%LOCALAPPDATA%\REVLO Dash\
```

To open it, press the Windows key and R together, paste `%LOCALAPPDATA%\REVLO Dash` and press Enter.

| Folder | Content |
| --- | --- |
| `profile` | Cookies, login session, Local Storage |
| `cache` | Temporary files (emptied on every start) |
| `logs` | `revlo-dash.log`, useful when something goes wrong |

Because data lives here and not next to the EXE, you can replace or move the EXE without being logged out.

To log out completely and start fresh, close the app and delete the `profile` folder.

## Cache and website updates

A cache is a local copy of website files that browsers keep to load pages faster. REVLO Dash disables it on purpose so you always see the latest version of your site.

- The HTTP cache is turned off and emptied at every start.
- Service Workers (a browser feature that can keep old copies of a site) are removed at every page load and at every refresh.
- The **Refresh** button, F5, Ctrl+R and the right-click entry "Actualiser (sans cache)" force a full reload without cache.
- Cookies, login sessions and Local Storage are never deleted by any of this. The cache and your login data are separate things.

## Keyboard shortcuts

| Shortcut | Action |
| --- | --- |
| F5, Ctrl+R, Ctrl+F5, Ctrl+Shift+R | Refresh without cache |
| F11 | Toggle full screen |
| Ctrl+W | Close a pop-up window |

## Customizing the app

Open `main.py` with Notepad or any text editor. The settings are at the top of the file.

| Setting | Default | Meaning |
| --- | --- | --- |
| `APP_URL` | `https://dash-revlo.ct.ws/` | Website that the app opens |
| `APP_HOST` | `dash-revlo.ct.ws` | Domain used for the Service Worker cleanup. Change it together with `APP_URL`. |
| `WINDOW_SIZE` | `(1200, 800)` | Starting window size |
| `SHOW_REFRESH_BAR` | `True` | Set to `False` to hide the thin Refresh bar |
| `LOAD_TIMEOUT_MS` | `30000` | Time before the error page appears if the site never loads |

After changing anything, run `run.bat` to test and `build.bat` to create a new EXE.

**Changing the icon.** The icon is `assets\revlo-logo.ico`, generated from `revlo-logo.svg`. To regenerate it after editing the logo, open Command Prompt in the project folder and run:

```
.venv\Scripts\python.exe -m pip install pillow
.venv\Scripts\python.exe tools\make_icon.py
```

The logo is white on a transparent background, so the icon places it on a dark rounded square to stay visible on light taskbars. The color is set at the top of `tools\make_icon.py`.

## Troubleshooting

**"Python was not found" or install.bat says Python is missing.**
Reinstall Python and make sure **Add python.exe to PATH** is ticked (see Step 1). Use a version between 3.9 and 3.13.

**install.bat fails while downloading packages.**
Check your internet connection, disable any VPN or proxy, and run `install.bat` again. It is safe to run it as many times as needed.

**The window opens but shows only a dark blue or blank screen.**
Open the log file at `%LOCALAPPDATA%\REVLO Dash\logs\revlo-dash.log` and look for lines starting with `load:`. They say whether the site loaded or failed and why. If the screen stays blank, try disabling GPU acceleration: open Command Prompt in the project folder and run

```
set REVLO_SAFE_GRAPHICS=1
run.bat
```

**An error page says the site cannot be loaded.**
Check your internet connection, then click **Retry** or press F5. If other websites work but this one does not, the website itself may be down.

**I am logged out after restarting.**
Make sure you did not delete the `profile` folder, and that the app is closed normally (using the window close button) rather than ended from Task Manager.

**Pop-ups do not appear.**
Run `test.bat` and check which test fails, then look at the log file. Pop-ups are never intentionally blocked by the app.

**build.bat fails.**
Run `install.bat` first. Close any running `REVLO Dash.exe`, because Windows cannot overwrite a program that is open. Then run `build.bat` again.

**The EXE does nothing when double-clicked.**
Wait a few seconds, as the first start is slow. Only one copy of the app can run at once, so if it is already running, a second launch just brings the existing window to the front. Check the Task Manager for a leftover `REVLO Dash` process if nothing appears.

## Project files

```
REVLO_Dash/
  main.py            The whole application
  revlo-logo.svg     Original logo
  requirements.txt   List of Python packages to install
  install.bat        Step 2: installs everything
  run.bat            Step 3: runs the app for testing
  test.bat           Runs the pop-up and scrolling test page
  build.bat          Step 4: creates dist\REVLO Dash.exe
  README.txt         Short instructions
  README.md          This guide
  assets/
    revlo-logo.ico   Application and EXE icon
  tools/
    make_icon.py     Regenerates the icon from the SVG
```

Folders created later: `.venv` (private Python environment), `build` and `dist` (build output).
