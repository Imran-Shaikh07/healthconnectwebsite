document.addEventListener('DOMContentLoaded', function() {
    // Handle profile updates
    const profileForm = document.getElementById('profileForm');
    if (profileForm) {
        profileForm.addEventListener('submit', updateProfile);
    }

    // Search functionality
    const searchInput = document.getElementById('searchBooking');
    if (searchInput) {
        searchInput.addEventListener('input', function(e) {
            const searchTerm = e.target.value.toLowerCase();
            const cards = document.querySelectorAll('.booking-card');
            
            cards.forEach(card => {
                const text = card.textContent.toLowerCase();
                card.style.display = text.includes(searchTerm) ? 'block' : 'none';
            });
        });
    }

    // Book test functionality
    const bookTestForm = document.getElementById('bookTestForm');
    if (bookTestForm) {
        bookTestForm.addEventListener('submit', async function(e) {
            e.preventDefault();
            await bookTest();
        });
    }

    // Mobile-friendly event handlers
    // Handle tab switching with touch events
    const tabButtons = document.querySelectorAll('.tab-btn');
    tabButtons.forEach(button => {
        button.addEventListener('click', function() {
            const tabId = this.getAttribute('data-tab');
            switchTab(tabId);
        });
    });

    // Handle modals
    const modals = document.querySelectorAll('.modal');
    const closeButtons = document.querySelectorAll('.close');
    
    closeButtons.forEach(button => {
        button.addEventListener('click', function() {
            const modal = this.closest('.modal');
            closeModal(modal);
        });
    });

    // Close modal on outside click
    modals.forEach(modal => {
        modal.addEventListener('click', function(e) {
            if (e.target === this) {
                closeModal(this);
            }
        });
    });

    // Handle touch events for cards
    const cards = document.querySelectorAll('.customer-request-card, .assignment-card');
    cards.forEach(card => {
        let touchStart = null;
        
        card.addEventListener('touchstart', function(e) {
            touchStart = e.touches[0].clientY;
        });

        card.addEventListener('touchmove', function(e) {
            if (!touchStart) return;
            
            const touchEnd = e.touches[0].clientY;
            const diff = touchStart - touchEnd;

            // If user has scrolled more than 5px, prevent card interaction
            if (Math.abs(diff) > 5) {
                e.stopPropagation();
            }
        });
    });
});

async function updateProfile(e) {
    e.preventDefault();
    
    const formData = new FormData(e.target);
    const data = Object.fromEntries(formData.entries());
    
    try {
        const response = await fetch('/update-customer-profile', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(data)
        });
        
        if (!response.ok) throw new Error('Failed to update profile');
        
        showNotification('Profile updated successfully', 'success');
    } catch (error) {
        showNotification(error.message, 'error');
    }
}

async function bookTest() {
    const testType = document.getElementById('testType').value;
    const dateTime = document.getElementById('bookingDateTime').value;
    const location = document.getElementById('location').value;

    if (!testType || !dateTime || !location) {
        showNotification('Please fill in all fields', 'error');
        return;
    }

    try {
        const response = await fetch('/book-test', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                test_type: testType,
                date_time: dateTime,
                location: location
            })
        });

        if (!response.ok) throw new Error('Failed to book test');

        showNotification('Booking submitted successfully', 'success');
        setTimeout(() => location.reload(), 1500);
    } catch (error) {
        showNotification('Failed to submit booking', 'error');
    }
}

async function cancelBooking(bookingId) {
    try {
        const response = await fetch(`/cancel-booking/${bookingId}`, {
            method: 'POST'
        });

        if (!response.ok) throw new Error('Failed to cancel booking');

        showNotification('Booking cancelled successfully', 'success');
        setTimeout(() => location.reload(), 1500);
    } catch (error) {
        showNotification('Failed to cancel booking', 'error');
    }
}

function showNotification(message, type = 'info') {
    const toast = document.getElementById('notificationToast');
    toast.textContent = message;
    toast.className = `notification-toast ${type}`;
    toast.style.display = 'block';

    setTimeout(() => {
        toast.style.display = 'none';
    }, 3000);
}

// Helper functions
function switchTab(tabId) {
    // Remove active class from all tabs and contents
    document.querySelectorAll('.tab-btn').forEach(btn => btn.classList.remove('active'));
    document.querySelectorAll('.tab-content').forEach(content => content.classList.remove('active'));
    
    // Add active class to selected tab and content
    document.querySelector(`[data-tab="${tabId}"]`).classList.add('active');
    document.getElementById(tabId).classList.add('active');
}

function openModal(modalId) {
    const modal = document.getElementById(modalId);
    modal.style.display = 'block';
    document.body.style.overflow = 'hidden'; // Prevent background scrolling
}

function closeModal(modal) {
    modal.style.display = 'none';
    document.body.style.overflow = ''; // Restore scrolling
}

// Add smooth scrolling for iOS
function addSmoothScrolling() {
    document.querySelectorAll('.customer-grid, .assignments-grid').forEach(grid => {
        grid.style.webkitOverflowScrolling = 'touch';
    });
}

// Handle orientation change
window.addEventListener('orientationchange', function() {
    // Wait for orientation change to complete
    setTimeout(function() {
        // Refresh any charts or complex layouts
        window.dispatchEvent(new Event('resize'));
    }, 200);
});

// Handle device-specific features
function initializeDeviceSpecifics() {
    // Check if device is iOS
    const isIOS = /iPad|iPhone|iPod/.test(navigator.userAgent) && !window.MSStream;
    
    if (isIOS) {
        addSmoothScrolling();
        // Add iOS-specific classes
        document.body.classList.add('ios-device');
    }
}

// Initialize
initializeDeviceSpecifics(); 