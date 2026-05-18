// Clean CSV Download Function for Data Reports Page
function downloadCSV() {
    console.log('Downloading CSV...');
    
    if (!window.analyticsData || window.analyticsData.length === 0) {
        alert('No data available. Please load data first using the "Load Data" button above.');
        return;
    }
    
    // Generate CSV content with proper headers
    let csvContent = 'DateTime,"Air Temp (°C)","Humidity (%)","Rainfall (mm)","Water Temp (°C)","Dissolved O₂ (mg/L)","pH Level"\n';
    
    window.analyticsData.forEach(r => {
        csvContent += `"${r.datetime}",${r.air_temp},${r.humidity},${r.rain},${r.water_temp},${r.do},${r.ph}\n`;
    });
    
    // Generate filename with date range
    const fromDate = document.getElementById('analyticsFromDate')?.value || 'data';
    const toDate = document.getElementById('analyticsToDate')?.value || new Date().toISOString().split('T')[0];
    const filename = `aquamonitor_data_${fromDate}_to_${toDate}.csv`;
    
    try {
        // Create and trigger download
        const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' });
        const link = document.createElement('a');
        const url = URL.createObjectURL(blob);
        link.setAttribute('href', url);
        link.setAttribute('download', filename);
        link.style.visibility = 'hidden';
        document.body.appendChild(link);
        link.click();
        document.body.removeChild(link);
        URL.revokeObjectURL(url);
        
        console.log('CSV download completed:', filename);
        
        // Show success feedback
        const downloadBtn = document.getElementById('downloadBtn');
        if (downloadBtn) {
            const originalText = downloadBtn.textContent;
            downloadBtn.textContent = 'Downloaded!';
            downloadBtn.style.background = '#22c55e';
            setTimeout(() => {
                downloadBtn.textContent = originalText;
                downloadBtn.style.background = '';
            }, 2000);
        }
        
    } catch (error) {
        console.error('CSV download error:', error);
        alert('Failed to download CSV file. Please try again.');
    }
}

// Initialize download functionality when page loads
if (window.location.href.includes('data-reports')) {
    window.addEventListener('load', () => {
        const downloadBtn = document.getElementById('downloadBtn');
        if (downloadBtn) {
            downloadBtn.onclick = downloadCSV;
        }
    });
}