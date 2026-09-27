# NEXVARY RealEstate AI OS — Native Qt Migration

This directory is the parallel native desktop migration track. It intentionally does **not** delete or replace the tested React/FastAPI v1.8 product.

## Stack

- C++20
- Qt 6
- QML / Qt Quick Controls 2
- CMake
- Qt Network
- Qt Test / CTest
- Existing Python/FastAPI backend during the migration

This mirrors the stable architectural direction used by NEXVARY Avionics Lab: native C++ core, QML shell, CMake builds, explicit RTL and back-stack behavior, and CI gates before packaging.

## Current native scope

- Arabic/English application state in C++.
- True QML RTL/LTR shell: Arabic places the navigation rail on the right.
- Native back-stack.
- Digital clock/date.
- NEXVARY dark/electric/silver visual shell.
- FastAPI health probe.
- Native login through `/api/v1/auth/login`.
- Native live dashboard through `/overview`, `/leads`, and `/units`.
- Non-migrated routes remain clearly marked as migration work; the production v1.8 UI is kept intact.

## Build

### Windows / PowerShell

```powershell
cmake -S apps/desktop-qt -B build-qt -DCMAKE_BUILD_TYPE=Release
cmake --build build-qt --config Release
ctest --test-dir build-qt -C Release --output-on-failure
.\build-qt\Release\nexvary_realestate_native.exe
```

### Linux

```bash
cmake -S apps/desktop-qt -B build-qt -DCMAKE_BUILD_TYPE=Release
cmake --build build-qt -j2
ctest --test-dir build-qt --output-on-failure
./build-qt/nexvary_realestate_native
```

Set a non-default backend with:

```powershell
$env:NEXVARY_API_URL="http://127.0.0.1:8000"
```

or:

```powershell
.\build-qt\Release\nexvary_realestate_native.exe --api-url http://127.0.0.1:8000
```

## Migration rule

A module may replace its v1.8 implementation only after native feature parity and its build/test/UI gates pass. No mass rewrite and no removal of the current tested product before parity.
