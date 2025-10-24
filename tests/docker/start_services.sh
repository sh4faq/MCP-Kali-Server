#!/bin/bash
# Start services script for test container

echo "Starting SSH daemon..."
service ssh start

echo "Starting Apache web server on port 8080..."
# Configure Apache to listen on port 8080
echo "Listen 8080" >> /etc/apache2/ports.conf
sed -i 's/:80>/:8080>/g' /etc/apache2/sites-available/000-default.conf
service apache2 start

echo "Enabling PHP module for Apache..."
a2enmod php*
service apache2 reload

# Verify PHP is working
echo "<?php phpinfo(); ?>" > /var/www/html/phpinfo.php

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

# Create vulnerable web application directory
echo "Creating vulnerable web application..."
mkdir -p /var/www/html/vulnerable

# Create vulnerable exec.php file
cat > /var/www/html/vulnerable/exec.php << 'EOF'
<?php
// Simple vulnerable command execution script for testing
$cmd = $_GET['cmd'] ?? $_POST['cmd'] ?? '';
if (!empty($cmd)) {
    echo "<pre>";
    echo "Executing: " . htmlspecialchars($cmd) . "\n";
    echo "Output:\n";
    system($cmd);
    echo "</pre>";
} else {
    echo "<p>Vulnerable command execution endpoint</p>";
    echo "<p>Usage: ?cmd=your_command</p>";
}
?>
EOF

# Create vulnerable post_exec.php file
cat > /var/www/html/vulnerable/post_exec.php << 'EOF'
<?php
// POST-based vulnerable command execution
if ($_SERVER['REQUEST_METHOD'] === 'POST') {
    $cmd = $_POST['cmd'] ?? '';
    if (!empty($cmd)) {
        echo "<pre>";
        echo "Executing: " . htmlspecialchars($cmd) . "\n";
        echo "Output:\n";
        system($cmd);
        echo "</pre>";
    } else {
        echo "No command provided";
    }
} else {
    echo "Send POST request with 'cmd' parameter";
}
?>
EOF

# Ensure vulnerable web app is accessible
chown -R www-data:www-data /var/www/html/vulnerable
chmod 755 /var/www/html/vulnerable
chmod 644 /var/www/html/vulnerable/*.php

echo "Test container services started successfully"
echo "SSH is available on port 22"
echo "Apache web server is available on port 8080"
echo "Vulnerable PHP app is available at /vulnerable/"
echo "Test files created in /tmp/test_files/"

# Test PHP functionality
echo "Testing PHP functionality..."

# Create phpinfo.php for testing
echo "Creating phpinfo.php for testing..."
cat > /var/www/html/phpinfo.php << 'EOF'
<?php
phpinfo();
?>
EOF

chmod 644 /var/www/html/phpinfo.php
chown www-data:www-data /var/www/html/phpinfo.php

if curl -s http://localhost:8080/phpinfo.php | grep -q "PHP Version"; then
    echo "✅ PHP is working correctly"
else
    echo "❌ PHP is not working correctly"
fi

# Test vulnerable app
echo "Testing vulnerable PHP app..."
if [ -f /var/www/html/vulnerable/exec.php ]; then
    echo "✅ Vulnerable exec.php is available"
else
    echo "❌ Vulnerable exec.php is missing"
fi

if [ -f /var/www/html/vulnerable/post_exec.php ]; then
    echo "✅ Vulnerable post_exec.php is available"
else
    echo "❌ Vulnerable post_exec.php is missing"
fi

# Create a test endpoint to verify reverse shell connectivity
echo "Creating reverse shell test endpoint..."
cat > /var/www/html/test_reverse_shell.php << 'EOF'
<?php
header('Content-Type: application/json');

if ($_SERVER['REQUEST_METHOD'] !== 'POST') {
    http_response_code(405);
    echo json_encode(['error' => 'Method not allowed']);
    exit;
}

$input = json_decode(file_get_contents('php://input'), true);
$command = $input['command'] ?? '';

if (empty($command)) {
    http_response_code(400);
    echo json_encode(['error' => 'Command parameter required']);
    exit;
}

// Execute command and capture output
$output = shell_exec($command . ' 2>&1');
$exit_code = 0;

echo json_encode([
    'success' => true,
    'command' => $command,
    'output' => $output,
    'exit_code' => $exit_code,
    'timestamp' => date('Y-m-d H:i:s')
]);
?>
EOF

chmod 644 /var/www/html/test_reverse_shell.php
chown www-data:www-data /var/www/html/test_reverse_shell.php
echo "✅ Reverse shell test endpoint created at /test_reverse_shell.php"

# Keep container running
tail -f /dev/null
