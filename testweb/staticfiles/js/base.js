// Simple JavaScript to demonstrate mobile menu toggle
        document.querySelector('.menu-toggle').addEventListener('click', function() {
            alert('Menu toggle clicked! In a real implementation, this would open a mobile menu.');
        });
        
        // Language selector functionality
        document.querySelectorAll('.language-dropdown li').forEach(item => {
            item.addEventListener('click', function() {
                const lang = this.getAttribute('data-lang');
                document.querySelector('.selected-language').textContent = this.textContent;
                alert(`Language changed to ${this.textContent} (${lang})`);
            });
        });




         document.addEventListener('DOMContentLoaded', function() {
            const menuToggle = document.getElementById('menuToggle');
            const sidebar = document.getElementById('sidebar');
            
            if (menuToggle && sidebar) {
                menuToggle.addEventListener('click', function() {
                    sidebar.classList.toggle('active');
                });
            }
            
            // Close sidebar when clicking outside on mobile
            document.addEventListener('click', function(event) {
                if (window.innerWidth < 992 && 
                    sidebar.classList.contains('active') && 
                    !sidebar.contains(event.target) && 
                    !menuToggle.contains(event.target)) {
                    sidebar.classList.remove('active');
                }
            });
        });


        // dashboard js

         // Toggle sidebar on mobile
        document.querySelector('.menu-toggle').addEventListener('click', function() {
            document.querySelector('.sidebar').classList.toggle('active');
        });

        // Notification bell functionality
        document.querySelector('.notification-bell').addEventListener('click', function() {
            alert('You have 3 new notifications!\n- Package #1234 has been shipped\n- Package #5678 is out for delivery\n- Your invoice is ready for download');
        });

        // Simulate file upload functionality
        document.querySelector('.upload-button').addEventListener('click', function(e) {
            e.preventDefault();
            alert('Upload functionality would open here. You can upload purchase bills and shipping details.');
        });

        // Add active class to nav items
        const navItems = document.querySelectorAll('.nav-links a');
        navItems.forEach(item => {
            item.addEventListener('click', function() {
                navItems.forEach(i => i.classList.remove('active'));
                this.classList.add('active');
            });
        });



        
document.addEventListener('DOMContentLoaded', function() {
    // Plan selection functionality
    const planRadios = document.querySelectorAll('input[name="plan"]');
    const planLabels = document.querySelectorAll('label.border.rounded.p-3');
    const saveButton = document.querySelector('button[type="submit"]');
    
    // Update button text based on selected plan
    function updateButtonText(planName) {
        if (planName === 'Classic') {
            saveButton.textContent = 'Continue';
            saveButton.className = 'btn btn-continue plan-button mt-3';
        } else if (planName === 'Business') {
            saveButton.textContent = 'Get in touch';
            saveButton.className = 'btn btn-contact plan-button mt-3';
        }
    }
    
    // Handle plan selection
    planRadios.forEach((radio, index) => {
        radio.addEventListener('change', function() {
            // Remove selected class from all labels
            planLabels.forEach(label => {
                label.classList.remove('selected');
                label.style.borderColor = '';
                label.style.background = '';
            });
            
            // Add selected class to current label
            if (this.checked) {
                const label = this.closest('label');
                label.classList.add('selected');
                label.style.borderColor = '#007bff';
                label.style.background = '#f8f9ff';
                
                // Update button text
                const planName = label.querySelector('strong').textContent;
                updateButtonText(planName);
            }
        });
        
        // Initialize selected state
        if (radio.checked) {
            const label = radio.closest('label');
            label.classList.add('selected');
            label.style.borderColor = '#007bff';
            label.style.background = '#f8f9ff';
            
            const planName = label.querySelector('strong').textContent;
            updateButtonText(planName);
        }
    });
    
    // Add visual feedback on label hover
    planLabels.forEach(label => {
        label.addEventListener('mouseenter', function() {
            if (!this.classList.contains('selected')) {
                this.style.borderColor = '#007bff';
                this.style.transform = 'translateY(-2px)';
            }
        });
        
        label.addEventListener('mouseleave', function() {
            if (!this.classList.contains('selected')) {
                this.style.borderColor = '';
                this.style.transform = '';
            }
        });
    });
    
    // Enhance form submission
    const form = document.querySelector('form');
    form.addEventListener('submit', function(e) {
        const selectedPlan = document.querySelector('input[name="plan"]:checked');
        if (!selectedPlan) {
            e.preventDefault();
            alert('Please select a plan');
            return;
        }
        
        const planName = selectedPlan.closest('label').querySelector('strong').textContent;
        if (planName === 'Business') {
            // You might want to handle Business plan differently
            console.log('Business plan selected - redirect to contact form');
        }
    });
});
