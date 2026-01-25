/**
 * Location.js - Google Maps Integration
 * Handles map initialization and marker placement
 */

// Restaurant location
const RESTAURANT_LOCATION = { lat: 51.0632, lng: -1.308 };
const RESTAURANT_NAME = 'Buffetier Restaurant';
const RESTAURANT_ADDRESS = '123 Food Street, Winchester';

/**
 * Initialize Google Map
 * Called by Google Maps API callback
 */
function initMap() {
    const mapElement = document.getElementById('map');
    if (!mapElement) {
        console.error('Map element not found');
        return;
    }
    
    // Create map
    const map = new google.maps.Map(mapElement, {
        zoom: 15,
        center: RESTAURANT_LOCATION,
        mapTypeControl: true,
        streetViewControl: true,
        fullscreenControl: true
    });
    
    // Create marker
    const marker = new google.maps.Marker({
        position: RESTAURANT_LOCATION,
        map: map,
        title: RESTAURANT_NAME,
        animation: google.maps.Animation.DROP
    });
    
    // Create info window
    const infoWindow = new google.maps.InfoWindow({
        content: `
            <div style="padding:10px;">
                <strong>${RESTAURANT_NAME}</strong><br>
                ${RESTAURANT_ADDRESS}
            </div>
        `
    });
    
    // Show info window on marker click
    marker.addListener('click', function() {
        infoWindow.open(map, marker);
    });
}

// Make initMap globally accessible for Google Maps callback
window.initMap = initMap;
