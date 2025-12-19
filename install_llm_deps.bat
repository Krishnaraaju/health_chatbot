@echo off
echo Installing AI Core Dependencies...
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu118
pip install transformers accelerate bitsandbytes
echo.
echo Installation Complete.
echo To enable the Medical LLM, open 'app.py' and change AI_MODE = 'SIMPLE' to AI_MODE = 'LLM'.
pause
