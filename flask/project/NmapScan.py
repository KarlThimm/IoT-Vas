from flask import Flask, jsonify, Blueprint
import subprocess

scan = Blueprint('scan', __name__)

@scan.route('/api/scan_network', methods=['POST'])
def scan_network():
    command = "nmap -sn 192.168.1.0/24"
    process = subprocess.Popen(command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    stdout, stderr = process.communicate()
    scan_results = []
    for line in stdout.decode().split('\n'):
        if 'Nmap scan report for' in line:
            parts = line.split()
            if '(' in line and ')' in line:
                name = parts[4]
                ip_address = parts[5].strip('()')
                scan_results.append({'name': name, 'ip_address': ip_address})

    return jsonify(scan_results)

if __name__ == '__main__':
    scan.run(debug=True)