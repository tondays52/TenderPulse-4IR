@echo off
title TenderPulse 4IR - Autonomous 24/7 Ingestion Crawler
color 0B
echo =======================================================================
echo   Starting TenderPulse 4IR Autonomous Procurement Ingestion Daemon
echo   Monitoring: e-GP (eprocure.gov.bd), Newspaper OCR, Gazette Feeds
echo =======================================================================
powershell -ExecutionPolicy Bypass -NoExit -Command "& '%~dp0backend\crawler.ps1' -Loop -IntervalSeconds 15"
pause
