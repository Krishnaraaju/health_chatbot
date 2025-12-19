@echo off
echo Installing CPU-Optimized AI Engine...
pip install ctransformers[cuda]
echo.
echo NOTE: If you have no GPU, ignore the CUDA warnings. It works on CPU too.
echo.
echo Installation Complete.
pause
