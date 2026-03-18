# Windows File Sync Commands
## Copy files/folders from your Windows machine into the Kiro workspace

The Kiro workspace path is:
```
/Users/pratiksha/Documents/Project/Opensearch_search_functionality/opensearch-search-functionality
```

On Windows, this path is accessed via WSL or the Kiro terminal.
Use the commands below in **Windows Command Prompt (cmd)** or **PowerShell**.

---

## View files and folders

```cmd
:: List files in current folder
dir

:: List files in a specific folder
dir C:\Users\YourName\Documents\my-project

:: List all files including subfolders
dir /s C:\Users\YourName\Documents\my-project

:: Show folder tree structure
tree C:\Users\YourName\Documents\my-project

:: Show folder tree with files
tree /f C:\Users\YourName\Documents\my-project
```

---

## Navigate folders

```cmd
:: Go into a folder
cd C:\Users\YourName\Documents\my-project

:: Go up one level
cd ..

:: Go to root of drive
cd \

:: Show current folder path
cd
```

---

## Copy a single file to workspace

```cmd
:: Copy one file
copy C:\Users\YourName\Documents\index.py "\\wsl$\Ubuntu\Users\pratiksha\Documents\Project\Opensearch_search_functionality\opensearch-search-functionality\src\indexer\index.py"
```

---

## Copy an entire folder to workspace

```cmd
:: Copy folder and all contents (xcopy)
xcopy /E /I /Y C:\Users\YourName\Documents\my-project\src "\\wsl$\Ubuntu\Users\pratiksha\Documents\Project\Opensearch_search_functionality\opensearch-search-functionality\src"

:: /E = copy subfolders including empty ones
:: /I = treat destination as folder
:: /Y = overwrite without asking
```

---

## Copy using PowerShell (recommended — more reliable)

```powershell
# Copy a single file
Copy-Item -Path "C:\Users\YourName\Documents\index.py" `
          -Destination "\\wsl$\Ubuntu\Users\pratiksha\Documents\Project\Opensearch_search_functionality\opensearch-search-functionality\src\indexer\index.py" `
          -Force

# Copy entire folder recursively
Copy-Item -Path "C:\Users\YourName\Documents\my-project\src" `
          -Destination "\\wsl$\Ubuntu\Users\pratiksha\Documents\Project\Opensearch_search_functionality\opensearch-search-functionality\src" `
          -Recurse -Force

# Copy everything inside a folder into workspace root
Copy-Item -Path "C:\Users\YourName\Documents\my-project\*" `
          -Destination "\\wsl$\Ubuntu\Users\pratiksha\Documents\Project\Opensearch_search_functionality\opensearch-search-functionality\" `
          -Recurse -Force
```

---

## Check what is different between local and workspace folder

```powershell
# Compare two folders and show differences
$local = "C:\Users\YourName\Documents\my-project"
$workspace = "\\wsl$\Ubuntu\Users\pratiksha\Documents\Project\Opensearch_search_functionality\opensearch-search-functionality"

Compare-Object `
  (Get-ChildItem $local -Recurse | Select-Object -ExpandProperty FullName) `
  (Get-ChildItem $workspace -Recurse | Select-Object -ExpandProperty FullName)
```

---

## Open the workspace folder in Windows Explorer

```cmd
:: Open workspace folder in File Explorer (if using WSL)
explorer.exe \\wsl$\Ubuntu\Users\pratiksha\Documents\Project\Opensearch_search_functionality\opensearch-search-functionality
```

---

## Notes

- Replace `YourName` with your actual Windows username
- Replace `Ubuntu` with your actual WSL distro name (check with `wsl -l` in cmd)
- If Kiro is running natively on Windows (not WSL), replace the `\\wsl$\...` path with the actual Windows path where Kiro opened the workspace
- To find your WSL distro name run this in cmd: `wsl -l -v`
