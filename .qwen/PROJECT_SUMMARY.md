The user wants a comprehensive markdown summary of the project based on our conversation history.
I need to analyze the entire context provided and extract:
1. Overall Goal
2. Key Knowledge
3. Recent Actions
4. Current Plan

Let's review the conversation history:
- **Initial State**: A PyQt6-based HR data processing tool (payroll/tax conversion) was being worked on.
- **Key Features Implemented**:
    - Unified "Tax Merge" page (Payroll mandatory, Social Security optional).
    - Automatic update checking (Gitee/GitHub).
    - Fluent Design UI using `PyQt6-Fluent-Widgets`.
    - Settings and History pages.
    - Database migration to user data directory to avoid permission issues in Program Files.
- **Issues Encountered & Fixed**:
    - Crash on startup due to import errors (fixed).
    - Crash on "Generate" button click on macOS (fixed by changing default output dir from Desktop to Documents and using standard `QProgressBar` instead of Fluent's).
    - Update checker API 404 errors (fixed by using correct Gitee/GitHub API URLs and fallback logic).
    - Windows build automation via GitHub Actions.
    - Windows installer creation using Inno Setup.
    - Version management and Release management on Gitee and GitHub.
    - Large file in git history causing push timeouts (cleaned up).
    - Added global exception hook (`sys.excepthook`) to prevent silent crashes and generate crash logs on Desktop (`HR_Tools_Crash_Debug.txt`).

**Structure the summary**:

# Project Summary

## Overall Goal
Develop, maintain, and package a cross-platform HR data processing desktop tool that converts payroll and social security data into tax declaration forms, featuring a modern Fluent Design UI and automatic update capabilities.

## Key Knowledge
- **Tech Stack**: Python 3.10+, PyQt6, PyQt6-Fluent-Widgets, pandas, openpyxl.
- **Architecture**: 
    - Entry: `main.py`
    - UI: `ui/main_window.py` (FluentWindow), `ui/tools/tax_merge_page.py`, etc.
    - Logic: `core/` (loaders, mappers, generators).
    - Update System: `core/updater.py`, `core/version.py`.
- **Critical Paths**:
    - macOS Output: Default changed to `~/Documents/HR工具输出` to avoid Desktop permission crashes.
    - Windows Installer: Automated via GitHub Actions (`build-windows.yml`) using PyInstaller + Inno Setup.
    - Update Checking: Uses API URLs `https://gitee.com/api/v5/repos/shibo8817/xinfud-tools/releases?per_page=1` and `https://api.github.com/repos/Bob1817/xinfudTools/releases?per_page=1`.
- **Debugging**: Global exception hook in `main.py` creates `HR_Tools_Crash_Debug.txt` on the Desktop upon fatal errors.

## Recent Actions
- **v1.0.9 Release**: Released to enhance crash diagnostics and fix hidden dependency issues in Windows builds.
- **Crash Diagnostics**: Added `sys.excepthook` in `main.py` to catch unhandled exceptions and save detailed stack traces to the Desktop.
- **Windows Build Optimization**: Updated `build-windows.yml` to include hidden imports (`pytz`, `dateutil`, `lxml`, `numpy`) to prevent silent crashes related to pandas data manipulation.
- **Git Maintenance**: Cleaned up large binary files from git history to resolve push timeouts and synchronized tags/releases to both Gitee and GitHub.

## Current Plan
- **[DONE]** Implement global crash reporting mechanism.
- **[DONE]** Configure automated Windows build pipeline with PyInstaller and Inno Setup.
- **[IN PROGRESS]** Monitoring v1.0.9 Windows build via GitHub Actions.
- **[TODO]** Analyze `HR_Tools_Crash_Debug.txt` from Windows testing environment to identify and fix the specific "Tax Declaration" generation crash.
- **[TODO]** Create Gitee Release for v1.0.9 to enable update detection for domestic users.# Project Summary

## Overall Goal
Develop, maintain, and package a cross-platform HR data processing desktop tool (HR数据处理工具集) that converts payroll and social security data into tax declaration forms, featuring a modern Fluent Design UI, automatic update capabilities, and robust error reporting.

## Key Knowledge
- **Tech Stack**: Python 3.10+, PyQt6, PyQt6-Fluent-Widgets, pandas, openpyxl.
- **Architecture**: 
    - **Entry**: `main.py` (includes global exception hook).
    - **UI**: `ui/main_window.py` (FluentWindow), `ui/tools/tax_merge_page.py`, `ui/settings_page.py`.
    - **Logic**: `core/` (data_loader, mappers, report_generator).
    - **Updates**: `core/updater.py`, `core/version.py`.
- **Critical Paths & Fixes**:
    - **macOS Output**: Default output path changed to `~/Documents/HR工具输出` to avoid Desktop permission crashes.
    - **Windows Installer**: Automated via GitHub Actions (`build-windows.yml`) using PyInstaller + Inno Setup. 
    - **Update Checking**: Uses API URLs `https://gitee.com/api/v5/repos/shibo8817/xinfud-tools/releases?per_page=1` and `https://api.github.com/repos/Bob1817/xinfudTools/releases?per_page=1`.
    - **Hidden Imports**: Added `pytz`, `dateutil`, `lxml`, `numpy` to PyInstaller config to prevent pandas-related crashes.
- **Debugging Protocol**: 
    - Global exception hook (`sys.excepthook`) captures crashes and writes a detailed report to `HR_Tools_Crash_Debug.txt` on the user's Desktop.
    - Background worker logs step-by-step execution to the same file.

## Recent Actions
- **v1.0.9 Release**: Released to enhance crash diagnostics and fix hidden dependency issues in Windows builds.
- **Crash Diagnostics**: Added `sys.excepthook` in `main.py` to catch unhandled exceptions and save detailed stack traces to the Desktop.
- **Windows Build Optimization**: Updated `build-windows.yml` to include hidden imports (`pytz`, `dateutil`, `lxml`, `numpy`) to prevent silent crashes related to pandas data manipulation.
- **Git Maintenance**: Cleaned up large binary files from git history to resolve push timeouts and synchronized tags/releases to both Gitee and GitHub.

## Current Plan
- [DONE] Implement global crash reporting mechanism and debug logging.
- [DONE] Configure automated Windows build pipeline with PyInstaller and Inno Setup.
- [IN PROGRESS] Monitoring v1.0.9 Windows build via GitHub Actions.
- [TODO] Analyze `HR_Tools_Crash_Debug.txt` from Windows testing environment to identify the specific cause of the "Tax Declaration" generation crash.
- [TODO] Create Gitee Release for v1.0.9 to enable update detection for domestic users.

---

## Summary Metadata
**Update time**: 2026-04-10T08:18:05.048Z 
