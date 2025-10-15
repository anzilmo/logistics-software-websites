//step 1: get DOM
let nextDom = document.getElementById('next');
let prevDom = document.getElementById('prev');

let carouselDom = document.querySelector('.carousel');
let SliderDom = carouselDom.querySelector('.carousel .list');
let thumbnailBorderDom = document.querySelector('.carousel .thumbnail');
let thumbnailItemsDom = thumbnailBorderDom.querySelectorAll('.item');
let timeDom = document.querySelector('.carousel .time');

thumbnailBorderDom.appendChild(thumbnailItemsDom[0]);
let timeRunning = 3000;
let timeAutoNext = 7000;

nextDom.onclick = function(){
    showSlider('next');    
}

prevDom.onclick = function(){
    showSlider('prev');    
}
let runTimeOut;
let runNextAuto = setTimeout(() => {
    next.click();
}, timeAutoNext)
function showSlider(type){
    let  SliderItemsDom = SliderDom.querySelectorAll('.carousel .list .item');
    let thumbnailItemsDom = document.querySelectorAll('.carousel .thumbnail .item');
    
    if(type === 'next'){
        SliderDom.appendChild(SliderItemsDom[0]);
        thumbnailBorderDom.appendChild(thumbnailItemsDom[0]);
        carouselDom.classList.add('next');
    }else{
        SliderDom.prepend(SliderItemsDom[SliderItemsDom.length - 1]);
        thumbnailBorderDom.prepend(thumbnailItemsDom[thumbnailItemsDom.length - 1]);
        carouselDom.classList.add('prev');
    }
    clearTimeout(runTimeOut);
    runTimeOut = setTimeout(() => {
        carouselDom.classList.remove('next');
        carouselDom.classList.remove('prev');
    }, timeRunning);

    clearTimeout(runNextAuto);
    runNextAuto = setTimeout(() => {
        next.click();
    }, timeAutoNext)
}

// Creat accounts seiontion 
document.addEventListener('DOMContentLoaded', function() {
            const steps = document.querySelectorAll('.info-step');
            
            // Function to check if an element is in the viewport
            function isInViewport(element) {
                const rect = element.getBoundingClientRect();
                return (
                    rect.top >= 0 &&
                    rect.left >= 0 &&
                    rect.bottom <= (window.innerHeight || document.documentElement.clientHeight) &&
                    rect.right <= (window.innerWidth || document.documentElement.clientWidth)
                );
            }
            
            // Function to handle scroll events
            function handleScroll() {
                steps.forEach(step => {
                    if (isInViewport(step)) {
                        step.classList.add('visible');
                    }
                });
            }
            
            // Initial check on page load
            handleScroll();
            
            // Listen for scroll events
            window.addEventListener('scroll', handleScroll);
            
            // Add some extra animation for the connectors
            const connectors = document.querySelectorAll('.info-connector');
            
            function animateConnectors() {
                connectors.forEach((connector, index) => {
                    setTimeout(() => {
                        connector.style.opacity = '1';
                        connector.style.transition = 'opacity 0.8s ease';
                    }, 1000 + index * 300);
                });
            }
            
            // Animate connectors when steps become visible
            const observer = new IntersectionObserver((entries) => {
                entries.forEach(entry => {
                    if (entry.isIntersecting) {
                        animateConnectors();
                    }
                });
            }, { threshold: 0.5 });
            
            observer.observe(document.querySelector('.info-steps'));
        });


// why choice

document.addEventListener('DOMContentLoaded', function() {
            // Animate elements on page load
            setTimeout(function() {
                document.querySelector('.h-why').classList.add('visible');
                document.querySelector('.subtitle').classList.add('visible');
                document.querySelector('.description-why').classList.add('visible');
                document.querySelectorAll('.option').forEach(option => {
                    option.classList.add('visible');
                });
                document.querySelector('.image-content').classList.add('visible');
            }, 300);
            
            // Option click interaction
            document.querySelectorAll('.option').forEach(option => {
                option.addEventListener('click', function() {
                    this.classList.toggle('active');
                    const paragraph = this.querySelector('.p-why');
                    paragraph.style.color = this.classList.contains('active') ? '#3498db' : '#666';
                });
            });
            
            // Learn More button functionality
            document.getElementById('learnMoreBtn').addEventListener('click', function() {
                const statsContainer = document.getElementById('statsContainer');
                statsContainer.classList.add('visible');
                
                // Animate counting stats
                animateCounter('stat1', 0, 120, 2000);
                animateCounter('stat2', 0, 10000, 2000);
                animateCounter('stat3', 0, 50000, 2000);
            });
            
            // Counter animation function
            function animateCounter(elementId, start, end, duration) {
                let obj = document.getElementById(elementId);
                let current = start;
                let range = end - start;
                let increment = end > start ? 1 : -1;
                let stepTime = Math.abs(Math.floor(duration / range));
                let timer = setInterval(function() {
                    current += increment;
                    obj.textContent = current.toLocaleString();
                    if (current == end) {
                        clearInterval(timer);
                    }
                }, stepTime);
            }
            
            // Image hover effect with JS fallback
            const image = document.querySelector('.image-content img');
            image.addEventListener('mouseover', function() {
                this.style.transform = 'scale(1.03)';
            });
            
            image.addEventListener('mouseout', function() {
                this.style.transform = 'scale(1)';
            });
        });



        // signupjs

        const signUpButton = document.getElementById('signUp');
const signInButton = document.getElementById('signIn');
const container = document.getElementById('container');

signUpButton.addEventListener('click', () => {
	container.classList.add("right-panel-active");
});

signInButton.addEventListener('click', () => {
	container.classList.remove("right-panel-active");
});







 document.addEventListener('DOMContentLoaded', function() {
            const uploadBtn = document.getElementById('uploadBtn');
            const uploadModal = document.getElementById('uploadModal');
            const closeModal = document.getElementById('closeModal');
            const fileInput = document.getElementById('fileInput');
            const progressBar = document.getElementById('progressBar');
            const submitBtn = document.getElementById('submitBtn');
            const toast = document.getElementById('toast');
            
            // Add ripple effect to upload button
            uploadBtn.addEventListener('click', function(e) {
                e.preventDefault();
                
                // Create ripple element
                const ripple = document.createElement('span');
                ripple.classList.add('ripple');
                
                // Position the ripple
                const rect = uploadBtn.getBoundingClientRect();
                const size = Math.max(rect.width, rect.height);
                const x = e.clientX - rect.left - size/2;
                const y = e.clientY - rect.top - size/2;
                
                ripple.style.width = ripple.style.height = size + 'px';
                ripple.style.left = x + 'px';
                ripple.style.top = y + 'px';
                
                // Add ripple to button
                this.appendChild(ripple);
                
                // Remove ripple after animation completes
                setTimeout(() => {
                    ripple.remove();
                }, 600);
                
                // Show modal after ripple effect
                setTimeout(() => {
                    uploadModal.style.display = 'flex';
                }, 300);
            });
            
            // Close modal when clicking X
            closeModal.addEventListener('click', function() {
                uploadModal.style.display = 'none';
                resetProgress();
            });
            
            // Close modal when clicking outside
            window.addEventListener('click', function(e) {
                if (e.target === uploadModal) {
                    uploadModal.style.display = 'none';
                    resetProgress();
                }
            });
            
            // Simulate file upload
            submitBtn.addEventListener('click', function() {
                if (!fileInput.value) {
                    alert('Please select a file first!');
                    return;
                }
                
                // Simulate upload progress
                let width = 0;
                const interval = setInterval(() => {
                    if (width >= 100) {
                        clearInterval(interval);
                        showToast();
                        setTimeout(() => {
                            uploadModal.style.display = 'none';
                            resetProgress();
                        }, 2000);
                    } else {
                        width += 5;
                        progressBar.style.width = width + '%';
                    }
                }, 100);
            });
            
            // Drag and drop functionality
            const fileLabel = document.querySelector('.file-label');
            
            fileLabel.addEventListener('dragover', function(e) {
                e.preventDefault();
                this.style.borderColor = '#6a11cb';
                this.style.background = '#f0f0ff';
            });
            
            fileLabel.addEventListener('dragleave', function() {
                this.style.borderColor = '#ccc';
                this.style.background = '#f8f9fa';
            });
            
            fileLabel.addEventListener('drop', function(e) {
                e.preventDefault();
                this.style.borderColor = '#6a11cb';
                this.style.background = '#f0f0ff';
                
                // Handle dropped files
                if (e.dataTransfer.files.length) {
                    fileInput.files = e.dataTransfer.files;
                    
                    // Update label text
                    const fileName = fileInput.files[0].name;
                    this.querySelector('h3').textContent = fileName;
                    this.querySelector('p').textContent = 'Click to change file';
                }
            });
            
            // Show toast notification
            function showToast() {
                toast.classList.add('show');
                setTimeout(() => {
                    toast.classList.remove('show');
                }, 3000);
            }
            
            // Reset progress bar
            function resetProgress() {
                progressBar.style.width = '0%';
                fileInput.value = '';
                
                // Reset label text
                const fileLabel = document.querySelector('.file-label');
                fileLabel.querySelector('h3').textContent = 'Click to browse files';
                fileLabel.querySelector('p').textContent = 'or drag and drop your file here';
            }
        });





        (function () {
  const input = document.getElementById('shipment-search-input');
  const resultsWrap = document.getElementById('shipment-search-results');
  let timeout = null;

  function renderResults(items) {
    if (!items || items.length === 0) {
      resultsWrap.style.display = 'none';
      resultsWrap.innerHTML = '';
      return;
    }
    resultsWrap.innerHTML = items.map(it => {
      const title = it.suit_number || it.tracking_number || 'Shipment #' + it.id;
      const subtitle = it.tracking_number ? `Tracking: ${it.tracking_number}` : '';
      const courier = it.courier ? ` • ${it.courier}` : '';
      const status = it.status ? `<div class="small text-muted">${it.status}${courier}</div>` : '';
      return `<li class="dropdown-item" data-url="${it.url}" style="cursor:pointer; padding:8px 12px; border-bottom:1px solid rgba(0,0,0,0.03);">
                <div><strong>${escapeHtml(title)}</strong></div>
                ${status}
              </li>`;
    }).join('');
    resultsWrap.style.display = 'block';
  }

  function escapeHtml(s) {
    return String(s).replace(/[&<>"']/g, function(m){ return ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'})[m]; });
  }

  async function fetchResults(q) {
    if (!q || q.length < 2) {
      renderResults([]);
      return;
    }
    const url = new URL("{% url 'customer:search_shipments' %}", window.location.origin);
    url.searchParams.set('q', q);
    try {
      const resp = await fetch(url.toString(), { headers: { 'X-Requested-With': 'XMLHttpRequest' }});
      if (!resp.ok) return;
      const data = await resp.json();
      renderResults(data.results || []);
    } catch (err) {
      console.error('Search error', err);
    }
  }

  input.addEventListener('input', function (e) {
    clearTimeout(timeout);
    const q = e.target.value.trim();
    timeout = setTimeout(() => fetchResults(q), 250); // debounce 250ms
  });

  // Click handling: navigate to selected shipment
  resultsWrap.addEventListener('click', function (e) {
    const li = e.target.closest('li[data-url]');
    if (!li) return;
    const url = li.getAttribute('data-url');
    window.location.href = url;
  });

  // Hide when click outside
  document.addEventListener('click', function (e) {
    if (!input.contains(e.target) && !resultsWrap.contains(e.target)) {
      resultsWrap.style.display = 'none';
    }
  });

  // Allow keyboard navigation (Enter to open first)
  input.addEventListener('keydown', function (e) {
    if (e.key === 'Enter') {
      e.preventDefault();
      const first = resultsWrap.querySelector('li[data-url]');
      if (first) window.location.href = first.getAttribute('data-url');
    }
  });
})();