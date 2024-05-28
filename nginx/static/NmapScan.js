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
            var ipElement = '<span class="clickable-ip" style="cursor: pointer; text-decoration: underline;">' + scan.ip_address + '</span>';
            resultsElement.innerHTML += scan.name + ' - ' + ipElement + '<br>';
        });

        // Add click event listeners to the IP addresses
        document.querySelectorAll('.clickable-ip').forEach(function(element) {
            element.addEventListener('click', function() {
                document.getElementById('host').value = this.textContent; // Updates the host input field
            });
        });
    })
    .catch(error => {
        console.error('Error:', error);
    });
}
