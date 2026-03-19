# Oxia: The Metabolic Digital Twin - Windows Launcher
# Run: .\run.ps1

Write-Host "Starting Oxia: The Metabolic Digital Twin..." -ForegroundColor Cyan

if (-not (Test-Path ".venv")) {
    Write-Host "Error: Virtual environment not found. Run: python -m venv .venv; .\.venv\Scripts\Activate.ps1; pip install -r requirements.txt" -ForegroundColor Red
    exit 1
}

# Start backend in new window
Write-Host "Starting FastAPI backend on port 8000..." -ForegroundColor Green
$backend = Start-Process -FilePath ".\.venv\Scripts\python.exe" -ArgumentList "-m", "uvicorn", "backend:app", "--port", "8000" -PassThru -WindowStyle Normal

Start-Sleep -Seconds 2

# Start frontend in new window  
Write-Host "Starting Streamlit frontend on port 8501..." -ForegroundColor Green
$frontend = Start-Process -FilePath ".\.venv\Scripts\streamlit.exe" -ArgumentList "run", "app.py", "--server.port", "8501" -PassThru -WindowStyle Normal

Write-Host "`nBoth servers are running!" -ForegroundColor Green
Write-Host "  Backend:  http://localhost:8000" -ForegroundColor White
Write-Host "  Frontend: http://localhost:8501" -ForegroundColor White
Write-Host "`nOpen http://localhost:8501 in your browser." -ForegroundColor Yellow
Write-Host "Press Enter to stop servers..." -ForegroundColor Gray
Read-Host

Stop-Process -Id $backend.Id -Force -ErrorAction SilentlyContinue
Stop-Process -Id $frontend.Id -Force -ErrorAction SilentlyContinue
Write-Host "Servers stopped." -ForegroundColor Cyan
