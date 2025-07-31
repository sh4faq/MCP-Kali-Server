# Docker + Pytest Tests - Simple Setup

## Quick Start

### Run everything in one command:
```batch
run_all.bat
```

### Or run step by step:

1. **Start Docker container:**
```batch
cd docker
start.bat
```

2. **Run tests:**
```batch
cd ..
python -m pytest kali\test_ssh_manager.py -v
```

3. **Stop Docker:**
```batch
docker stop kali-test-ssh
docker rm kali-test-ssh
```

## What it does

- Starts Ubuntu container with SSH server
- Maps port 2222 → 22 (SSH)
- Creates test users: `testuser:testpass` and `root:rootpass`
- Runs SSH Manager tests with pytest
- Cleans up automatically

## Files

- `run_all.bat` - Complete automation (start Docker + run tests + cleanup)
- `docker/start.bat` - Just start Docker container
- `docker/Dockerfile` - Container configuration
- `kali/test_ssh_manager.py` - SSH tests

That's it. Simple and clean.
