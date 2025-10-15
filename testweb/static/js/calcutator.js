 document.addEventListener('DOMContentLoaded', function() {
            const calculateBtn = document.getElementById('calculateBtn');
            const inputs = document.querySelectorAll('input');
            
            // Add event listeners to inputs for Enter key
            inputs.forEach(input => {
                input.addEventListener('keyup', function(event) {
                    if (event.key === 'Enter') {
                        calculateRates();
                    }
                });
            });
            
            // Calculate button click event
            calculateBtn.addEventListener('click', calculateRates);
            
            function calculateRates() {
                // Get input values
                const length = parseFloat(document.getElementById('length').value);
                const width = parseFloat(document.getElementById('width').value);
                const height = parseFloat(document.getElementById('height').value);
                const grossWeight = parseFloat(document.getElementById('grossWeight').value);
                
                // Validate inputs
                if (!length || !width || !height || !grossWeight) {
                    alert('Please fill in all fields with valid numbers');
                    return;
                }
                
                // Perform calculations
                const cbm = (length * width * height) / 1000000; // Convert to cubic meters
                const volumeWeight = cbm * 200;
                const chargeableWeight = Math.max(grossWeight, volumeWeight);
                
                // Calculate shipping rate (example rate: $5 per kg)
                const rate = chargeableWeight * 5;
                
                // Update UI with results
                document.getElementById('cbmValue').textContent = cbm.toFixed(4) + ' m³';
                document.getElementById('volWeightValue').textContent = volumeWeight.toFixed(2) + ' kg';
                document.getElementById('grossWeightValue').textContent = grossWeight.toFixed(2) + ' kg';
                document.getElementById('chargeableWeightValue').textContent = chargeableWeight.toFixed(2) + ' kg';
                document.getElementById('rateValue').textContent = '$' + rate.toFixed(2);
                
                // Update comparison boxes
                document.getElementById('grossWeightDisplay').textContent = grossWeight.toFixed(2) + ' kg';
                document.getElementById('volWeightDisplay').textContent = volumeWeight.toFixed(2) + ' kg';
                
                // Highlight the larger weight
                document.getElementById('grossWeightBox').classList.remove('active');
                document.getElementById('volWeightBox').classList.remove('active');
                
                if (grossWeight >= volumeWeight) {
                    document.getElementById('grossWeightBox').classList.add('active');
                } else {
                    document.getElementById('volWeightBox').classList.add('active');
                }
            }
            
            // Initialize with example values for demonstration
            document.getElementById('length').value = 100;
            document.getElementById('width').value = 50;
            document.getElementById('height').value = 40;
            document.getElementById('grossWeight').value = 15;
            
            // Calculate initial rates for example
            calculateRates();
        });


        // seconde js
         document.addEventListener('DOMContentLoaded', function() {
            const calculateBtn = document.getElementById('calculateBtn');
            
            calculateBtn.addEventListener('click', function() {
                // Get input values
                const length = parseFloat(document.getElementById('length').value) || 0;
                const width = parseFloat(document.getElementById('width').value) || 0;
                const height = parseFloat(document.getElementById('height').value) || 0;
                const grossWeight = parseFloat(document.getElementById('grossWeight').value) || 0;
                
                // Perform calculations
                const cbm = (length * width * height) / 1000000; // Convert to m³
                const volWeight = cbm * 167; // Standard conversion factor
                const chargeableWeight = Math.max(grossWeight, volWeight);
                
                // Calculate shipping rate (example rate: $5 per kg)
                const ratePerKg = 5;
                const shippingRate = chargeableWeight * ratePerKg;
                
                // Update the UI with results
                document.getElementById('cbmValue').textContent = cbm.toFixed(3) + ' m³';
                document.getElementById('volWeightValue').textContent = volWeight.toFixed(2) + ' kg';
                document.getElementById('grossWeightValue').textContent = grossWeight.toFixed(2) + ' kg';
                document.getElementById('chargeableWeightValue').textContent = chargeableWeight.toFixed(2) + ' kg';
                document.getElementById('rateValue').textContent = '$' + shippingRate.toFixed(2);
                
                // Update comparison boxes
                document.getElementById('grossWeightDisplay').textContent = grossWeight.toFixed(2) + ' kg';
                document.getElementById('volWeightDisplay').textContent = volWeight.toFixed(2) + ' kg';
                
                // Highlight the larger weight
                const grossWeightBox = document.getElementById('grossWeightBox');
                const volWeightBox = document.getElementById('volWeightBox');
                
                grossWeightBox.style.background = grossWeight >= volWeight ? 
                    'linear-gradient(135deg, #4b6cb7 0%, #182848 100%)' : 
                    'linear-gradient(135deg, #5a77b9 0%, #243656 100%)';
                
                volWeightBox.style.background = volWeight >= grossWeight ? 
                    'linear-gradient(135deg, #4b6cb7 0%, #182848 100%)' : 
                    'linear-gradient(135deg, #5a77b9 0%, #243656 100%)';
            });
        });