#!/bin/bash
# Start services script for test container

echo "Starting SSH daemon..."
service ssh start

# Create additional test files
mkdir -p /tmp/test_files
echo "Test SSH connection file" > /tmp/test_files/ssh_test.txt
echo "$(date): Container started" > /tmp/test_files/startup.log

# Create some sample files for testing
echo "Small test file content" > /tmp/test_files/small.txt
dd if=/dev/zero of=/tmp/test_files/large.txt bs=1024 count=1024 2>/dev/null
echo "Binary test file" > /tmp/test_files/binary.dat

# Set proper permissions
chmod 644 /tmp/test_files/*

echo "Test container services started successfully"
echo "SSH is available on port 22"
echo "Test files created in /tmp/test_files/"

# Keep container running
tail -f /dev/null
