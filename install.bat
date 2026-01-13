@echo off
echo [INFO] Starting environment setup...
echo [INFO] Installing dependencies from Tsinghua Mirror...
pip install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple
echo.
echo [SUCCESS] Environment installed successfully!
echo You can now click 'Run.bat' to start the system.
pause