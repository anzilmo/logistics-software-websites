// Simulate PDF loading
        document.addEventListener('DOMContentLoaded', function() {
            setTimeout(() => {
                document.getElementById('pdfLoading').style.display = 'none';
                const pdfFrame = document.getElementById('pdfFrame');
                pdfFrame.style.display = 'block';
                // In a real application, you would set the PDF URL here
                // pdfFrame.src = "{{ purchase.pdf.url }}";
                
                // For demo purposes, we'll show a sample message
                pdfFrame.contentDocument.write(`
                    <!DOCTYPE html>
                    <html>
                    <head>
                        <title>Invoice Preview</title>
                        <style>
                            body { 
                                font-family: Arial, sans-serif; 
                                padding: 40px;
                                display: flex;
                                justify-content: center;
                                align-items: center;
                                height: 100%;
                                background: #f9fafc;
                            }
                            .invoice-placeholder {
                                text-align: center;
                                color: #4a6491;
                            }
                            .invoice-placeholder i {
                                font-size: 48px;
                                margin-bottom: 20px;
                                color: #ccd1d9;
                            }
                        </style>
                    </head>
                    <body>
                        <div class="invoice-placeholder">
                            <i class="fas fa-file-pdf"></i>
                            <h2>Invoice Preview</h2>
                            <p>Invoice: INV-2023-0876</p>
                            <p>Supplier: Global Supplies Inc.</p>
                            <p>Amount: $1,245.75</p>
                            <p>In a real application, the actual PDF would be displayed here.</p>
                        </div>
                    </body>
                    </html>
                `);
                pdfFrame.contentDocument.close();
            }, 2000);
        });
        
        // Print PDF function
        function printPdf() {
            const pdfFrame = document.getElementById('pdfFrame');
            if (!pdfFrame || pdfFrame.style.display === 'none') {
                alert('PDF is not loaded yet. Please wait.');
                return;
            }
            
            try {
                pdfFrame.contentWindow.print();
            } catch (e) {
                alert('Error printing PDF: ' + e.message);
            }
        }
        
        // Share purchase info
        function sharePurchase() {
            const notification = document.getElementById('notification');
            notification.classList.add('show');
            
            // Copy purchase details to clipboard
            const purchaseDetails = `
                Purchase Invoice: INV-2023-0876
                Supplier: Global Supplies Inc.
                Date: October 15, 2023
                Amount: $1,245.75
            `;
            
            // In a real app, we would use the Clipboard API
            // navigator.clipboard.writeText(purchaseDetails)
            
            setTimeout(() => {
                notification.classList.remove('show');
            }, 3000);
        }
        
        // Archive purchase
        function archivePurchase() {
            if (confirm('Are you sure you want to archive this purchase?')) {
                alert('Purchase archived successfully!');
            }
        }
        
        // Duplicate purchase
        function duplicatePurchase() {
            alert('Creating a duplicate of this purchase...');
        }