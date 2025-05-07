        function checkSelectedProductTables() {
            const selectedLinks = [];
            const linkCheckboxes = document.querySelectorAll('#links-results .product-table-checkbox:checked');
            
            // Get the timeout setting
            const timeout = document.getElementById('selected-timeout').value;
            
            // Get all selected URLs
            linkCheckboxes.forEach(checkbox => {
                if (checkbox.checked) {
                    selectedLinks.push(checkbox.getAttribute('data-url'));
                }
            });
            
            if (selectedLinks.length === 0) {
                alert('Please select at least one link to check');
                return;
            }
            
            // Show loading state
            const checkButton = document.getElementById('check-product-tables-btn');
            checkButton.disabled = true;
            checkButton.textContent = 'Checking...';
            
            // Update status of selected checkboxes to indicate loading
            linkCheckboxes.forEach(checkbox => {
                const statusSpan = checkbox.closest('div').querySelector('.product-table-status');
                if (statusSpan) {
                    statusSpan.textContent = 'Checking...';
                    statusSpan.style.color = '#3182ce'; // Blue for loading state
                }
            });
            
            // Make API request
            fetch('/api/check-product-tables', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'Accept': 'application/json'
                },
                body: JSON.stringify({
                    urls: selectedLinks,
                    timeout: parseInt(timeout)
                })
            })
            .then(response => {
                if (!response.ok) {
                    throw new Error('Network response was not ok');
                }
                return response.json();
            })
            .then(data => {
                // Update UI with results
                if (data.results) {
                    Object.entries(data.results).forEach(([url, result]) => {
                        // Find all checkboxes with this URL
                        const checkboxes = document.querySelectorAll(`#links-results .product-table-checkbox[data-url="${url}"]`);
                        
                        checkboxes.forEach(checkbox => {
                            const container = checkbox.closest('div');
                            const statusContainer = container.querySelector('.product-table-status-container');
                            const statusSpan = statusContainer.querySelector('.product-table-status');
                            
                            // Remove any existing additional elements
                            while (statusContainer.childNodes.length > 1) {
                                statusContainer.removeChild(statusContainer.lastChild);
                            }
                            
                            // Update row styling
                            const row = checkbox.closest('tr');
                            
                            // Process the result
                            if (result.found === true) {
                                statusSpan.textContent = 'Yes';
                                statusSpan.style.color = '#38a169'; // Green
                                
                                if (row) {
                                    row.style.backgroundColor = '#f0fff4'; // Light green background
                                }
                                
                                // Add class name if available
                                if (result.class_name) {
                                    const classSpan = document.createElement('span');
                                    classSpan.style.fontSize = '0.9em';
                                    classSpan.style.display = 'block';
                                    classSpan.style.color = '#718096'; // Gray
                                    classSpan.textContent = `Class: ${result.class_name}`;
                                    statusContainer.appendChild(classSpan);
                                }
                            } else {
                                statusSpan.textContent = 'No';
                                statusSpan.style.color = '#4a5568'; // Gray
                                
                                // Add error if available
                                if (result.error) {
                                    const errorDiv = document.createElement('div');
                                    errorDiv.style.fontSize = '12px';
                                    errorDiv.style.marginTop = '4px';
                                    errorDiv.style.color = '#e53e3e'; // Red
                                    errorDiv.textContent = `Error: ${result.error}`;
                                    statusContainer.appendChild(errorDiv);
                                }
                                
                                // Add detection method if available
                                if (result.detection_method) {
                                    const methodSpan = document.createElement('span');
                                    methodSpan.style.fontSize = '0.9em';
                                    methodSpan.style.display = 'block';
                                    methodSpan.style.color = '#718096'; // Gray
                                    methodSpan.textContent = `Method: ${result.detection_method}`;
                                    statusContainer.appendChild(methodSpan);
                                }
                            }
                        });
                    });
                }
                
                // Restore button state
                checkButton.disabled = false;
                checkButton.textContent = 'Check Selected Links';
            })
            .catch(error => {
                console.error('Error checking product tables:', error);
                alert('Error checking product tables: ' + error.message);
                
                // Reset status for checkboxes that were being checked
                linkCheckboxes.forEach(checkbox => {
                    const statusSpan = checkbox.closest('div').querySelector('.product-table-status');
                    if (statusSpan) {
                        statusSpan.textContent = 'Check failed';
                        statusSpan.style.color = '#e53e3e'; // Red for error
                    }
                });
                
                // Restore button state
                checkButton.disabled = false;
                checkButton.textContent = 'Check Selected Links';
            });
        }
