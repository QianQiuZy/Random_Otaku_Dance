@echo off
chcp 65001 > nul
setlocal enabledelayedexpansion

REM 获取当前脚本所在的目录
set "script_dir=%~dp0"

REM 检查ffmpeg文件夹是否存在
if exist "%script_dir%ffmpeg" (
    REM 将ffmpeg文件夹路径添加到系统PATH中
    set "new_path=%script_dir%ffmpeg;!PATH!"

    REM 使用PowerShell提升权限
    PowerShell.exe -Command "Start-Process cmd -Verb RunAs -ArgumentList '/c setx PATH \""!new_path!\"" /M'"

    echo ffmpeg文件夹已成功添加到系统PATH中。
) else (
    echo 未找到ffmpeg文件夹，请确保脚本与ffmpeg文件夹在同一目录下。
)

endlocal

pause
