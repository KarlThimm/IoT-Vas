async function runNetworkScan() {
    fetch('/api/scan_network', {
        method: 'POST',
        headers: {
            'Cache-Control': 'no-cache, no-store, must-revalidate',
            'Pragma': 'no-cache',
            'Expires': '0'
        }
    })
    .then(response => response.json())
    .then(data => {
        console.log(data); 
        var resultsElement = document.getElementById('scan-results');
        resultsElement.innerHTML = '';
        data.forEach(function(scan) {
            resultsElement.innerHTML += scan.name + ' - ' + scan.ip_address + '<br>';
        });
    })
    .catch(error => {
        console.error('Error:', error);
    });
}
